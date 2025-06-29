# GFS Wind Profiler

A Python tool to automatically download, extract, and interpolate high-resolution wind data from the NOAA GFS model. Outputs wind speed and direction every 1,000 feet above a user-specified location. Runs entirely on-device using open-source libraries and official .grib2 forecast data.

---

## ✨ Features

- **Interactive Location Selection**: Enter any latitude/longitude coordinates worldwide
- **Customizable Altitude Range**: Specify maximum elevation from 1,000 to 50,000 feet
- **Latest Forecast Data**: Downloads the most recent GFS 0-hour forecast from NOAA
- **High-Resolution Interpolation**: Wind data interpolated to every 1,000 feet
- **Clean Output**: Tabular format with wind speed (knots) and direction (degrees)
- **Offline Capable**: Caches downloaded data for repeated use
- **No API Keys Required**: Uses publicly available NOAA data
- **Cross-Platform**: Works on macOS, Linux, and Windows (WSL)

---

## 🔒 Why Source Directly from NOAA?

For operations requiring atmospheric wind data, it may be advantageous to source forecasts directly from official U.S. government models such as HRRR or GFS provided by NOAA, rather than relying on third-party public websites like the Mark Schulze wind profiler. While both methods involve retrieving data over the internet, using government-hosted sources may offer greater reliability and reduce exposure to unvetted external platforms. Additionally, once the data is downloaded, it can be processed locally without further internet access, enabling offline use in communications-restricted environments. This approach may enhance operational resilience and data integrity in tactical or field applications.

---

## 📦 Requirements

- **Python 3.8+** (tested on Python 3.8-3.13)
- **Recommended**: macOS or Linux (Windows WSL also works)

### System Requirements

- **Memory**: Minimum 2GB RAM (4GB+ recommended for large files)
- **Storage**: ~50MB per forecast file (cached locally)
- **Network**: Internet connection for initial data download
- **Processing**: Single-core processing is sufficient

### Performance Considerations

- **First Run**: May take 1-2 minutes to download initial data
- **Subsequent Runs**: Typically 10-30 seconds with cached files
- **File Size**: GFS files ~50MB, HRRR files ~200MB
- **Cache Management**: Old files are automatically detected and can be refreshed

### Python Dependencies

```bash
pip install cfgrib xarray pandas numpy scipy
```

### System Dependencies

**macOS:**
```bash
brew install eccodes
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libeccodes-dev
```

**CentOS/RHEL:**
```bash
sudo yum install eccodes-devel
```

---

## 🐍 Environment Setup

### Recommended: Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python projects:

**Using venv (Python 3.3+):**
```bash
# Create virtual environment
python -m venv gfs_env

# Activate virtual environment
# On macOS/Linux:
source gfs_env/bin/activate
# On Windows:
gfs_env\Scripts\activate

# Install dependencies
pip install cfgrib xarray pandas numpy scipy
```

**Using conda:**
```bash
# Create conda environment
conda create -n gfs_env python=3.11

# Activate environment
conda activate gfs_env

# Install dependencies
conda install -c conda-forge cfgrib xarray pandas numpy scipy
```

### Environment Verification

After setting up your environment, verify the installation:

```bash
# Check Python version
python --version

# Check installed packages
pip list | grep -E "(cfgrib|xarray|pandas|numpy|scipy)"

# Test import
python -c "import cfgrib, xarray, pandas, numpy, scipy; print('All packages imported successfully!')"
```

---

## 🚀 Installation

1. **Clone or download** this repository
2. **Set up Python environment** (see Environment Setup above)
3. **Install Python dependencies:**
   ```bash
   pip install cfgrib xarray pandas numpy scipy
   ```
4. **Install system dependencies** (see above for your OS)
5. **Run the script:**
   ```bash
   python wind_profiler.py
   ```

---

## 📖 Usage

### Basic Usage

```bash
python wind_profiler.py
```

The script will prompt you for:
- **Latitude** (decimal degrees, -90 to 90)
- **Longitude** (decimal degrees, -180 to 180)  
- **Maximum elevation** (feet, 1000 to 50000)

### Example Session

```
GFS Wind Profiler - Location Setup
========================================
Enter latitude (decimal degrees, -90 to 90): 32.22
Enter longitude (decimal degrees, -180 to 180): -110.94
Enter maximum elevation in feet (1000 to 50000): 20000

Location: 32.2200°N, -110.9400°E
Maximum elevation: 20,000 feet
========================================
Using cached file: gfs.t00z.pgrb2.0p25.f000
Processing wind data...

GFS Wind Profile for 32.2200°N, -110.9400°E
============================================================
 Altitude_ft  Wind_Speed_kts  Wind_Direction_deg
           0        0.110228          282.702341
        1000        0.106185          288.963790
        2000        0.107529          286.372465
        ...
       20000       13.234940          265.378142
```

### Forecast Hours Selection

The script allows you to select forecast hours for more detailed analysis:

- **GFS Model**: 0 to 384 hours (16 days)
- **HRRR Model**: 0 to 18 hours

```
Select forecast hour (0-384 for GFS, 0-18 for HRRR): 6
```

- **0-hour**: Current analysis (most accurate for current conditions)
- **6-hour**: 6-hour forecast
- **12-hour**: 12-hour forecast
- And so on...

### File Caching

The script automatically caches downloaded files and asks whether to use cached or fresh data:

```
Found cached file: gfs.t18z.pgrb2.0p25.f006 (2.3 MB, 3 hours old)
Use cached file? (y/n): y
```

- **Cached files**: Faster execution, no re-download needed
- **Fresh files**: Ensures latest data, but requires download time
- **File age**: Shows when the cached file was downloaded
- **File size**: Helps verify data integrity

### Data Export

Results can be saved to a file for further analysis:

```
Save results to file? (y/n): y
Enter filename (or press Enter for default): berlin_winds.txt
```

Default filename format: `{location}_{model}_{forecast_hour}h.txt`

### Output Format

- **Altitude_ft**: Height above ground level in feet
- **Wind_Speed_kts**: Wind speed in knots (1 knot ≈ 1.15 mph)
- **Wind_Direction_deg**: Wind direction in degrees (meteorological convention)
  - 0° = North, 90° = East, 180° = South, 270° = West

---

## 🔧 How It Works

1. **Data Source**: Downloads latest GFS 0-hour forecast from NOAA NOMADS
2. **File Format**: Processes .grib2 files using cfgrib library
3. **Wind Components**: Extracts U (eastward) and V (northward) wind components
4. **Calculations**: Converts to wind speed and direction using meteorological formulas
5. **Altitude Conversion**: Maps pressure levels to altitude using International Standard Atmosphere (ISA)
6. **Interpolation**: Smoothly interpolates wind data to 1,000-foot intervals
7. **Output**: Displays results in a clean, tabular format

---

## 📊 Data Accuracy & Limitations

### Interpolation Quality

- **Linear Interpolation**: Uses linear interpolation between pressure levels, which is standard practice in meteorology
- **Altitude Conversion**: Based on International Standard Atmosphere (ISA) model, which assumes standard atmospheric conditions
- **Grid Resolution**: GFS data at 0.25° resolution (~25km), HRRR at 3km resolution
- **Update Frequency**: GFS every 6 hours, HRRR every hour

### Known Limitations

- **Atmospheric Variations**: ISA model may not perfectly match actual atmospheric conditions
- **Terrain Effects**: Model doesn't account for local terrain influences on wind patterns
- **Temporal Resolution**: Limited to model output times (not real-time)
- **Ocean vs Land**: Data quality may vary over oceans vs. land areas
- **Extreme Weather**: Accuracy may decrease during severe weather events

### Best Practices

- **Current Conditions**: Use 0-hour forecast for most accurate current conditions
- **Short-term Planning**: Use 6-12 hour forecasts for near-term planning
- **Verification**: Compare with local observations when available
- **Multiple Sources**: Consider using multiple forecast hours for trend analysis

---

## 🌍 Data Coverage

- **Global Coverage**: Works for any location worldwide
- **Update Frequency**: GFS runs every 6 hours (00Z, 06Z, 12Z, 18Z)
- **Resolution**: 0.25-degree grid (approximately 25km)
- **Altitude Range**: 0 to 50,000 feet (limited by GFS pressure levels)
- **Forecast Period**: 0-hour analysis (current conditions)

---

## 🌎 Model Selection & Coverage

- **HRRR (High-Resolution Rapid Refresh):**
  - Coverage: Only the continental US (CONUS, 20°N–60°N, 140°W–50°W)
  - Does NOT cover Hawaii, Alaska, or US territories
  - Used automatically for locations within CONUS
- **GFS (Global Forecast System):**
  - Coverage: Global (including Hawaii, Alaska, and all other locations)
  - Used automatically for all locations outside CONUS

**The script will automatically select the best model based on your coordinates.**

---

## ⚙️ Advanced Usage

### Command Line Options

For automated or batch processing, you can modify the script to accept command line arguments:

```python
# Example: Add to the top of wind_profiler.py
import sys

if len(sys.argv) >= 4:
    lat = float(sys.argv[1])
    lon = float(sys.argv[2])
    max_elevation = int(sys.argv[3])
    forecast_hour = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    # Use these values instead of prompting
```

### Batch Processing

Create a script to process multiple locations:

```python
locations = [
    (32.22, -110.94, 20000),  # Tucson
    (52.52, 13.41, 15000),    # Berlin
    (21.31, -157.86, 25000),  # Honolulu
]

for lat, lon, max_elev in locations:
    # Process each location
    print(f"Processing {lat}, {lon}")
    # ... wind calculation code
```

### Data Analysis

The interpolated data can be used for:

- **Wind Shear Analysis**: Calculate wind shear between altitude levels
- **Trend Analysis**: Compare multiple forecast hours
- **Statistical Analysis**: Process multiple locations or time periods
- **Visualization**: Create wind profile plots using matplotlib

---

## 🛠️ Troubleshooting

### Common Issues

**"Failed to download" error:**
- Check internet connection
- NOAA servers may be temporarily unavailable
- Try running again in a few minutes

**"Error loading GFS data" error:**
- Ensure eccodes is properly installed
- Try deleting cached .grib2 files and re-downloading
- Check Python environment has all required packages

**Import errors:**
- Verify all dependencies are installed: `pip list | grep -E "(cfgrib|xarray|pandas|numpy|scipy)"`
- Consider using a virtual environment

**Environment issues:**
- Ensure you're in the correct virtual environment: `which python`
- Reinstall dependencies if needed: `pip install --upgrade cfgrib xarray pandas numpy scipy`

### Performance Tips

- **Caching**: Downloaded files are cached locally for faster subsequent runs
- **Location**: Script works best for locations over land (ocean data may be limited)
- **Timing**: GFS data is typically available 3-4 hours after each run time

---

## 📊 Use Cases

- **Aviation**: Pre-flight wind analysis and route planning
- **Skydiving**: Wind conditions at various altitudes
- **UAV/Drones**: Flight planning and safety assessment
- **Weather Analysis**: Local wind profile studies
- **Tactical Operations**: Environmental assessment
- **Research**: Meteorological data analysis

---

## 🔗 Data Sources

- **NOAA NOMADS**: [https://nomads.ncep.noaa.gov/](https://nomads.ncep.noaa.gov/)
- **GFS Model**: Global Forecast System documentation
- **GRIB2 Format**: WMO standard for meteorological data

---

## 📝 License

This project uses open-source libraries and publicly available NOAA data. No license restrictions apply.

---

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

---

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the code comments for technical details
3. Open an issue on the repository

## 🪁 How Are Winds Calculated Every 1,000 Feet?

- **Raw Data:** Both HRRR and GFS provide wind data at specific pressure levels (e.g., 1000 hPa, 925 hPa, 850 hPa, etc.), not at fixed altitude intervals.
- **Pressure-to-Altitude Conversion:** The script uses the International Standard Atmosphere (ISA) model to convert each pressure level to its corresponding altitude in feet.
- **Wind Components:** For each pressure level, the script extracts the U (east-west) and V (north-south) wind components, then calculates wind speed and direction.
- **Interpolation:**
  - The script creates a regular grid of altitudes from 0 to your specified maximum (e.g., 0 to 20,000 feet) in 1,000-foot increments.
  - It uses linear interpolation (via `scipy.interpolate.interp1d`) to estimate wind speed and direction at each 1,000-foot level, based on the values at the original pressure levels.
- **Result:**
  - You get a smooth, regularly spaced wind profile (every 1,000 feet) that is easy to read and use for aviation, ballooning, UAVs, and more.
