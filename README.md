# NOAA Wind Profiler

A Python tool that downloads, extracts, and interpolates wind data from NOAA's HRRR, RAP, and GFS weather models to provide wind speed and direction profiles at various altitudes for a specified location.

---

## 🔒 Why Source Directly from NOAA?

For operations requiring atmospheric wind data, it may be advantageous to source forecasts directly from official U.S. government models such as HRRR, RAP, or GFS provided by NOAA, rather than relying on third-party public websites. While both methods involve retrieving data over the internet, using government-hosted sources may offer greater reliability and reduce exposure to unvetted external platforms. Additionally, once the data is downloaded, it can be processed locally without further internet access, enabling offline use in communications-restricted environments. This approach may enhance operational resilience and data integrity in tactical or field applications.

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

## Features

- **Multiple Weather Models**: Support for HRRR (High-Resolution Rapid Refresh), RAP (Rapid Refresh), and GFS (Global Forecast System)
- **Interactive Location Input**: Enter coordinates or use predefined city locations
- **Altitude Reference Options**: Choose between MSL (Mean Sea Level) and AGL (Above Ground Level)
- **Manual Ground Elevation Input**: User must enter ground elevation in feet MSL when using AGL
- **File Caching**: Avoids re-downloading the same forecast files
- **Multiple Output Formats**: CSV and human-readable text files
- **Progress Reporting**: Real-time download progress and status updates
- **Robust Error Handling**: Graceful handling of network issues and missing data

## File Sizes and Coverage

| Model | File Size | Coverage | Resolution | Max Altitude |
|-------|-----------|----------|------------|--------------|
| HRRR  | ~134 MB   | CONUS    | 3km        | ~34,000 ft   |
| RAP   | ~134 MB   | CONUS    | 13km       | ~39,000 ft   |
| GFS   | ~520 MB   | Global   | 25km       | ~50,000+ ft  |

## Security Benefits

- **Local Processing**: All data processing happens locally on your machine
- **No Location Tracking**: Your coordinates are never sent to external services
- **Offline Capable**: Once downloaded, forecast files can be used offline
- **Privacy Preserved**: No personal data or location information is transmitted
- **Operational Security**: Ideal for tactical, aviation, or field use where privacy is critical.

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script:
```bash
python wind_profiler.py
```

Follow the interactive prompts:
1. Enter latitude and longitude (or use predefined cities)
2. Choose maximum elevation (1,000 to 50,000 feet)
3. Select altitude reference (MSL or AGL)
4. If AGL, **enter ground elevation in feet MSL manually**
5. Choose weather model (HRRR, RAP, GFS, or Auto)
6. Select forecast hour
7. Choose to use cached file or download fresh data

## Altitude Reference Options

### MSL (Mean Sea Level)
- Heights are measured above sea level
- Consistent reference point worldwide
- Useful for aviation and standard atmospheric calculations

### AGL (Above Ground Level)
- Heights are measured above local terrain
- **User must enter ground elevation in feet MSL manually**
- More intuitive for ground-based applications

## Output Files

The tool generates two output files:

### CSV Format (`wind_profile_[lat]_[lon]_[model]_[hour]h.csv`)
```csv
Altitude_ft_AGL,Wind_Speed_kts,Wind_Direction_deg
0,1.67,304.51
1000,4.34,300.67
2000,7.00,296.83
...
```

### Human-Readable Format (`wind_profile_[lat]_[lon]_[model]_[hour]h.txt`)
```
HRRR Wind Profile for 40.7128°N, -74.0060°E
Forecast: Current conditions (0-hour analysis)
Altitude Reference: AGL (Above Ground Level)
Ground Elevation: 3 feet MSL
============================================================
 Altitude_ft_AGL  Wind_Speed_kts  Wind_Direction_deg
               0        1.669212          304.514958
            1000        4.336202          300.671300
            2000        7.003191          296.827641
...
```

## Weather Models

### HRRR (High-Resolution Rapid Refresh)
- **Coverage**: Continental United States
- **Resolution**: 3km
- **Update Frequency**: Hourly
- **Forecast Range**: 0-18 hours
- **Best For**: High-resolution local forecasts, severe weather

### RAP (Rapid Refresh)
- **Coverage**: Continental United States
- **Resolution**: 13km
- **Update Frequency**: Hourly
- **Forecast Range**: 0-21 hours
- **Best For**: Regional forecasts, aviation

### GFS (Global Forecast System)
- **Coverage**: Global
- **Resolution**: 25km
- **Update Frequency**: Every 6 hours
- **Forecast Range**: 0-384 hours
- **Best For**: Global coverage, long-range forecasts

### Auto Mode
- Automatically selects the most current available model
- Prioritizes HRRR for CONUS locations
- Falls back to GFS for international locations

## Error Handling

The tool includes comprehensive error handling for:
- **Network Issues**: Connection timeouts and download failures
- **Missing Data**: Unavailable forecast hours or models
- **File Corruption**: Invalid or incomplete downloads
- **Invalid Input**: Out-of-range coordinates or parameters

## Advanced Usage

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

## Troubleshooting

### Common Issues

- **"No GFS forecast files are currently available" error:**
  - GFS data may be temporarily unavailable
  - Try using Auto mode to select an available model
  - Try a different forecast hour
  - Wait a few hours and try again

- **"Failed to download" error:**
  - Check internet connection
  - NOAA servers may be temporarily unavailable
  - Try running again in a few minutes

- **"Error loading data" error:**
  - Ensure eccodes is properly installed
  - Try deleting cached .grib2 files and re-downloading
  - Check Python environment has all required packages

- **Import errors:**
  - Verify all dependencies are installed: `pip list | grep -E "(cfgrib|xarray|pandas|numpy|scipy)"`
  - Consider using a virtual environment

- **Environment issues:**
  - Ensure you're in the correct virtual environment: `which python`
  - Reinstall dependencies if needed: `pip install --upgrade -r requirements.txt`

### Performance Tips

- **Caching**: Downloaded files are cached locally for faster subsequent runs
- **Location**: Script works best for locations over land (ocean data may be limited)
- **Timing**: Model data is typically available 1-4 hours after each run time
- **Auto Mode**: Use Auto mode for best model selection and availability

## Example Output

The repository includes example output files from various locations and models:

- `wind_profile_40.71_-74.01_hrrr_0h.txt` — Wind profile for New York, NY (1-hour HRRR forecast)
- `wind_profile_52.52_13.40_gfs_3h.txt` — Wind profile for Berlin, Germany (3-hour GFS forecast)
- `wind_profile_35.69_139.69_gfs_3h.txt` — Wind profile for Tokyo, Japan (3-hour GFS forecast)

These files show the format and content you can expect when saving results as text files.

## Data Sources

- **NOAA NOMADS:** [https://nomads.ncep.noaa.gov/](https://nomads.ncep.noaa.gov/)
- **HRRR Model:** High-Resolution Rapid Refresh documentation
- **RAP Model:** Rapid Refresh documentation
- **GFS Model:** Global Forecast System documentation
- **GRIB2 Format:** WMO standard for meteorological data

## Requirements

- Python 3.7+
- Internet connection for initial data download
- ~1GB free disk space for cached files

## Dependencies

- `numpy`: Numerical computations
- `xarray`: NetCDF data handling
- `cfgrib`: GRIB2 file reading
- `requests`: HTTP downloads
- `tqdm`: Progress bars

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Disclaimer

This tool is for educational and research purposes. Always verify weather data from official sources for critical applications. The authors are not responsible for any decisions made based on this data.
