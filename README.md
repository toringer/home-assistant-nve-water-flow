[![GitHub Release][releases-shield]][releases]
[![Total downloads][total-downloads-shield]][total-downloads]
[![Latest release downloads][latest-release-downloads-shield]][latest-release-downloads]

<p align="right">
<img width="50" alt="Logo" src="https://raw.githubusercontent.com/toringer/home-assistant-nve-water-flow/main/assets/icon.png">
</p>

# Home Assistant NVE Water Flow Component

A custom Home Assistant component for monitoring water flow data from [Norwegian Water Resources and Energy Directorate (NVE)](https://www.nve.no/) stations using their Hydrological API.

## Features

- Monitor water flow from NVE stations across Norway
- Add station by id
- Real-time water flow data updates

<p align="center">
<img width="50" alt="sensor" src="https://raw.githubusercontent.com/toringer/home-assistant-nve-water-flow/main/assets/sensor.png">
</p>

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/nve_water_flow` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

### Method 2: HACS (Home Assistant Community Store)

This component is not yet available in HACS, but manual installation is recommended for now.

## Configuration


### Configuration Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `api_key` | string | yes | - | Your NVE Hydrological API key |
| `station id` | string | yes | - | Station id to monitor |



## Getting an API Key

1. Visit [NVE Hydrological API](https://hydapi.nve.no)
2. Click "Click here to create a API-key"
3. Enter your email address
4. Copy the generated API key

## Finding station id
1. Visit [Sildre](https://sildre.nve.no)
2. Filter for "Water flow"
3. Find your station
4. You will find the station id on the about page for the station

## API Information

This component uses the NVE Hydrological API (HydAPI). For more information, visit: [https://hydapi.nve.no](https://hydapi.nve.no)

## Entities Created

For each configured station, the following entities will be created:

- **Sensor**: `sensor.{station_name}_water_flow` - Current water flow rate
- **Sensor**: `sensor.{station_name}_last_update` - Last data update timestamp

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
3. Add the NVE Water Flow integration through the UI
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


[releases-shield]: https://img.shields.io/github/v/release/toringer/home-assistant-nve-water-flow?style=flat-square
[releases]: https://github.com/toringer/home-assistant-nve-water-flow/releases
[total-downloads-shield]: https://img.shields.io/github/downloads/toringer/home-assistant-nve-water-flow/total?style=flat-square
[total-downloads]: https://github.com/toringer/home-assistant-nve-water-flow
[latest-release-downloads-shield]: https://img.shields.io/github/downloads/toringer/home-assistant-nve-water-flow/latest/total?style=flat-square
[latest-release-downloads]: https://github.com/toringer/home-assistant-nve-water-flow