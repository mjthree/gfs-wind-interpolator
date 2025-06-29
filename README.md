# NOAA Wind Profiler

---

## 🔒 Why Source Directly from NOAA?

For operations requiring atmospheric wind data, it may be advantageous to source forecasts directly from official U.S. government models such as HRRR, RAP, or GFS provided by NOAA, rather than relying on third-party public websites like the Mark Schulze wind profiler. While both methods involve retrieving data over the internet, using government-hosted sources may offer greater reliability and reduce exposure to unvetted external platforms. Additionally, once the data is downloaded, it can be processed locally without further internet access, enabling offline use in communications-restricted environments. This approach may enhance operational resilience and data integrity in tactical or field applications.

### 🔐 Enhanced Security Through Global Data Processing

**Local Location Processing:**
Unlike web-based wind profilers that send your specific coordinates to external servers, this tool downloads **complete global weather data** and processes your location information entirely on your local device. This approach provides several security advantages:

- **No Location Tracking**: Your exact coordinates are never transmitted to external servers
- **No Query Logs**: External services cannot log your location requests or usage patterns
- **Offline Capability**: Once downloaded, wind profiles can be generated without internet access
- **Operational Security**: Ideal for tactical operations where location privacy is critical

**How It Works:**
1. **Global Download**: Downloads complete weather data for the entire Earth (GFS) or continental region (HRRR/RAP)
2. **Local Processing**: Your device extracts and interpolates wind data for your specific location
3. **No External Queries**: No need to send coordinates to third-party services
4. **Cached Data**: Downloaded files can be reused for multiple locations without additional downloads

**Security Benefits:**
- **Location Privacy**: Your coordinates never leave your device
- **Usage Anonymity**: No external service can track your wind profiling activities
- **Reduced Digital Footprint**: Minimizes exposure to potential surveillance or tracking
- **Tactical Advantage**: Enables wind analysis in communications-restricted environments

This approach is particularly valuable for aviation, military operations, research, and any application where location privacy and operational security are priorities.

---

## ✨ Features

- **Interactive Location Selection**: Enter any latitude/longitude coordinates worldwide
- **Customizable Altitude Range**: Specify maximum elevation from 1,000 to 50,000 feet
- **Multiple Weather Models**: 
  - **HRRR** (High-Resolution Rapid Refresh) - Continental US, 3km resolution
  - **RAP** (Rapid Refresh) - Continental US, 13km resolution  
  - **GFS** (Global Forecast System) - Global coverage, 25km resolution
  - **Auto Mode** - Automatically selects the freshest available model
- **Latest Forecast Data**: Downloads the most recent forecast from NOAA
- **High-Resolution Interpolation**: Wind data interpolated to every 1,000 feet
- **Clean Output**: Tabular format with wind speed (knots) and direction (degrees)
- **Offline Capable**: Caches downloaded data for repeated use
- **No API Keys Required**: Uses publicly available NOAA data
- **Cross-Platform**: Works on macOS, Linux, and Windows (WSL)
- **Robust Error Handling**: Graceful handling of unavailable data and network issues
- **Progress Reporting**: Real-time download progress with file size and speed
- **Zulu Time Display**: All forecasts show valid UTC/Zulu time for precision

---

## 📦 Requirements

- **Python 3.8+** (tested on Python 3.8-3.13)
- **Recommended**: macOS or Linux (Windows WSL also works)

### System Requirements

- **Memory**: Minimum 2GB RAM (4GB+ recommended for large files)
- **Storage**: Varies by model (see File Sizes section below)
- **Network**: Internet connection for initial data download
- **Processing**: Single-core processing is sufficient

### Performance Considerations

- **First Run**: May take 1-5 minutes to download initial data (depending on model)
- **Subsequent Runs**: Typically 10-30 seconds with cached files
- **Cache Management**: Old files are automatically detected and can be refreshed

### Python Dependencies

Install all required Python packages using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
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

## 📊 File Sizes & Data Coverage

### Why Are the Files So Large?

The NOAA weather model files are massive because they contain **complete 3D snapshots of the entire atmosphere** at specific forecast times. Here's what makes them so large:

#### **Data Coverage by Model:**

**HRRR (High-Resolution Rapid Refresh):**
- **Coverage Area:** Continental United States only
- **Grid Size:** 1059 × 1059 = ~1.1 million grid points
- **Horizontal Resolution:** 3km (very high resolution)
- **File Size:** ~130-140 MB
- **Coverage:** ~10 million square kilometers

**RAP (Rapid Refresh):**
- **Coverage Area:** Continental United States
- **Grid Size:** 337 × 337 = ~114,000 grid points  
- **Horizontal Resolution:** 13km
- **File Size:** ~17-20 MB
- **Coverage:** ~10 million square kilometers

**GFS (Global Forecast System):**
- **Coverage Area:** **Entire Earth** (every square kilometer of the planet)
- **Grid Size:** 721 × 1440 = ~1.04 million grid points
- **Horizontal Resolution:** 25km
- **File Size:** ~520 MB
- **Coverage:** ~510 million square kilometers (entire Earth's surface)

#### **What's Inside Each File:**

Each file contains multiple meteorological variables at multiple pressure levels:

**Primary Variables (what we extract):**
- **`u`** - Eastward wind component (m/s)
- **`v`** - Northward wind component (m/s)

**Additional Variables (not used by our script):**
- **`gh`** - Geopotential height (geopotential meters)
- **`t`** - Temperature (Kelvin)
- **`dpt`** - Dew point temperature (Kelvin)
- **`wz`** - Vertical velocity (Pa/s)

**Pressure Levels:**
- **HRRR:** 7 levels (1000, 925, 850, 700, 500, 300, 250 hPa)
- **RAP:** Similar levels
- **GFS:** More comprehensive levels, goes higher in altitude

#### **Why We Need the Full Files:**

Even though we only extract wind data for one location, NOAA doesn't provide "point downloads." The wind components are distributed throughout the file at different pressure levels, so we need the complete 3D atmospheric state to interpolate wind data to any altitude.

**Think of it like this:** When you download GFS data for a wind profile in Berlin, you're actually downloading a complete snapshot of the world's weather at that moment - you're just extracting the wind data for that one specific location from the massive global dataset!

---

## 🐍 Environment Setup

### Recommended: Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python projects:

**Using venv (Python 3.3+):**
```bash
# Create virtual environment
python -m venv wind_env

# Activate virtual environment
# On macOS/Linux:
source wind_env/bin/activate
# On Windows:
wind_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Using conda:**
```bash
# Create conda environment
conda create -n wind_env python=3.11

# Activate environment
conda activate wind_env

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
   pip install -r requirements.txt
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
- **Model selection** (HRRR, RAP, GFS, or Auto)

### Model Selection

**For locations within the Continental United States (CONUS):**
- **HRRR** (High-Resolution Rapid Refresh): Highest resolution (3km), 0-18 hours
- **RAP** (Rapid Refresh): Medium resolution (13km), 0-21 hours  
- **GFS** (Global Forecast System): Lower resolution (25km), 0-384 hours
- **Auto** (Recommended): Automatically selects the freshest available model

**For locations outside CONUS (international):**
- **GFS** (Global Forecast System): Only option available, global coverage

### Example Session

```
NOAA Wind Profiler - Location Setup
========================================
Enter latitude (decimal degrees, -90 to 90): 40.7128
Enter longitude (decimal degrees, -180 to 180): -74.0060
Enter maximum elevation in feet (1000 to 50000): 10000

Location is within CONUS. Choose model:
1. HRRR (High-Resolution Rapid Refresh, up to ~34,000 ft)
2. RAP (Rapid Refresh, up to ~39,000 ft)
3. GFS (Global Forecast System, up to ~50,000+ ft)
4. Auto (Most Current Available)
Select model (1=HRRR, 2=RAP, 3=GFS, 4=Auto): 4

Auto mode: Checking all models for most current available forecast...
Auto-selected model: HRRR (valid for 2025-06-29 04:00Z)
Downloading hrrr.t03z.wrfsfcf01.grib2 from NOAA...
Downloaded: 134.91 MB / 134.91 MB (100.0%)
Download complete. File size: 134.91 MB. Time: 9.4s. Speed: 14.35 MB/s.

HRRR Wind Profile for 40.7128°N, -74.0060°E
Forecast: 1 hour from now
============================================================
 Altitude_ft  Wind_Speed_kts  Wind_Direction_deg
           0        3.373525          241.694966
        1000        6.712482          241.871594
        2000       10.051440          242.048221
        ...
       10000       13.089032          239.220947
```

### Auto Mode

The **Auto mode** is recommended for most users as it:
- Automatically checks all available models (HRRR, RAP, GFS)
- Selects the model with the most current valid forecast
- Ensures you get the freshest available data
- Handles model availability issues gracefully

### Forecast Hours Selection

The script allows you to select forecast hours for more detailed analysis:

- **HRRR Model**: 0 to 18 hours (hourly intervals)
- **RAP Model**: 0 to 21 hours (hourly intervals)  
- **GFS Model**: 0 to 384 hours (6-hour intervals for longer forecasts)

```
Enter forecast hour: 0
```

- **0-hour**: Current analysis (most accurate for current conditions)
- **1-hour**: 1-hour forecast
- **6-hour**: 6-hour forecast
- And so on...

### File Caching

The script automatically caches downloaded files and asks whether to use cached or fresh data:

```
Found cached file: hrrr.t03z.wrfsfcf01.grib2
File age: 5 minutes ago
File size: 134.9 MB
Use cached file or download fresh? (c/d): c
```

- **Cached files**: Faster execution, no re-download needed
- **Fresh files**: Ensures latest data, but requires download time
- **File age**: Shows when the cached file was downloaded
- **File size**: Helps verify data integrity

### Data Export

Results can be saved to both CSV and human-readable text files:

```
Save results to file? (y/n): y
Results saved to: wind_profile_40.71_-74.01_hrrr_1h.csv
Human-readable results saved to: wind_profile_40.71_-74.01_hrrr_1h.txt
CSV results saved to: wind_profile_40.71_-74.01_hrrr_1h.csv
```

**File naming convention:** `wind_profile_<lat>_<lon>_<model>_<forecast_hour>h.<ext>`

### Output Format

- **Altitude_ft**: Height above ground level in feet
- **Wind_Speed_kts**: Wind speed in knots (1 knot ≈ 1.15 mph)
- **Wind_Direction_deg**: Wind direction in degrees (meteorological convention)
  - 0° = North, 90° = East, 180° = South, 270° = West
- **Valid_Zulu_Time**: UTC/Zulu time when the forecast is valid

---

## 🔧 How It Works

1. **Location Analysis**: Determines if location is within CONUS for model selection
2. **Model Selection**: Chooses appropriate weather model (HRRR/RAP/GFS/Auto)
3. **Data Source**: Downloads latest forecast from NOAA NOMADS servers
4. **File Format**: Processes .grib2 files using cfgrib library
5. **Wind Components**: Extracts U (eastward) and V (northward) wind components
6. **Calculations**: Converts to wind speed and direction using meteorological formulas
7. **Altitude Conversion**: Maps pressure levels to altitude using International Standard Atmosphere (ISA)
8. **Interpolation**: Smoothly interpolates wind data to 1,000-foot intervals
9. **Output**: Displays results in a clean, tabular format with Zulu time

**Security Note**: All location processing occurs locally on your device. Your coordinates are never transmitted to external servers - the tool downloads complete global/regional weather data and extracts your specific location's wind profile locally.

---

## 📊 Data Accuracy & Limitations

### Interpolation Quality

- **Linear Interpolation**: Uses linear interpolation between pressure levels, which is standard practice in meteorology
- **Altitude Conversion**: Based on International Standard Atmosphere (ISA) model, which assumes standard atmospheric conditions
- **Grid Resolution**: 
  - HRRR: 3km resolution (highest detail)
  - RAP: 13km resolution (medium detail)
  - GFS: 25km resolution (global coverage)
- **Update Frequency**: 
  - HRRR: Every hour
  - RAP: Every hour
  - GFS: Every 6 hours

### Known Limitations

- **Atmospheric Variations**: ISA model may not perfectly match actual atmospheric conditions
- **Terrain Effects**: Model doesn't account for local terrain influences on wind patterns
- **Temporal Resolution**: Limited to model output times (not real-time)
- **Ocean vs Land**: Data quality may vary over oceans vs. land areas
- **Extreme Weather**: Accuracy may decrease during severe weather events

### Best Practices

- **Current Conditions**: Use 0-hour forecast for most accurate current conditions
- **Short-term Planning**: Use 1-6 hour forecasts for near-term planning
- **Auto Mode**: Use Auto mode for best model selection
- **Verification**: Compare with local observations when available
- **Multiple Sources**: Consider using multiple forecast hours for trend analysis

---

## 🌍 Data Coverage

### Model Coverage Areas

- **HRRR**: Continental United States only (20°N–60°N, 140°W–50°W)
- **RAP**: Continental United States and nearby regions
- **GFS**: Global coverage (entire Earth)
- **Auto**: Automatically selects best available model for location

### Update Frequency

- **HRRR**: Every hour (00Z, 01Z, 02Z, etc.)
- **RAP**: Every hour (00Z, 01Z, 02Z, etc.)
- **GFS**: Every 6 hours (00Z, 06Z, 12Z, 18Z)

### Resolution & Altitude

- **HRRR**: 3km resolution, up to ~34,000 feet
- **RAP**: 13km resolution, up to ~39,000 feet
- **GFS**: 25km resolution, up to ~50,000+ feet

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

## 🔬 Raw Data Viewer (Testing Only)

For debugging and testing purposes, a separate script `raw_data_viewer.py` is included that shows all raw pressure level data without interpolation.

### Features:
- **All Variables**: Displays every available variable (wind, temperature, humidity, etc.)
- **All Pressure Levels**: Shows data at every pressure level in the model
- **No Interpolation**: Raw values exactly as provided by NOAA
- **Model Selection**: Choose between HRRR, RAP, and GFS
- **CSV Export**: Save complete raw data to CSV files

### Usage:
```bash
python raw_data_viewer.py
```

**Note**: This script is for testing, debugging, and data analysis only. For operational wind profiling, use `wind_profiler.py` which provides clean, interpolated output.

---

## 🛠️ Troubleshooting

### Common Issues

**"No GFS forecast files are currently available" error:**
- GFS data may be temporarily unavailable
- Try using Auto mode to select an available model
- Try a different forecast hour
- Wait a few hours and try again

**"Failed to download" error:**
- Check internet connection
- NOAA servers may be temporarily unavailable
- Try running again in a few minutes

**"Error loading data" error:**
- Ensure eccodes is properly installed
- Try deleting cached .grib2 files and re-downloading
- Check Python environment has all required packages

**Import errors:**
 - Verify all dependencies are installed: `pip list | grep -E "(cfgrib|xarray|pandas|numpy|scipy)"`
- Consider using a virtual environment

**Environment issues:**
- Ensure you're in the correct virtual environment: `which python`
- Reinstall dependencies if needed: `pip install --upgrade -r requirements.txt`

### Performance Tips

- **Caching**: Downloaded files are cached locally for faster subsequent runs
- **Location**: Script works best for locations over land (ocean data may be limited)
- **Timing**: Model data is typically available 1-4 hours after each run time
- **Auto Mode**: Use Auto mode for best model selection and availability

---

## 📊 Use Cases

- **Aviation**: Pre-flight wind analysis and route planning
- **Skydiving**: Wind conditions at various altitudes
- **UAV/Drones**: Flight planning and safety assessment
- **Weather Analysis**: Local wind profile studies
- **Tactical Operations**: Environmental assessment
- **Research**: Meteorological data analysis
- **Ballooning**: Wind conditions for balloon flights
- **Paragliding**: Wind profile analysis for launch decisions

---

## 🔗 Data Sources

- **NOAA NOMADS**: [https://nomads.ncep.noaa.gov/](https://nomads.ncep.noaa.gov/)
- **HRRR Model**: High-Resolution Rapid Refresh documentation
- **RAP Model**: Rapid Refresh documentation
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

## ⚠️ Disclaimer

This software is provided "as is," without warranty of any kind, express or implied. Use of this tool and the data it produces is at your own risk. The authors and contributors are not responsible for any loss, damage, or consequences resulting from the use of this software or its outputs, including but not limited to operational, financial, or safety impacts. This tool is not certified for use in life-critical or aviation navigation applications. Always verify results with official sources and exercise appropriate judgment.

## 🪁 How Are Winds Calculated Every 1,000 Feet?

- **Raw Data:** All models provide wind data at specific pressure levels (e.g., 1000 hPa, 925 hPa, 850 hPa, etc.), not at fixed altitude intervals.
- **Pressure-to-Altitude Conversion:** The script uses the International Standard Atmosphere (ISA) model to convert each pressure level to its corresponding altitude in feet.
- **Wind Components:** For each pressure level, the script extracts the U (east-west) and V (north-south) wind components, then calculates wind speed and direction.
- **Interpolation:**
  - The script creates a regular grid of altitudes from 0 to your specified maximum elevation in 1,000-foot increments.
  - It uses linear interpolation (via `scipy.interpolate.interp1d`) to estimate wind speed and direction at each 1,000-foot level, based on the values at the original pressure levels.
- **Result:**
  - You get a smooth, regularly spaced wind profile (every 1,000 feet) that is easy to read and use for aviation, ballooning, UAVs, and more.

## 📁 Repository Files

- **`wind_profiler.py`**: Main wind profiling script (interpolated output)
- **`raw_data_viewer.py`**: Raw data viewer for testing/debugging
- **`README.md`**: This documentation
- **`requirements.txt`**: Python dependencies list
- **`.gitignore`**: Excludes data files and system files from version control

## 📄 Example Output

The repository includes example output files from various locations and models:

- `wind_profile_40.71_-74.01_hrrr_1h.txt` — Wind profile for New York, NY (1-hour HRRR forecast)
- `wind_profile_52.52_13.40_gfs_3h.txt` — Wind profile for Berlin, Germany (3-hour GFS forecast)
- `wind_profile_35.69_139.69_gfs_3h.txt` — Wind profile for Tokyo, Japan (3-hour GFS forecast)

These files show the format and content you can expect when saving results as text files.
