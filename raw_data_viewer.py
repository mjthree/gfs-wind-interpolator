#!/usr/bin/env python3
"""
Raw Data Viewer for GFS/HRRR Wind Data
Shows all raw pressure level data without interpolation
"""

import cfgrib
import numpy as np
import pandas as pd
import urllib.request
import os
import sys
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def is_within_conus(lat, lon):
    """Check if location is within CONUS for HRRR coverage."""
    return 20 <= lat <= 60 and -140 <= lon <= -50

def get_available_forecast_hours(model_type):
    """Get available forecast hours for the model."""
    if model_type == 'gfs':
        return list(range(0, 385, 6))  # 0 to 384 hours, every 6 hours
    else:  # hrrr
        return list(range(0, 19))  # 0 to 18 hours

def get_user_input():
    """Get user input for location, elevation, and forecast hour."""
    print("Raw Data Viewer - Location Setup")
    print("=" * 40)
    
    # Get location
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
    
    # Determine model type
    if is_within_conus(lat, lon):
        print(f"\nLocation: {lat:.4f}°N, {lon:.4f}°E")
        print("You are within CONUS. Choose model:")
        print("1. HRRR (High-Resolution Rapid Refresh, up to ~34,000 ft)")
        print("2. GFS (Global Forecast System, up to ~50,000+ ft)")
        while True:
            model_choice = input("Select model (1=HRRR, 2=GFS): ").strip()
            if model_choice == '1':
                model_type = 'hrrr'
                print("Model: HRRR (High-Resolution Rapid Refresh)")
                print("Coverage: Continental US")
                break
            elif model_choice == '2':
                model_type = 'gfs'
                print("Model: GFS (Global Forecast System)")
                print("Coverage: Global")
                break
            else:
                print("Please enter 1 or 2.")
    else:
        model_type = 'gfs'
        print(f"\nLocation: {lat:.4f}°N, {lon:.4f}°E")
        print("Model: GFS (Global Forecast System)")
        print("Coverage: Global")
    
    # Get forecast hour
    available_hours = get_available_forecast_hours(model_type)
    print(f"\nAvailable forecast hours: {available_hours[0]} to {available_hours[-1]}")
    
    while True:
        try:
            forecast_hour = int(input(f"Select forecast hour (0-{available_hours[-1]}): "))
            if forecast_hour in available_hours:
                break
            else:
                print(f"Forecast hour must be one of: {available_hours}")
        except ValueError:
            print("Please enter a valid number.")
    
    return lat, lon, forecast_hour, model_type

def get_forecast_time(forecast_hour, model_type):
    """Get human-readable forecast time."""
    if model_type == 'gfs':
        if forecast_hour == 0:
            return "Current Analysis"
        else:
            return f"{forecast_hour}-hour Forecast"
    else:  # hrrr
        if forecast_hour == 0:
            return "Current Analysis"
        else:
            return f"{forecast_hour}-hour Forecast"

def find_latest_available_run_hour(forecast_hour, model_type):
    """Find the latest available run hour for the given forecast hour and model."""
    now = datetime.utcnow()
    if model_type == 'gfs':
        # GFS runs every 6 hours
        for offset in range(0, 24, 6):
            run_hour = ((now.hour - offset) // 6) * 6
            if run_hour < 0:
                run_hour += 24
            run_time = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            # GFS files are typically available 3-4 hours after run time
            file_date = run_time.strftime('%Y%m%d')
            filename = f"gfs.t{run_hour:02d}z.pgrb2.0p25.f{forecast_hour:03d}"
            if os.path.exists(filename):
                return file_date, run_hour, filename
            # Check remote availability (HEAD request)
            base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
            file_url = f"{base_url}/gfs.{file_date}/{run_hour:02d}/{filename}"
            try:
                from urllib.request import Request, urlopen
                req = Request(file_url, method="HEAD")
                with urlopen(req, timeout=5) as r:
                    if r.status == 200:
                        return file_date, run_hour, filename
            except Exception:
                continue
        # Fallback to current hour if nothing found
        run_hour = (now.hour // 6) * 6
        file_date = now.strftime('%Y%m%d')
        filename = f"gfs.t{run_hour:02d}z.pgrb2.0p25.f{forecast_hour:03d}"
        return file_date, run_hour, filename
    else:
        # HRRR runs every hour
        for offset in range(0, 24):
            run_hour = now.hour - offset
            if run_hour < 0:
                run_hour += 24
            run_time = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            file_date = run_time.strftime('%Y%m%d')
            filename = f"hrrr.t{run_hour:02d}z.wrfsfcf{forecast_hour:02d}.grib2"
            if os.path.exists(filename):
                return file_date, run_hour, filename
            base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod"
            file_url = f"{base_url}/hrrr.{file_date}/conus/{filename}"
            try:
                from urllib.request import Request, urlopen
                req = Request(file_url, method="HEAD")
                with urlopen(req, timeout=5) as r:
                    if r.status == 200:
                        return file_date, run_hour, filename
            except Exception:
                continue
        # Fallback to current hour if nothing found
        run_hour = now.hour
        file_date = now.strftime('%Y%m%d')
        filename = f"hrrr.t{run_hour:02d}z.wrfsfcf{forecast_hour:02d}.grib2"
        return file_date, run_hour, filename

def download_forecast_file(forecast_hour, model_type):
    """Download the latest available forecast file from NOAA."""
    file_date, run_hour, filename = find_latest_available_run_hour(forecast_hour, model_type)
    if model_type == 'gfs':
        base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
        file_url = f"{base_url}/gfs.{file_date}/{run_hour:02d}/{filename}"
    else:
        base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod"
        file_url = f"{base_url}/hrrr.{file_date}/conus/{filename}"
    # Check if file exists locally
    if os.path.exists(filename):
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(filename))
        if file_age.total_seconds() < 3600:
            age_str = f"{int(file_age.total_seconds() / 60)} minutes ago"
        elif file_age.total_seconds() < 86400:
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
            try:
                os.remove(filename)
            except:
                pass
    # Download file
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
    """Load forecast data from GRIB2 file."""
    try:
        # Load all pressure level data
        ds = cfgrib.open_dataset(filename, filter_by_keys={
            "typeOfLevel": "isobaricInhPa"
        })
        return ds
    except Exception as e:
        print(f"Error loading {model_type.upper()} data: {e}")
        if model_type == 'hrrr':
            print("Note: HRRR data is only available for the continental United States.")
        exit(1)

def pressure_to_alt(p_hpa):
    """Convert pressure in hectopascals to altitude in feet using ISA model."""
    return 44330 * (1 - (p_hpa / 1013.25) ** (1 / 5.255)) * 3.28084

def main():
    """Main function to display raw wind data."""
    print("Raw Data Viewer for GFS/HRRR Wind Data")
    print("=" * 50)
    print("This script shows all raw pressure level data without interpolation.")
    print()
    
    # Get user input
    lat, lon, forecast_hour, model_type = get_user_input()
    
    # Download and load data
    filename = download_forecast_file(forecast_hour, model_type)
    print("Loading raw wind data...")
    ds = load_forecast_data(filename, model_type)
    
    # Find nearest grid point
    print(f"Grid dimensions: lat={len(ds.latitude)}, lon={len(ds.longitude)}")
    
    # Handle longitude conversion for HRRR
    lon_adjusted = lon
    if model_type == 'hrrr' and lon < 0:
        lon_adjusted = lon + 360
        print(f"Converting longitude from {lon} to {lon_adjusted} for HRRR format")
    
    # Find nearest grid point
    if len(ds.latitude.values.shape) == 2:
        # 2D arrays (irregular grid like HRRR)
        lat_diff = np.abs(ds.latitude.values - lat)
        lon_diff = np.abs(ds.longitude.values - lon_adjusted)
        total_diff = lat_diff + lon_diff
        lat_idx, lon_idx = np.unravel_index(total_diff.argmin(), total_diff.shape)
        actual_lat = float(ds.latitude.values[lat_idx, lon_idx])
        actual_lon = float(ds.longitude.values[lat_idx, lon_idx])
    else:
        # 1D arrays (regular grid like GFS)
        lat_idx = np.abs(ds.latitude.values - lat).argmin()
        lon_idx = np.abs(ds.longitude.values - lon_adjusted).argmin()
        actual_lat = float(ds.latitude.values[lat_idx])
        actual_lon = float(ds.longitude.values[lon_idx])
    
    print(f"Target location: {lat:.4f}°N, {lon:.4f}°E")
    print(f"Nearest grid point: {actual_lat:.4f}°N, {actual_lon:.4f}°E")
    print(f"Grid indices: lat_idx={lat_idx}, lon_idx={lon_idx}")
    
    # Extract all available variables at all pressure levels
    pressure_levels = ds.isobaricInhPa.values
    print(f"\nTotal pressure levels: {len(pressure_levels)}")
    print(f"Available variables: {list(ds.data_vars.keys())}")
    
    # Create comprehensive data table
    data_rows = []
    
    for i, p in enumerate(pressure_levels):
        row = {
            'Pressure_hPa': p,
            'Altitude_ft': pressure_to_alt(p)
        }
        
        # Extract all variables at this pressure level
        for var_name in ds.data_vars.keys():
            try:
                if len(ds.latitude.values.shape) == 2:
                    # 2D arrays
                    value = float(ds[var_name].values[i, lat_idx, lon_idx])
                else:
                    # 1D arrays
                    value = float(ds[var_name].values[i, lat_idx, lon_idx])
                row[var_name] = value
            except:
                row[var_name] = np.nan
        
        # Calculate wind speed and direction if U and V are available
        if 'u' in row and 'v' in row and not np.isnan(row['u']) and not np.isnan(row['v']):
            u, v = row['u'], row['v']
            row['Wind_Speed_mps'] = np.sqrt(u**2 + v**2)
            row['Wind_Speed_kts'] = row['Wind_Speed_mps'] * 1.944
            row['Wind_Direction_deg'] = (270 - np.rad2deg(np.arctan2(v, u))) % 360
        else:
            row['Wind_Speed_mps'] = np.nan
            row['Wind_Speed_kts'] = np.nan
            row['Wind_Direction_deg'] = np.nan
        
        data_rows.append(row)
    
    # Create DataFrame and display
    df = pd.DataFrame(data_rows)
    
    # Display results
    forecast_time = get_forecast_time(forecast_hour, model_type)
    print(f"\n{model_type.upper()} Raw Data for {lat:.4f}°N, {lon:.4f}°E")
    print(f"Forecast: {forecast_time}")
    print("=" * 80)
    
    # Show all data
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    print(df.to_string(index=False, float_format='%.2f'))
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    if 'Wind_Speed_kts' in df.columns:
        valid_winds = df[df['Wind_Speed_kts'].notna()]
        if len(valid_winds) > 0:
            print(f"Wind Speed Range: {valid_winds['Wind_Speed_kts'].min():.1f} - {valid_winds['Wind_Speed_kts'].max():.1f} kts")
            print(f"Average Wind Speed: {valid_winds['Wind_Speed_kts'].mean():.1f} kts")
            print(f"Altitude Range: {df['Altitude_ft'].min():.0f} - {df['Altitude_ft'].max():.0f} ft")
    
    print(f"Total Pressure Levels: {len(pressure_levels)}")
    print(f"Variables Available: {len(ds.data_vars)}")
    
    # Ask if user wants to save data
    while True:
        save_choice = input("\nSave raw data to file? (y/n): ").lower().strip()
        if save_choice in ['y', 'n']:
            break
        else:
            print("Please enter 'y' or 'n'.")
    
    if save_choice == 'y':
        default_filename = f"raw_data_{lat:.2f}_{lon:.2f}_{model_type}_{forecast_hour}h.csv"
        filename = input(f"Enter filename (or press Enter for {default_filename}): ").strip()
        if not filename:
            filename = default_filename
        
        df.to_csv(filename, index=False)
        print(f"Raw data saved to: {filename}")

if __name__ == "__main__":
    main() 
