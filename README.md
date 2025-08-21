[![GitHub Release][releases-shield]][releases]
[![Total downloads][total-downloads-shield]][total-downloads]
[![Latest release downloads][latest-release-downloads-shield]][latest-release-downloads]

<p align="right">
<img width="50" alt="Logo" src="https://raw.githubusercontent.com/toringer/home-assistant-sildre/main/assets/icon.png">
</p>

# Home Assistant Sildre Component

A custom Home Assistant component for monitoring data from [Norwegian Water Resources and Energy Directorate (NVE)](https://www.nve.no/) stations using their Hydrological API.

## Features

- Monitor data from NVE stations across Norway
- Add station by id

<p align="center">
<img width="350" alt="sensor" src="https://raw.githubusercontent.com/toringer/home-assistant-sildre/main/assets/sensor.png">
</p>

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/sildre` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

### Method 2: HACS (Home Assistant Community Store)

This component is not yet available in HACS, but manual installation is recommended for now.

## Configuration


### Configuration Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `api_key` | string | yes | Your NVE Hydrological API key |
| `station id` | string | yes | Station id to monitor |



## Getting an API Key

1. Visit [NVE Hydrological API](https://hydapi.nve.no)
2. Click "Click here to create a API-key"
3. Enter your email address
4. Copy the generated API key

## Finding station id
1. Visit [Sildre](https://sildre.nve.no)
3. Find your station
4. You will find the station id on the about page for the station

## API Information

This component uses the NVE Hydrological API (HydAPI). For more information, visit: [https://hydapi.nve.no](https://hydapi.nve.no)

## Entities Created

For each configured station, the following entities will be created:

- **Sensor**: `sensor.{station_name}_mean_flooding_culqm` - Mean flooding based on observed values timestep
- **Sensor**: `sensor.{station_name}_5_year_flood_return_period_culq5` - 5-year flood return period (20% annual probability)
- **Sensor**: `sensor.{station_name}_50_year_flood_return_period_culq50` - 50-year flood return period (2% annual probability)

### Sensor Details

All culQ sensors provide flood statistics for hydrological analysis and flood risk assessment:

- **culQm**: Mean flooding based on the timestep for the observed values
- **culQ5**: Flood with a return period of 5 years (20% probability each year)
- **culQ50**: Flood with a return period of 50 years (2% probability each year)

These values are fetched from the NVE stations endpoint and provide crucial information for water resource management and flood risk assessment. The culQ sensors are implemented using a single, efficient sensor class that handles all three flood statistics values.

## Development

This project uses a devcontainer for development. To get started:

1. Open in VS Code with Dev Containers extension
2. The container will automatically install dependencies
3. Make your changes
4. Test locally before deploying

### Development Tasks

The devcontainer includes several VS Code tasks for Home Assistant development:

- **Start Home Assistant**: Starts Home Assistant in the background
- **Start Home Assistant (Development)**: Starts HA with UI auto-open and development options
- **Stop Home Assistant**: Stops any running Home Assistant instances


### Local Testing

1. Start Home Assistant
2. Access the UI at http://localhost:8123
3. Add the Sildre integration through the UI
4. Test with your API key and stations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions:

1. Check the [Home Assistant forums](https://community.home-assistant.io/)
2. Open an issue on this repository
3. Check the [NVE API documentation](https://hydapi.nve.no) for API-related questions


[releases-shield]: https://img.shields.io/github/v/release/toringer/home-assistant-sildre?style=flat-square
[releases]: https://github.com/toringer/home-assistant-sildre/releases
[total-downloads-shield]: https://img.shields.io/github/downloads/toringer/home-assistant-sildre/total?style=flat-square
[total-downloads]: https://github.com/toringer/home-assistant-sildre
[latest-release-downloads-shield]: https://img.shields.io/github/downloads/toringer/home-assistant-sildre/latest/total?style=flat-square
[latest-release-downloads]: https://github.com/toringer/home-assistant-sildre