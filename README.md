# NOAA Wind Profiler

A Python tool that downloads, extracts, and interpolates wind data from NOAA's HRRR, RAP, and GFS weather models to provide wind speed and direction profiles at various altitudes for a specified location.

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

## Examples

### New York City (40.7128°N, -74.0060°E)
```bash
python wind_profiler.py
# Enter: 40.7128, -74.0060, 10000, 2, 1, 0
```

### Los Angeles (34.0522°N, -118.2437°E)
```bash
python wind_profiler.py
# Enter: 34.0522, -118.2437, 15000, 2, 1, 0
```

### International Location (London: 51.5074°N, -0.1278°E)
```bash
python wind_profiler.py
# Enter: 51.5074, -0.1278, 20000, 2, 3, 0
```

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
