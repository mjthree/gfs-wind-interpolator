#!/usr/bin/env python3
"""
NOAA Wind Profiler - HRRR/GFS Wind Data Extractor

This script automatically selects between HRRR (High-Resolution Rapid Refresh) for the continental US
and GFS (Global Forecast System) for worldwide coverage. Downloads the latest forecast data from NOAA,
extracts wind information for a specific location, and interpolates wind speed and direction to various altitudes.
Outputs a table showing wind conditions every 1,000 feet from 0 to a user-specified maximum.
Operates fully offline after the first download—no external APIs used.

Author: Michael Julio
Purpose: Aviation, skydiving, UAV planning, tactical operations
"""

import os
import warnings
import sys
from datetime import datetime, timedelta, timezone
import urllib.request
import cfgrib
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import re
import time
import struct
from dted import TileSet, LatLon

# DTED imports
def read_dted0_file(filepath):
    """
    Reads a DTED Level 0 (.dt0) file and returns elevation data.
    
    Args:
        filepath (str): Path to the .dt0 file
        
    Returns:
        tuple: (latitudes, longitudes, elevations) or None if error
    """
    try:
        with open(filepath, 'rb') as f:
            # Read DTED header (UHL - User Header Label)
            uhl = f.read(80)
            if not uhl.startswith(b'UHL1'):
                return None
            
            # Read DSI (Data Set Identification)
            dsi = f.read(648)
            
            # Read ACC (Accuracy Description)
            acc = f.read(2700)
            
            # Read data records
            elevations = []
            latitudes = []
            longitudes = []
            
            # DTED0 has 121 latitude points and 121 longitude points
            for lat_idx in range(121):
                # Read record header
                record_header = f.read(8)
                if len(record_header) < 8:
                    break
                    
                # Read 121 elevation values (2 bytes each, signed)
                lat_elevations = []
                for lon_idx in range(121):
                    elevation_bytes = f.read(2)
                    if len(elevation_bytes) < 2:
                        break
                    elevation = struct.unpack('>h', elevation_bytes)[0]  # Big-endian signed short
                    lat_elevations.append(elevation)
                
                if len(lat_elevations) == 121:
                    elevations.append(lat_elevations)
                    
            if not elevations:
                return None
                
            # Convert to numpy arrays
            elevations = np.array(elevations)
            
            # Extract lat/lon info from header
            # This is a simplified approach - in practice you'd parse the header more carefully
            return elevations
            
    except Exception as e:
        print(f"Error reading DTED file {filepath}: {e}")
        return None

def get_dted0_filename(lat, lon):
    """
    Determines the DTED0 filename for given coordinates.
    
    Args:
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees
        
    Returns:
        str: Path to the DTED0 file, or None if not found
    """
    # DTED0 covers 1-degree tiles
    # Longitude: e000-e097 (0° to 97°E), w000-w097 (0° to 97°W)
    # Latitude: n00-n90 (0° to 90°N), s00-s90 (0° to 90°S)
    
    # Calculate tile coordinates
    lon_tile = int(abs(lon))
    lat_tile = int(abs(lat))
    
    # Determine longitude prefix
    # For 0° longitude and slightly negative (like London at -0.1278°), use e000
    if lon >= 0 or (lon < 0 and lon_tile == 0):
        lon_prefix = f"e{lon_tile:03d}"
    else:
        lon_prefix = f"w{lon_tile:03d}"
    
    # Determine latitude prefix
    if lat >= 0:
        lat_prefix = f"n{lat_tile:02d}"
    else:
        lat_prefix = f"s{lat_tile:02d}"
    
    # Construct filename
    filename = f"{lat_prefix}.dt0"
    filepath = os.path.join("DTED0", lon_prefix, filename)
    
    return filepath if os.path.exists(filepath) else None

def get_ground_elevation_dted0(lat, lon):
    """
    Gets ground elevation in feet MSL using local DTED0 data, using [lat_idx, lon_idx] axis order and bilinear interpolation.
    """
    filepath = get_dted0_filename(lat, lon)
    if not filepath:
        print(f"DTED0 file not found for {lat}, {lon}")
        return None
    elevations = read_dted0_file(filepath)
    if elevations is None:
        print(f"Could not read DTED0 file: {filepath}")
        return None
    # Ensure array is at least 2D
    if elevations.ndim != 2:
        print(f"DTED0 data is not 2D: shape={elevations.shape}")
        return None
    n_lat, n_lon = elevations.shape  # [latitude, longitude] (swapped)
    # Find SW corner of tile
    lat0 = int(lat)
    lon0 = int(lon)
    # Compute fractional index within tile
    lat_frac = lat - lat0
    lon_frac = lon - lon0
    lat_idx = lat_frac * (n_lat - 1)
    lon_idx = lon_frac * (n_lon - 1)
    # Integer indices
    i = int(lat_idx)
    j = int(lon_idx)
    # Clamp indices
    i = min(max(i, 0), n_lat - 2)
    j = min(max(j, 0), n_lon - 2)
    di = lat_idx - i
    dj = lon_idx - j
    # Bilinear interpolation, axis order [lat, lon]
    z00 = elevations[i, j]
    z10 = elevations[i+1, j]
    z01 = elevations[i, j+1]
    z11 = elevations[i+1, j+1]
    elevation_m = (
        z00 * (1 - di) * (1 - dj) +
        z10 * di * (1 - dj) +
        z01 * (1 - di) * dj +
        z11 * di * dj
    )
    elevation_ft = elevation_m * 3.28084
    print(f"DTED0 (axis [lat,lon]) bilinear: {elevation_m:.2f}m = {elevation_ft:.2f}ft")
    return elevation_ft

# Set DTED availability based on local data
DTED_AVAILABLE = False

# Suppress all warnings and debug output
warnings.filterwarnings('ignore')
os.environ['CFGRIB_DEBUG'] = '0'

class NoGFSDataError(Exception):
    """Exception raised when no GFS forecast data is available."""
    pass

def is_within_conus(lat, lon):
    """
    Determines if a location is within the Continental United States (CONUS) coverage area for HRRR.
    HRRR does NOT cover Hawaii, Alaska, or US territories. GFS is used for those locations.
    Args:
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees
    Returns:
        bool: True if within CONUS, False otherwise
    """
    # CONUS coverage: roughly 20°N to 60°N, 140°W to 50°W
    return 20 <= lat <= 60 and -140 <= lon <= -50

def get_ground_elevation(lat, lon):
    """
    Always prompt the user for manual ground elevation input (in feet MSL).
    """
    return get_manual_ground_elevation()

def get_manual_ground_elevation():
    """
    Prompts user for manual ground elevation input.
    
    Returns:
        float: Ground elevation in feet MSL
    """
    while True:
        try:
            ground_elevation_ft = float(input("Enter ground elevation in feet MSL: "))
            if -1000 <= ground_elevation_ft <= 30000:  # Reasonable range
                return ground_elevation_ft
            else:
                print("Ground elevation must be between -1000 and 30000 feet.")
        except ValueError:
            print("Please enter a valid number.")

def get_available_forecast_hours(model_type):
    """
    Returns a list of available forecast hours for the specified model.
    Args:
        model_type (str): 'hrrr', 'rap', 'nam', or 'gfs'
    Returns:
        list: Available forecast hours
    """
    if model_type == 'hrrr':
        return list(range(0, 19))  # 0-18 hours, hourly
    elif model_type == 'rap':
        return list(range(0, 22))  # 0-21 hours, hourly
    elif model_type == 'gfs':
        hours_3h = list(range(0, 121, 3))
        hours_6h = list(range(126, 385, 6))
        return hours_3h + hours_6h
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def check_forecast_availability(forecast_hour, model_type):
    """
    Checks if a specific forecast hour is available from NOAA.
    
    Args:
        forecast_hour (int): Forecast hour to check
        model_type (str): 'hrrr', 'rap', 'nam', or 'gfs'
        
    Returns:
        bool: True if available, False otherwise
    """
    now = datetime.now(timezone.utc)
    
    if model_type == 'hrrr':
        # For HRRR, we need to check multiple recent run hours since data becomes available gradually
        # Try the most recent 3 run hours to see what's available
        for hours_back in range(3):
            check_time = now - timedelta(hours=hours_back)
            run_hour = check_time.hour
            run_hour_str = f"{run_hour:02d}"
            date_str = check_time.strftime("%Y%m%d")
            base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/conus/"
            filename = f"hrrr.t{run_hour_str}z.wrfsfcf{forecast_hour:02d}.grib2"
            file_url = base_url + filename
            
            try:
                request = urllib.request.Request(file_url, method="HEAD")
                with urllib.request.urlopen(request, timeout=5) as response:
                    if 200 <= response.status < 400:
                        return True
            except Exception:
                continue
        return False
    elif model_type == 'rap':
        # RAP runs hourly, similar to HRRR
        for hours_back in range(3):
            check_time = now - timedelta(hours=hours_back)
            run_hour = check_time.hour
            run_hour_str = f"{run_hour:02d}"
            date_str = check_time.strftime("%Y%m%d")
            base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.{date_str}/"
            filename = f"rap.t{run_hour_str}z.awp130pgrbf{forecast_hour:02d}.grib2"
            file_url = base_url + filename
            try:
                request = urllib.request.Request(file_url, method="HEAD")
                with urllib.request.urlopen(request, timeout=5) as response:
                    if 200 <= response.status < 400:
                        return True
            except Exception:
                continue
        return False
    elif model_type == 'gfs':
        # For GFS, check multiple recent run hours since data becomes available gradually
        # GFS runs every 6 hours (00Z, 06Z, 12Z, 18Z)
        for hours_back in range(0, 24, 6):  # Check last 24 hours of runs
            check_time = now - timedelta(hours=hours_back)
            run_hour = check_time.hour - (check_time.hour % 6)  # Round to nearest 6-hour run
            run_hour_str = f"{run_hour:02d}"
            date_str = check_time.strftime("%Y%m%d")
            base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{run_hour_str}/atmos/"
            filename = f"gfs.t{run_hour_str}z.pgrb2.0p25.f{forecast_hour:03d}"
            file_url = base_url + filename

            try:
                request = urllib.request.Request(file_url, method="HEAD")
                with urllib.request.urlopen(request, timeout=10) as response:
                    if 200 <= response.status < 400:
                        return True
            except Exception:
                continue
        return False
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def get_immediately_available_hours(model_type):
    """
    Returns a list of forecast hours that are immediately available from NOAA.
    Args:
        model_type (str): 'hrrr', 'rap', 'nam', or 'gfs'
    Returns:
        list: Available forecast hours that can be downloaded now
    """
    print(f"Checking available forecast hours from NOAA {model_type.upper()}...")
    all_hours = get_available_forecast_hours(model_type)
    available_hours = []
    for hour in all_hours:
        if check_forecast_availability(hour, model_type):
            available_hours.append(hour)
    if 0 not in available_hours:
        available_hours.insert(0, 0)
    return available_hours

def find_available_run_hour(forecast_hour, model_type):
    """
    Finds the most recent run hour that has the requested forecast hour available.
    
    Args:
        forecast_hour (int): Forecast hour needed
        model_type (str): 'hrrr', 'rap', 'nam', or 'gfs'
        
    Returns:
        tuple: (run_hour, date_str) for the available run
    """
    now = datetime.now(timezone.utc)
    
    if model_type == 'hrrr':
        # Check recent run hours for HRRR
        for hours_back in range(6):  # Check last 6 hours of runs
            check_time = now - timedelta(hours=hours_back)
            run_hour = check_time.hour
            run_hour_str = f"{run_hour:02d}"
            date_str = check_time.strftime("%Y%m%d")
            base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/conus/"
            filename = f"hrrr.t{run_hour_str}z.wrfsfcf{forecast_hour:02d}.grib2"
            file_url = base_url + filename
            
            try:
                response = urllib.request.urlopen(file_url, timeout=5)
                response.close()
                return run_hour, date_str
            except:
                continue
        # If no specific forecast hour found, return the most recent run hour
        return now.hour, now.strftime("%Y%m%d")
    elif model_type == 'rap':
        for hours_back in range(6):
            check_time = now - timedelta(hours=hours_back)
            run_hour = check_time.hour
            run_hour_str = f"{run_hour:02d}"
            date_str = check_time.strftime("%Y%m%d")
            base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.{date_str}/"
            filename = f"rap.t{run_hour_str}z.awp130pgrbf{forecast_hour:02d}.grib2"
            file_url = base_url + filename
            try:
                response = urllib.request.urlopen(file_url, timeout=5)
                response.close()
                return run_hour, date_str
            except:
                continue
        return now.hour, now.strftime("%Y%m%d")
    elif model_type == 'gfs':
        # Check multiple recent run hours for GFS
        for hours_back in range(0, 48, 6):  # Check last 48 hours of runs
            check_time = now - timedelta(hours=hours_back)
            run_hour = check_time.hour - (check_time.hour % 6)  # Round to nearest 6-hour run
            run_hour_str = f"{run_hour:02d}"
            date_str = check_time.strftime("%Y%m%d")
            base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{run_hour_str}/atmos/"
            filename = f"gfs.t{run_hour_str}z.pgrb2.0p25.f{forecast_hour:03d}"
            file_url = base_url + filename
            
            try:
                response = urllib.request.urlopen(file_url, timeout=10)
                response.close()
                return run_hour, date_str
            except:
                continue
        # If no specific forecast hour found, return the most recent run hour
        run_hour = now.hour - (now.hour % 6)
        return run_hour, now.strftime("%Y%m%d")
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def get_user_input():
    """
    Prompts user for location coordinates, maximum elevation, and forecast hour.
    Automatically determines whether to use HRRR, RAP, NAM, or GFS based on location.
    
    Returns:
        tuple: (latitude, longitude, max_elevation_ft, forecast_hour, model_type)
    """
    print("NOAA Wind Profiler - Location Setup")
    print("=" * 40)

    while True:
        try:
            lat = float(input("Enter latitude (decimal degrees, -90 to 90): "))
            if -90 <= lat <= 90:
                break
            else:
                print("Latitude must be between -90 and 90 degrees.")
        except ValueError:
            print("Please enter a valid number.")

    while True:
        try:
            lon = float(input("Enter longitude (decimal degrees, -180 to 180): "))
            if -180 <= lon <= 180:
                break
            else:
                print("Longitude must be between -180 and 180 degrees.")
        except ValueError:
            print("Please enter a valid number.")

    # Prompt for maximum elevation before model selection so it is always defined
    while True:
        try:
            max_elevation_ft = int(input("Enter maximum elevation in feet (1000 to 50000): "))
            if 1000 <= max_elevation_ft <= 50000:
                break
            else:
                print("Maximum elevation must be between 1000 and 50000 feet.")
        except ValueError:
            print("Please enter a valid number.")

    # Ask for altitude reference preference
    print("\nAltitude Reference:")
    print("1. MSL (Mean Sea Level) - Height above sea level")
    print("2. AGL (Above Ground Level) - Height above local terrain")
    while True:
        altitude_choice = input("Select altitude reference (1=MSL, 2=AGL): ").strip()
        if altitude_choice == '1':
            altitude_reference = 'MSL'
            ground_elevation_ft = 0  # Not needed for MSL
            print("Using MSL (Mean Sea Level) altitudes")
            break
        elif altitude_choice == '2':
            altitude_reference = 'AGL'
            print("Using AGL (Above Ground Level) altitudes")
            # Try to get ground elevation automatically from DTED
            if DTED_AVAILABLE:
                ground_elevation_ft = get_ground_elevation_dted0(lat, lon)
                if ground_elevation_ft is not None:
                    print(f"Ground elevation from DTED: {ground_elevation_ft:.0f} feet MSL")
                else:
                    print("Could not get ground elevation from DTED. Manual input required.")
                    ground_elevation_ft = get_manual_ground_elevation()
            else:
                print("DTED not available for automatic ground elevation lookup.")
                print("Note: Install pydted from https://github.com/OpenTopography/pydted for automatic lookup.")
                ground_elevation_ft = get_manual_ground_elevation()
            break
        else:
            print("Please enter 1 for MSL or 2 for AGL.")

    # Determine which model to use based on location
    if is_within_conus(lat, lon):
        print(f"\nLocation is within CONUS. Choose model:")
        print("1. HRRR (High-Resolution Rapid Refresh, up to ~34,000 ft)")
        print("2. RAP (Rapid Refresh, up to ~39,000 ft)")
        print("3. GFS (Global Forecast System, up to ~50,000+ ft)")
        print("4. Auto (Most Current Available)")
        while True:
            model_choice = input("Select model (1=HRRR, 2=RAP, 3=GFS, 4=Auto): ").strip()
            if model_choice == '1':
                model_type = 'hrrr'
                print("Model: HRRR (High-Resolution Rapid Refresh)")
                print("Coverage: Continental US")
                break
            elif model_choice == '2':
                model_type = 'rap'
                print("Model: RAP (Rapid Refresh)")
                print("Coverage: Continental US and nearby regions")
                break
            elif model_choice == '3':
                model_type = 'gfs'
                print("Model: GFS (Global Forecast System)")
                print("Coverage: Global")
                break
            elif model_choice == '4':
                # Auto mode: check all models for freshest data using only HEAD requests
                print("Auto mode: Checking all models for most current available forecast...")
                from datetime import datetime, timedelta, timezone
                import urllib.request
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                freshest_model = None
                freshest_time = None
                freshest_info = None
                for m in ['hrrr', 'rap', 'gfs']:
                    available_hours = get_immediately_available_hours(m)
                    if not available_hours:
                        continue
                    run_hour, date_str = find_available_run_hour(0, m)  # Use 0 as a placeholder
                    run_hour_str = f"{run_hour:02d}"
                    if m == 'hrrr':
                        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/conus/"
                        filename_template = "hrrr.t{run_hour_str}z.wrfsfcf{forecast_hour:02d}.grib2"
                    elif m == 'rap':
                        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.{date_str}/"
                        filename_template = "rap.t{run_hour_str}z.awp130pgrbf{forecast_hour:02d}.grib2"
                    elif m == 'gfs':
                        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{run_hour_str}/atmos/"
                        filename_template = "gfs.t{run_hour_str}z.pgrb2.0p25.f{forecast_hour:03d}"
                    else:
                        continue
                    # Find the forecast hour whose valid time is closest to now but not after
                    best_fh = None
                    best_valid_time = None
                    for fh in available_hours:
                        valid_time = datetime.strptime(date_str, '%Y%m%d').replace(tzinfo=timezone.utc) + timedelta(hours=run_hour + fh)
                        if valid_time <= now and (best_valid_time is None or valid_time > best_valid_time):
                            best_fh = fh
                            best_valid_time = valid_time
                    if best_fh is None:
                        continue
                    filename = filename_template.format(run_hour_str=run_hour_str, forecast_hour=best_fh)
                    file_url = base_url + filename
                    # HEAD request only
                    try:
                        request = urllib.request.Request(file_url, method="HEAD")
                        with urllib.request.urlopen(request, timeout=5) as response:
                            if 200 <= response.status < 400:
                                if freshest_time is None or best_valid_time > freshest_time:
                                    freshest_time = best_valid_time
                                    freshest_model = m
                                    freshest_info = (best_fh, run_hour, date_str, filename, base_url)
                    except Exception:
                        continue
                if freshest_model is None:
                    print("No available forecast found for any model. Try again later.")
                    exit(1)
                model_type = freshest_model
                forecast_hour, run_hour, date_str, filename, base_url = freshest_info
                print(f"Auto-selected model: {model_type.upper()} (valid for {freshest_time.strftime('%Y-%m-%d %H:%MZ')})")
                # Download only the selected file
                file_url = base_url + filename
                print(f"Downloading {filename} from NOAA...")
                import sys
                import time
                def reporthook(block_num, block_size, total_size):
                    downloaded = block_num * block_size
                    percent = min(downloaded / total_size * 100, 100) if total_size else 0
                    sys.stdout.write(f"\rDownloaded: {downloaded/1024/1024:.2f} MB / {total_size/1024/1024:.2f} MB ({percent:.1f}%)")
                    sys.stdout.flush()
                start_time = time.time()
                urllib.request.urlretrieve(file_url, filename, reporthook=reporthook)
                end_time = time.time()
                print()
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    elapsed = end_time - start_time
                    speed = file_size / 1024 / 1024 / elapsed if elapsed > 0 else 0
                    print(f"Download complete. File size: {file_size/1024/1024:.2f} MB. Time: {elapsed:.1f}s. Speed: {speed:.2f} MB/s.")
                # Return all info needed for main()
                return lat, lon, max_elevation_ft, forecast_hour, model_type, filename, run_hour, date_str, altitude_reference, ground_elevation_ft
            else:
                print("Please enter 1, 2, 3, or 4.")
    else:
        model_type = 'gfs'
        print(f"\nLocation is outside CONUS (including Hawaii, Alaska, and overseas) - using GFS (Global Forecast System)")
        print("GFS provides global coverage with 25km resolution (0-384 hours)")

    available_hours = get_immediately_available_hours(model_type)
    print(f"\nImmediately available forecast hours: {', '.join(map(str, available_hours))}")
    
    if model_type == 'hrrr':
        print("Note: More forecast hours may become available as HRRR data is processed.")
        print("0 = Current conditions, 1 = 1 hour from now, 3 = 3 hours from now, etc.")
    elif model_type == 'rap':
        print("Note: More forecast hours may become available as RAP data is processed.")
        print("0 = Current conditions, 1 = 1 hour from now, 21 = 21 hours from now, etc.")
    else:
        print("Note: More forecast hours may become available as GFS data is processed.")
        print("0 = Current conditions, 3 = 3 hours from now, 24 = 24 hours from now, etc.")

    while True:
        try:
            forecast_hour = int(input("Enter forecast hour: "))
            if forecast_hour == 0 and model_type == 'gfs':
                # For GFS, 0 means search backwards for the most recent available file
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                found = False
                for hours_back in range(0, 25, 6):  # Go back up to 24 hours in 6-hour steps
                    check_time = now - timedelta(hours=hours_back)
                    run_hour = check_time.hour - (check_time.hour % 6)
                    run_hour_str = f"{run_hour:02d}"
                    date_str = check_time.strftime("%Y%m%d")
                    for fh in range(0, 85, 3):  # GFS forecast hours: 0, 3, ..., 84
                        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/"
                        filename = f"gfs.t{run_hour_str}z.pgrb2.0p25.f{fh:03d}"
                        file_url = base_url + filename
                        try:
                            request = urllib.request.Request(file_url, method="HEAD")
                            with urllib.request.urlopen(request, timeout=5) as response:
                                if 200 <= response.status < 400:
                                    forecast_hour = fh
                                    print(f"Using GFS run {date_str} {run_hour_str}Z, forecast hour {forecast_hour}")
                                    found = True
                                    break
                        except Exception:
                            continue
                    if found:
                        break
                if not found:
                    print("No GFS forecast files are currently available (checked last 24 hours).")
                    print("Please try another model or run the script again later.")
                    print("Exiting...")
                    raise NoGFSDataError
                break
            elif forecast_hour in available_hours:
                break
            else:
                print(f"Forecast hour {forecast_hour} is not available yet.")
                print(f"Available hours: {', '.join(map(str, available_hours))}")
                print("Try a shorter forecast time or wait for more data to be processed.")
        except ValueError:
            print("Please enter a valid number.")
        except EOFError:
            print("\nInput interrupted. Exiting...")
            raise NoGFSDataError

    forecast_time = get_forecast_time(forecast_hour, model_type)

    print(f"\nLocation: {lat:.4f}°N, {lon:.4f}°E")
    print(f"Model: {model_type.upper()}")
    print(f"Maximum elevation: {max_elevation_ft:,} feet")
    print(f"Forecast hour: {forecast_hour} ({forecast_time})")
    print("=" * 40)

    return lat, lon, max_elevation_ft, forecast_hour, model_type, altitude_reference, ground_elevation_ft

def get_forecast_time(forecast_hour, model_type):
    """
    Converts forecast hour to human-readable time.
    
    Args:
        forecast_hour (int): Forecast hour
        model_type (str): 'hrrr', 'rap', 'nam', or 'gfs'
        
    Returns:
        str: Human-readable forecast time
    """
    if forecast_hour == 0:
        return "Current conditions (0-hour analysis)"
    elif forecast_hour == 1:
        return "1 hour from now"
    else:
        return f"{forecast_hour} hours from now"

def download_forecast_file(forecast_hour, model_type):
    """
    Downloads a specific forecast file from NOAA servers.
    
    Args:
        forecast_hour (int): Forecast hour
        model_type (str): 'hrrr', 'rap', 'nam', or 'gfs'
        
    Returns:
        tuple: (filename, run_hour, date_str)
    """
    run_hour, date_str = find_available_run_hour(forecast_hour, model_type)
    run_hour_str = f"{run_hour:02d}"
    
    if model_type == 'hrrr':
        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/conus/"
        filename = f"hrrr.t{run_hour_str}z.wrfsfcf{forecast_hour:02d}.grib2"
    elif model_type == 'rap':
        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.{date_str}/"
        filename = f"rap.t{run_hour_str}z.awp130pgrbf{forecast_hour:02d}.grib2"
    elif model_type == 'gfs':
        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{run_hour_str}/atmos/"
        filename = f"gfs.t{run_hour_str}z.pgrb2.0p25.f{forecast_hour:03d}"
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    file_url = base_url + filename

    # Final HEAD check before download
    try:
        request = urllib.request.Request(file_url, method="HEAD")
        with urllib.request.urlopen(request, timeout=5) as response:
            if not (200 <= response.status < 400):
                print(f"Forecast file {filename} is not available (HTTP {response.status}). Please select another forecast hour.")
                return None, None, None
            total_size = int(response.headers.get('Content-Length', 0))
    except Exception as e:
        print(f"Forecast file {filename} is not available ({e}). Please select another forecast hour.")
        return None, None, None

    # Check if file exists and ask user preference
    if os.path.exists(filename):
        while True:
            choice = input("Use cached file or download fresh? (c/d): ").lower().strip()
            if choice == 'c':
                print(f"Using cached file: {filename}\n")
                return filename, run_hour, date_str
            elif choice == 'd':
                print(f"Downloading fresh file: {filename}")
                try:
                    os.remove(filename)
                except:
                    pass
                break
            else:
                print("Please enter 'c' for cached file or 'd' for fresh download.")
    # Download file with progress
    print(f"Downloading {filename} from NOAA...")
    try:
        def reporthook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded / total_size * 100, 100) if total_size else 0
            sys.stdout.write(f"\rDownloaded: {downloaded/1024/1024:.2f} MB / {total_size/1024/1024:.2f} MB ({percent:.1f}%)")
            sys.stdout.flush()
        start_time = time.time()
        urllib.request.urlretrieve(file_url, filename, reporthook=reporthook)
        end_time = time.time()
        print()
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            elapsed = end_time - start_time
            speed = file_size / 1024 / 1024 / elapsed if elapsed > 0 else 0
            print(f"Download complete. File size: {file_size/1024/1024:.2f} MB. Time: {elapsed:.1f}s. Speed: {speed:.2f} MB/s.")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
        print("This forecast hour may not be available yet. Try a shorter forecast time.")
        return None, None, None
    return filename, run_hour, date_str

def load_forecast_data(filename, model_type):
    """
    Loads forecast data from GRIB2 file with error handling and warning suppression.
    
    Args:
        filename (str): Path to the GRIB2 file
        model_type (str): 'hrrr', 'rap', 'nam', or 'gfs'
        
    Returns:
        xarray.Dataset: Loaded dataset with wind data
    """
    # Redirect stderr to suppress cfgrib warnings
    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    
    try:
        if model_type in ['hrrr', 'gfs', 'rap']:
            ds = cfgrib.open_dataset(filename, filter_by_keys={
                "typeOfLevel": "isobaricInhPa",
                "shortName": ["u", "v"]
            })
            return ds
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    except Exception as e:
        print(f"Error loading {model_type.upper()} data: {e}")
        if model_type == 'hrrr':
            print("Note: HRRR data is only available for the continental United States.")
        exit(1)
    finally:
        # Restore stderr
        sys.stderr.close()
        sys.stderr = original_stderr

def main():
    """Entry point for command-line execution."""
    try:
        # Get user input for location, elevation, and forecast hour
        user_input = get_user_input()
        # If auto mode, get all info directly
        if len(user_input) == 10:
            lat, lon, max_elevation_ft, forecast_hour, model_type, filename, run_hour, run_date_str, altitude_reference, ground_elevation_ft = user_input
        else:
            lat, lon, max_elevation_ft, forecast_hour, model_type, altitude_reference, ground_elevation_ft = user_input
            filename, run_hour, run_date_str = download_forecast_file(forecast_hour, model_type)
            if filename is None:
                print("No forecast file available. Exiting.")
                return
    except NoGFSDataError:
        print("Exiting due to unavailable GFS data.")
        return

    # Step 2: Load and parse the GRIB2 file using cfgrib
    print("Processing wind data...")
    ds = load_forecast_data(filename, model_type)

    # Step 3: Find the nearest grid point to our target location
    # Forecast data may use irregular grids, so we need to handle 2D coordinate arrays
    print(f"Grid dimensions: lat={len(ds.latitude)}, lon={len(ds.longitude)}")
    print(f"Latitude array shape: {ds.latitude.values.shape}")
    print(f"Longitude array shape: {ds.longitude.values.shape}")

    # Handle longitude conversion properly
    lon_adjusted = lon
    if model_type == 'hrrr':
        # HRRR uses longitude from 0 to 360, convert from -180 to 180 format
        if lon < 0:
            lon_adjusted = lon + 360
        print(f"Converting longitude from {lon} to {lon_adjusted} for HRRR format")

    # Check if we have 2D coordinate arrays (irregular grid)
    if len(ds.latitude.values.shape) == 2 and len(ds.longitude.values.shape) == 2:
        print("Detected 2D coordinate arrays (irregular grid)")
        # For 2D arrays, find the nearest point across the entire grid
        lat_diff = np.abs(ds.latitude.values - lat)
        lon_diff = np.abs(ds.longitude.values - lon_adjusted)
        total_diff = lat_diff + lon_diff  # Simple distance metric
        lat_idx, lon_idx = np.unravel_index(total_diff.argmin(), total_diff.shape)
    else:
        # For 1D arrays (regular grid)
        print("Detected 1D coordinate arrays (regular grid)")
        lat_idx = np.abs(ds.latitude.values - lat).argmin()
        lon_idx = np.abs(ds.longitude.values - lon_adjusted).argmin()

    # Validate indices are within bounds
    if len(ds.latitude.values.shape) == 2:
        # 2D arrays (irregular grid like HRRR)
        if lat_idx >= ds.latitude.values.shape[0] or lon_idx >= ds.longitude.values.shape[1]:
            print(f"Error: Calculated grid indices ({lat_idx}, {lon_idx}) are out of bounds.")
            print(f"Grid size: lat={ds.latitude.values.shape[0]}, lon={ds.longitude.values.shape[1]}")
            print(f"Target location: lat={lat}, lon={lon}")
            print(f"Adjusted longitude: {lon_adjusted}")
            exit(1)
    else:
        # 1D arrays (regular grid like GFS)
        if lat_idx >= ds.latitude.values.shape[0] or lon_idx >= ds.longitude.values.shape[0]:
            print(f"Error: Calculated grid indices ({lat_idx}, {lon_idx}) are out of bounds.")
            print(f"Grid size: lat={ds.latitude.values.shape[0]}, lon={ds.longitude.values.shape[0]}")
            print(f"Target location: lat={lat}, lon={lon}")
            print(f"Adjusted longitude: {lon_adjusted}")
            exit(1)

    # Get the actual grid coordinates for verification
    if len(ds.latitude.values.shape) == 2:
        # 2D arrays (irregular grid)
        actual_lat = float(ds.latitude.values[lat_idx, lon_idx])
        actual_lon = float(ds.longitude.values[lat_idx, lon_idx])
    else:
        # 1D arrays (regular grid)
        actual_lat = float(ds.latitude.values[lat_idx])
        actual_lon = float(ds.longitude.values[lon_idx])

    print(f"Target location: {lat:.4f}°N, {lon:.4f}°E")
    print(f"Nearest grid point: {actual_lat:.4f}°N, {actual_lon:.4f}°E")
    print(f"Grid indices: lat_idx={lat_idx}, lon_idx={lon_idx}")

    # Print valid time in Zulu (UTC)
    valid_time = None
    if run_date_str is not None and run_hour is not None:
        run_date = datetime.strptime(run_date_str, '%Y%m%d')
        valid_time = run_date.replace(tzinfo=timezone.utc) + timedelta(hours=run_hour + forecast_hour)
        print(f"\nForecast valid for: {valid_time.strftime('%Y-%m-%d %H:%MZ')} (Zulu/UTC)")
    valid_time_str = valid_time.strftime('%Y-%m-%d %H:%MZ') if valid_time else 'Unknown'

    # Extract wind components at all pressure levels for our location
    levs = ds.isobaricInhPa.values  # Pressure levels in hPa
    u = ds.u.values[:, lat_idx, lon_idx]  # U-component (eastward wind) in m/s
    v = ds.v.values[:, lat_idx, lon_idx]  # V-component (northward wind) in m/s

    # Step 4: Calculate wind speed and direction from U and V components
    # Wind speed = sqrt(u² + v²)
    spd = np.sqrt(u**2 + v**2)
    # Wind direction = 270° - arctan2(v,u), then normalize to 0-360°
    # Meteorological convention: 0° = North, 90° = East, 180° = South, 270° = West
    dir = (270 - np.rad2deg(np.arctan2(v, u))) % 360

    # Step 5: Convert pressure levels to altitude using International Standard Atmosphere (ISA)
    def pressure_to_alt(p_hpa):
        """Converts pressure in hectopascals to altitude in feet using ISA model."""

        # ISA formula: h = 44330 * (1 - (p/1013.25)^(1/5.255)) * 3.28084
        # Where 1013.25 hPa is standard sea-level pressure
        return 44330 * (1 - (p_hpa / 1013.25) ** (1 / 5.255)) * 3.28084

    # Convert each pressure level to corresponding altitude
    alt_ft = pressure_to_alt(levs)

    # Step 6: Interpolate wind data to regular altitude intervals
    # Create altitude array from 0 to user-specified maximum in 1,000-foot increments
    if altitude_reference == 'MSL':
        # For MSL, use the altitudes as-is (they're already MSL from ISA model)
        interp_alt = np.arange(0, max_elevation_ft + 1000, 1000)
        altitude_label = "Altitude_ft_MSL"
    else:  # AGL
        # For AGL, we need to convert MSL altitudes to AGL by subtracting ground elevation
        # Start from ground level (0 AGL) up to max_elevation_ft AGL
        interp_alt = np.arange(0, max_elevation_ft + 1000, 1000)
        altitude_label = "Altitude_ft_AGL"

    # Create interpolation functions for wind speed and direction
    # bounds_error=False allows extrapolation beyond data range
    # fill_value="extrapolate" uses linear extrapolation for out-of-bounds values
    speed_i = interp1d(alt_ft, spd, bounds_error=False, fill_value="extrapolate")
    dir_i = interp1d(alt_ft, dir, bounds_error=False, fill_value="extrapolate")

    # Apply interpolation to get wind values at each 1,000-foot level
    if altitude_reference == 'MSL':
        # For MSL, interpolate directly to the altitude levels
        wind_speeds = speed_i(interp_alt)
        wind_directions = dir_i(interp_alt)
    else:  # AGL
        # For AGL, we need to interpolate to MSL altitudes first, then convert to AGL
        # Convert AGL altitudes to MSL for interpolation
        msl_altitudes = interp_alt + ground_elevation_ft
        wind_speeds = speed_i(msl_altitudes)
        wind_directions = dir_i(msl_altitudes)

    df = pd.DataFrame(
        {
            altitude_label: interp_alt,
            "Wind_Speed_kts": wind_speeds,
            "Wind_Direction_deg": wind_directions,
        }
    )

    # Step 7: Display results in a formatted table
    forecast_time = get_forecast_time(forecast_hour, model_type)
    print(f"\n{model_type.upper()} Wind Profile for {lat:.4f}°N, {lon:.4f}°E")
    print(f"Forecast: {forecast_time}")
    if altitude_reference == 'AGL':
        print(f"Altitude Reference: AGL (Above Ground Level)")
        print(f"Ground Elevation: {ground_elevation_ft:.0f} feet MSL")
    else:
        print(f"Altitude Reference: MSL (Mean Sea Level)")
    print("=" * 60)
    print(df.to_string(index=False))

    # Ask if user wants to save results
    while True:
        save_choice = input("\nSave results to file? (y/n): ").lower().strip()
        if save_choice in ['y', 'n']:
            break
        else:
            print("Please enter 'y' or 'n'.")
    if save_choice == 'y':
        default_base = f"wind_profile_{lat:.2f}_{lon:.2f}_{model_type}_{forecast_hour}h"
        # Always use default filenames
        csv_filename = f"{default_base}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"Results saved to: {csv_filename}")
        txt_filename = f"{default_base}.txt"
        with open(txt_filename, 'w') as f:
            f.write(f"{model_type.upper()} Wind Profile for {lat:.4f}°N, {lon:.4f}°E\n")
            f.write(f"Forecast: {forecast_time}\n")
            f.write(f"Valid Zulu Time: {valid_time_str}\n")
            if altitude_reference == 'AGL':
                f.write(f"Altitude Reference: AGL (Above Ground Level)\n")
                f.write(f"Ground Elevation: {ground_elevation_ft:.0f} feet MSL\n")
            else:
                f.write(f"Altitude Reference: MSL (Mean Sea Level)\n")
            f.write("=" * 60 + "\n")
            f.write(df.to_string(index=False) + "\n")
        print(f"Human-readable results saved to: {txt_filename}")
        # Add valid Zulu time and altitude reference as columns in CSV
        df['Valid_Zulu_Time'] = valid_time_str
        df['Altitude_Reference'] = altitude_reference
        if altitude_reference == 'AGL':
            df['Ground_Elevation_MSL_ft'] = ground_elevation_ft
        df.to_csv(csv_filename, index=False)
        print(f"CSV results saved to: {csv_filename}")

    # NOTE: This script operates fully offline after the forecast file is downloaded.
    #       No external polling (e.g., from open websites) is required at runtime.
    #       This may offer improved operational security in field or tactical settings.


if __name__ == "__main__":
    main()

