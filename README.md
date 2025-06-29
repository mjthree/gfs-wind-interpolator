# GFS Wind Profiler

A Python tool to automatically download, extract, and interpolate high-resolution wind data from the NOAA GFS model. Outputs wind speed and direction every 1,000 feet above a specified location (default: Tucson, AZ). Runs entirely on-device using open-source libraries and official .grib2 forecast data.

---

## ✨ Features

- Downloads the latest GFS 0-hour forecast from NOAA
- Extracts wind data from GRIB2 format using `cfgrib`
- Interpolates wind speed and direction to every 1,000 feet
- Displays results in a tabular format
- Fully offline after initial download
- Ideal for aviation, skydiving, UAV planning, or tactical operations

---

## 📦 Requirements

- Python 3.8+
- Recommended: macOS or Linux (Windows WSL also works)

### Python dependencies:

```bash
pip install cfgrib xarray pandas numpy scipy
brew install eccodes  # macOS only
