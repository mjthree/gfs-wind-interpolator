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

## 📦 Requirements

- **Python 3.8+** (tested on Python 3.8-3.13)
- **Recommended**: macOS or Linux (Windows WSL also works)

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
   python winds_from_grib2.py
   ```

---

## 📖 Usage

### Basic Usage

```bash
python winds_from_grib2.py
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

## 🌍 Data Coverage

- **Global Coverage**: Works for any location worldwide
- **Update Frequency**: GFS runs every 6 hours (00Z, 06Z, 12Z, 18Z)
- **Resolution**: 0.25-degree grid (approximately 25km)
- **Altitude Range**: 0 to 50,000 feet (limited by GFS pressure levels)
- **Forecast Period**: 0-hour analysis (current conditions)

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
