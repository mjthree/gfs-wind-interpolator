import os
from datetime import datetime, timedelta
import urllib.request
import cfgrib
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# Tucson location
lat = 32.22
lon = -110.94

# Step 1: Download the latest available GFS 0-hour GRIB2 file
def download_latest_gfs_file():
    now = datetime.utcnow()
    run_hour = now.hour - (now.hour % 6)
    run_hour_str = f"{run_hour:02d}"
    date_str = now.strftime("%Y%m%d")
    base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{run_hour_str}/atmos/"
    filename = f"gfs.t{run_hour_str}z.pgrb2.0p25.f000"
    file_url = base_url + filename

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

# Step 2: Load the file with cfgrib
filename = download_latest_gfs_file()
ds = cfgrib.open_dataset(filename, filter_by_keys={"typeOfLevel": "isobaricInhPa"})

# Step 3: Find the nearest grid point to Tucson
lat_idx = np.abs(ds.latitude - lat).argmin()
lon_idx = np.abs(ds.longitude - lon).argmin()

levs = ds.isobaricInhPa.values
u = ds.u.values[:, lat_idx, lon_idx]
v = ds.v.values[:, lat_idx, lon_idx]

# Step 4: Calculate wind speed/direction
spd = np.sqrt(u**2 + v**2)
dir = (270 - np.rad2deg(np.arctan2(v, u))) % 360

# Step 5: Convert pressure levels to feet altitude (ISA model)
def pressure_to_alt(p_hpa):
    return 44330 * (1 - (p_hpa / 1013.25) ** (1 / 5.255)) * 3.28084

alt_ft = pressure_to_alt(levs)

# Step 6: Interpolate to every 1,000 ft
interp_alt = np.arange(0, 40000, 1000)
speed_i = interp1d(alt_ft, spd, bounds_error=False, fill_value="extrapolate")
dir_i = interp1d(alt_ft, dir, bounds_error=False, fill_value="extrapolate")

df = pd.DataFrame({
    "Altitude_ft": interp_alt,
    "Wind_Speed_kts": speed_i(interp_alt),
    "Wind_Direction_deg": dir_i(interp_alt)
})

# Step 7: Output
print(df.to_string(index=False))
