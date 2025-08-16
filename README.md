# Home Assistant NVE Water Flow Component

A custom Home Assistant component for monitoring water flow data from Norwegian Water Resources and Energy Directorate (NVE) stations using their Hydrological API.

## Features

- Monitor water flow from NVE stations across Norway
- Add stations by name (automatically resolves station ID)
- Real-time water flow data updates
- Configurable update intervals
- Support for multiple stations

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/nve_water_flow` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the component to your `configuration.yaml`

### Method 2: HACS (Home Assistant Community Store)

This component is not yet available in HACS, but manual installation is recommended for now.

## Configuration

Add the following to your `configuration.yaml`:

```yaml
nve_water_flow:
  api_key: "YOUR_NVE_API_KEY"
  stations:
    - name: "Gryta"
    - name: "Lierelv"
  scan_interval: 300  # Update every 5 minutes (optional, default: 300)
```

### Configuration Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `api_key` | string | yes | - | Your NVE Hydrological API key |
| `stations` | list | yes | - | List of stations to monitor |
| `scan_interval` | integer | no | 300 | Update interval in seconds |

### Station Configuration

Each station can be configured with:

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `name` | string | yes | - | Station name (will be resolved to station ID) |

## Getting an API Key

1. Visit [NVE Hydrological API](https://hydapi.nve.no)
2. Click "Click here to create a API-key"
3. Enter your email address
4. Copy the generated API key

## API Information

This component uses the NVE Hydrological API (HydAPI) which provides:
- Water flow data (parameter ID: 1001)
- Real-time and historical data
- Data from stations across Norway
- Multiple time resolutions (instantaneous, hourly, daily)

For more information, visit: [https://hydapi.nve.no](https://hydapi.nve.no)

## Entities Created

For each configured station, the following entities will be created:

- **Sensor**: `sensor.{station_name}_water_flow` - Current water flow rate
- **Sensor**: `sensor.{station_name}_water_flow_unit` - Unit of measurement
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

### Development Scripts

Use the included development script for common tasks:

```bash
# Create a test configuration
python dev_scripts.py create_config YOUR_API_KEY

# Test API connection
python dev_scripts.py test_api YOUR_API_KEY

# Start Home Assistant with test config
python dev_scripts.py start_ha test_config
```

### Local Testing

1. Create a test configuration: `python dev_scripts.py create_config YOUR_API_KEY`
2. Start Home Assistant: `python dev_scripts.py start_ha test_config`
3. Access the UI at http://localhost:8123
4. Add the NVE Water Flow integration through the UI
5. Test with your API key and stations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions:

1. Check the [Home Assistant forums](https://community.home-assistant.io/)
2. Open an issue on this repository
3. Check the [NVE API documentation](https://hydapi.nve.no) for API-related questions
