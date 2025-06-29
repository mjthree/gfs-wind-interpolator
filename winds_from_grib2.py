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

# Suppress all warnings and debug output
warnings.filterwarnings('ignore')
os.environ['CFGRIB_DEBUG'] = '0'

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

def get_available_forecast_hours(model_type):
    """
    Returns a list of available forecast hours for the specified model.
    
    Args:
        model_type (str): 'hrrr' or 'gfs'
        
    Returns:
        list: Available forecast hours
    """
    if model_type == 'hrrr':
        # HRRR provides forecasts out to 18 hours with 1-hour resolution
        return list(range(0, 19))
    elif model_type == 'gfs':
        # GFS provides forecasts out to 384 hours (16 days) with different intervals
        # Hours 0-120: every 3 hours
        hours_3h = list(range(0, 121, 3))
        # Hours 126-384: every 6 hours  
        hours_6h = list(range(126, 385, 6))
        return hours_3h + hours_6h
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def check_forecast_availability(forecast_hour, model_type):
    """
    Checks if a specific forecast hour is available from NOAA.
    
    Args:
        forecast_hour (int): Forecast hour to check
        model_type (str): 'hrrr' or 'gfs'
        
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
                response = urllib.request.urlopen(file_url, timeout=5)
                response.close()
                return True
            except:
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
                response = urllib.request.urlopen(file_url, timeout=10)
                response.close()
                return True
            except:
                continue
        return False
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def get_immediately_available_hours(model_type):
    """
    Returns a list of forecast hours that are immediately available from NOAA.
    
    Args:
        model_type (str): 'hrrr' or 'gfs'
        
    Returns:
        list: Available forecast hours that can be downloaded now
    """
    print(f"Checking available forecast hours from NOAA {model_type.upper()}...")
    all_hours = get_available_forecast_hours(model_type)
    available_hours = []

    if model_type == 'hrrr':
        # For HRRR, check all hours but be more lenient with availability
        for hour in all_hours:
            if check_forecast_availability(hour, model_type):
                available_hours.append(hour)
            else:
                # For HRRR, if we can't find a specific hour, stop checking
                # as HRRR data becomes available sequentially
                break
    else:  # GFS
        # For GFS, be more lenient and check more hours since data availability varies
        for hour in all_hours[:20]:  # Check first 20 hours
            if check_forecast_availability(hour, model_type):
                available_hours.append(hour)
            else:
                # For GFS, continue checking as some hours might be available from different runs
                continue

    if 0 not in available_hours:
        available_hours.insert(0, 0)

    return available_hours

def find_available_run_hour(forecast_hour, model_type):
    """
    Finds the most recent run hour that has the requested forecast hour available.
    
    Args:
        forecast_hour (int): Forecast hour needed
        model_type (str): 'hrrr' or 'gfs'
        
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
    else:  # GFS
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

def get_user_input():
    """
    Prompts user for location coordinates, maximum elevation, and forecast hour.
    Automatically determines whether to use HRRR or GFS based on location.
    
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

    # Determine which model to use based on location
    if is_within_conus(lat, lon):
        model_type = 'hrrr'
        print(f"\nLocation is within CONUS - using HRRR (High-Resolution Rapid Refresh)")
        print("HRRR provides 3km resolution data with hourly updates (0-18 hours) for the continental US only.")
    else:
        model_type = 'gfs'
        print(f"\nLocation is outside CONUS (including Hawaii, Alaska, and overseas) - using GFS (Global Forecast System)")
        print("GFS provides global coverage with 25km resolution (0-384 hours)")

    while True:
        try:
            max_elevation = int(input("Enter maximum elevation in feet (1000 to 50000): "))
            if 1000 <= max_elevation <= 50000:
                break
            else:
                print("Maximum elevation must be between 1000 and 50000 feet.")
        except ValueError:
            print("Please enter a valid number.")

    available_hours = get_immediately_available_hours(model_type)
    print(f"\nImmediately available forecast hours: {', '.join(map(str, available_hours))}")
    
    if model_type == 'hrrr':
        print("Note: More forecast hours may become available as HRRR data is processed.")
        print("0 = Current conditions, 1 = 1 hour from now, 3 = 3 hours from now, etc.")
    else:
        print("Note: More forecast hours may become available as GFS data is processed.")
        print("0 = Current conditions, 3 = 3 hours from now, 24 = 24 hours from now, etc.")

    while True:
        try:
            forecast_hour = int(input("Enter forecast hour: "))
            if forecast_hour in available_hours:
                break
            else:
                print(f"Forecast hour {forecast_hour} is not available yet.")
                print(f"Available hours: {', '.join(map(str, available_hours))}")
                print("Try a shorter forecast time or wait for more data to be processed.")
        except ValueError:
            print("Please enter a valid number.")

    forecast_time = get_forecast_time(forecast_hour, model_type)

    print(f"\nLocation: {lat:.4f}°N, {lon:.4f}°E")
    print(f"Model: {model_type.upper()}")
    print(f"Maximum elevation: {max_elevation:,} feet")
    print(f"Forecast hour: {forecast_hour} ({forecast_time})")
    print("=" * 40)

    return lat, lon, max_elevation, forecast_hour, model_type

def get_forecast_time(forecast_hour, model_type):
    """
    Converts forecast hour to human-readable time.
    
    Args:
        forecast_hour (int): Forecast hour
        model_type (str): 'hrrr' or 'gfs'
        
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
        model_type (str): 'hrrr' or 'gfs'
        
    Returns:
        str: Filename of the downloaded/cached GRIB2 file
    """
    # Find the appropriate run hour for this forecast
    run_hour, date_str = find_available_run_hour(forecast_hour, model_type)
    run_hour_str = f"{run_hour:02d}"
    
    if model_type == 'hrrr':
        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/conus/"
        filename = f"hrrr.t{run_hour_str}z.wrfsfcf{forecast_hour:02d}.grib2"
    else:  # GFS
        base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{run_hour_str}/atmos/"
        filename = f"gfs.t{run_hour_str}z.pgrb2.0p25.f{forecast_hour:03d}"
    
    file_url = base_url + filename

    # Check if file exists and ask user preference
    if os.path.exists(filename):
        # Get file modification time
        now = datetime.now(timezone.utc)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(filename), tz=timezone.utc)
        file_age = now - file_mtime
        
        # Format age for display
        if file_age.total_seconds() < 3600:  # Less than 1 hour
            age_str = f"{int(file_age.total_seconds() / 60)} minutes ago"
        elif file_age.total_seconds() < 86400:  # Less than 1 day
            age_str = f"{int(file_age.total_seconds() / 3600)} hours ago"
        else:
            age_str = f"{int(file_age.total_seconds() / 86400)} days ago"
        
        print(f"Found cached file: {filename}")
        print(f"File age: {age_str}")
        print(f"File size: {os.path.getsize(filename) / (1024*1024):.1f} MB")
        
        while True:
            choice = input("Use cached file or download fresh? (c/d): ").lower().strip()
            if choice in ['c', 'd']:
                break
            else:
                print("Please enter 'c' for cached file or 'd' for fresh download.")
        
        if choice == 'c':
            print(f"Using cached file: {filename}\n")
            return filename
        else:
            print(f"Downloading fresh file: {filename}")
            # Remove old file before downloading
            try:
                os.remove(filename)
            except:
                pass

    # Download file if it doesn't exist or user chose fresh download
    print(f"Downloading {filename} from NOAA...")
    try:
        urllib.request.urlretrieve(file_url, filename)
        print("Download complete.\n")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
        print("This forecast hour may not be available yet. Try a shorter forecast time.")
        exit(1)

    return filename

def load_forecast_data(filename, model_type):
    """
    Loads forecast data from GRIB2 file with error handling and warning suppression.
    
    Args:
        filename (str): Path to the GRIB2 file
        model_type (str): 'hrrr' or 'gfs'
        
    Returns:
        xarray.Dataset: Loaded dataset with wind data
    """
    # Redirect stderr to suppress cfgrib warnings
    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    
    try:
        # Load wind components from forecast data
        ds = cfgrib.open_dataset(filename, filter_by_keys={
            "typeOfLevel": "isobaricInhPa",
            "shortName": ["u", "v"]
        })
        return ds
    except Exception as e:
        print(f"Error loading {model_type.upper()} data: {e}")
        if model_type == 'hrrr':
            print("Note: HRRR data is only available for the continental United States.")
        exit(1)
    finally:
        # Restore stderr
        sys.stderr.close()
        sys.stderr = original_stderr

# Get user input for location, elevation, and forecast hour
lat, lon, max_elevation_ft, forecast_hour, model_type = get_user_input()

# Step 1: Download the specified forecast file
filename = download_forecast_file(forecast_hour, model_type)

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
    """
    Converts pressure in hectopascals to altitude in feet using ISA model.
    
    Args:
        p_hpa (float or array): Pressure in hectopascals (hPa)
    
    Returns:
        float or array: Altitude in feet
    """
    # ISA formula: h = 44330 * (1 - (p/1013.25)^(1/5.255)) * 3.28084
    # Where 1013.25 hPa is standard sea-level pressure
    return 44330 * (1 - (p_hpa / 1013.25) ** (1 / 5.255)) * 3.28084

# Convert each pressure level to corresponding altitude
alt_ft = pressure_to_alt(levs)

# Step 6: Interpolate wind data to regular altitude intervals
# Create altitude array from 0 to user-specified maximum in 1,000-foot increments
interp_alt = np.arange(0, max_elevation_ft + 1000, 1000)

# Create interpolation functions for wind speed and direction
# bounds_error=False allows extrapolation beyond data range
# fill_value="extrapolate" uses linear extrapolation for out-of-bounds values
speed_i = interp1d(alt_ft, spd, bounds_error=False, fill_value="extrapolate")
dir_i = interp1d(alt_ft, dir, bounds_error=False, fill_value="extrapolate")

# Apply interpolation to get wind values at each 1,000-foot level
df = pd.DataFrame({
    "Altitude_ft": interp_alt,
    "Wind_Speed_kts": speed_i(interp_alt),  # Convert m/s to knots (1 m/s ≈ 1.944 kts)
    "Wind_Direction_deg": dir_i(interp_alt)
})

# Step 7: Display results in a formatted table
forecast_time = get_forecast_time(forecast_hour, model_type)
print(f"\n{model_type.upper()} Wind Profile for {lat:.4f}°N, {lon:.4f}°E")
print(f"Forecast: {forecast_time}")
print("=" * 60)
print(df.to_string(index=False))

# NOTE: This script operates fully offline after the forecast file is downloaded.
#       No external polling (e.g., from open websites) is required at runtime.
#       This may offer improved operational security in field or tactical settings.

