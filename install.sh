#!/bin/bash

# NVE Water Flow Component Installation Script
# This script helps install the component in your Home Assistant setup

echo "NVE Water Flow Component Installation"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -d "custom_components/nve_water_flow" ]; then
    echo "Error: Please run this script from the project root directory"
    echo "Make sure you can see the 'custom_components' folder"
    exit 1
fi

# Get Home Assistant config directory
echo "Please enter the path to your Home Assistant configuration directory:"
echo "This is usually something like:"
echo "  - /config (if using Home Assistant OS)"
echo "  - /home/username/homeassistant (if using Home Assistant Core)"
echo "  - /opt/homeassistant (if using Docker)"
echo ""
read -p "Config directory path: " CONFIG_DIR

# Check if directory exists
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Error: Directory '$CONFIG_DIR' does not exist"
    exit 1
fi

# Check if it looks like a Home Assistant config directory
if [ ! -d "$CONFIG_DIR/custom_components" ]; then
    echo "Creating custom_components directory..."
    mkdir -p "$CONFIG_DIR/custom_components"
fi

# Copy the component
echo "Installing NVE Water Flow component..."
cp -r custom_components/nve_water_flow "$CONFIG_DIR/custom_components/"

# Check if copy was successful
if [ $? -eq 0 ]; then
    echo "✅ Component installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Restart Home Assistant"
    echo "2. Go to Settings > Devices & Services"
    echo "3. Click 'Add Integration' and search for 'NVE Water Flow'"
    echo "4. Enter your NVE API key from https://hydapi.nve.no"
    echo "5. Add the stations you want to monitor"
    echo ""
    echo "For configuration examples, see configuration.yaml.example"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
