"""
GFS Wind Profiler - NOAA Global Forecast System Wind Data Extractor

This script downloads the latest GFS forecast data from NOAA, extracts wind information
for a specific location, and interpolates wind speed and direction to various altitudes.
Outputs a table showing wind conditions every 1,000 feet from 0 to user-specified maximum.

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

def get_user_input():
    """
    Prompts user for location coordinates and maximum elevation.
    
    Returns:
        tuple: (latitude, longitude, max_elevation_ft)
    """
    print("GFS Wind Profiler - Location Setup")
    print("=" * 40)
    
    # Get latitude with validation
    while True:
        try:
            lat = float(input("Enter latitude (decimal degrees, -90 to 90): "))
            if -90 <= lat <= 90:
                break
            else:
                print("Latitude must be between -90 and 90 degrees.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Get longitude with validation
    while True:
        try:
            lon = float(input("Enter longitude (decimal degrees, -180 to 180): "))
            if -180 <= lon <= 180:
                break
            else:
                print("Longitude must be between -180 and 180 degrees.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Get maximum elevation with validation
    while True:
        try:
            max_elevation = int(input("Enter maximum elevation in feet (1000 to 50000): "))
            if 1000 <= max_elevation <= 50000:
                break
            else:
                print("Maximum elevation must be between 1000 and 50000 feet.")
        except ValueError:
            print("Please enter a valid number.")
    
    print(f"\nLocation: {lat:.4f}°N, {lon:.4f}°E")
    print(f"Maximum elevation: {max_elevation:,} feet")
    print("=" * 40)
    
    return lat, lon, max_elevation

def download_latest_gfs_file():
    """
    Downloads the latest available GFS 0-hour forecast file from NOAA servers.
    
    GFS runs are issued every 6 hours (00Z, 06Z, 12Z, 18Z). This function:
    1. Determines the most recent run time
    2. Constructs the NOAA URL for the GRIB2 file
    3. Downloads the file if not already cached locally
    
    Returns:
        str: Filename of the downloaded/cached GRIB2 file
    """
    # Get current UTC time and find the most recent 6-hour run
    now = datetime.now(timezone.utc)  # Use timezone-aware datetime compatible with older Python
    run_hour = now.hour - (now.hour % 6)  # Round down to nearest 6-hour interval
    run_hour_str = f"{run_hour:02d}"  # Format as 2-digit string (e.g., "06")
    date_str = now.strftime("%Y%m%d")  # Format date as YYYYMMDD
    
    # Construct NOAA GFS data URL
    base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{run_hour_str}/atmos/"
    filename = f"gfs.t{run_hour_str}z.pgrb2.0p25.f000"  # 0-hour forecast, 0.25-degree resolution
    file_url = base_url + filename

    # Download file if it doesn't exist locally (caching for efficiency)
    if not os.path.exists(filename):
        print(f"Downloading {filename} from NOAA...")
        try:
            urllib.request.urlretrieve(file_url, filename)
            print("Download complete.\n")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
            exit(1)
    else:
        print(f"Using cached file: {filename}\n")

    return filename

def load_gfs_data(filename):
    """
    Loads GFS data from GRIB2 file with error handling and warning suppression.
    
    Args:
        filename (str): Path to the GRIB2 file
        
    Returns:
        xarray.Dataset: Loaded dataset with wind data
    """
    # Redirect stderr to suppress cfgrib warnings
    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    
    try:
        # Load only wind components (u and v) to avoid conflicts
        ds = cfgrib.open_dataset(filename, filter_by_keys={
            "typeOfLevel": "isobaricInhPa",
            "shortName": ["u", "v"]
        })
        return ds
    except Exception as e:
        print(f"Error loading GFS data: {e}")
        exit(1)
    finally:
        # Restore stderr
        sys.stderr.close()
        sys.stderr = original_stderr

# Get user input for location and elevation
lat, lon, max_elevation_ft = get_user_input()

# Step 1: Download the latest GFS forecast file
filename = download_latest_gfs_file()

# Step 2: Load and parse the GRIB2 file using cfgrib
print("Processing wind data...")
ds = load_gfs_data(filename)

# Step 3: Find the nearest grid point to our target location
# GFS data is on a regular lat/lon grid, so we find the closest point
lat_idx = np.abs(ds.latitude - lat).argmin()  # Index of closest latitude
lon_idx = np.abs(ds.longitude - lon).argmin()  # Index of closest longitude

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
print(f"\nGFS Wind Profile for {lat:.4f}°N, {lon:.4f}°E")
print("=" * 60)
print(df.to_string(index=False))
