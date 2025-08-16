#!/usr/bin/env python3
"""Development scripts for NVE Water Flow component development."""

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add the custom_components directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

from nve_water_flow.nve_api import NVEAPI


def create_test_config(api_key: str, output_dir: str = "test_config") -> None:
    """Create a test Home Assistant configuration directory."""
    print(f"Creating test configuration in {output_dir}...")
    
    # Create test config directory
    config_dir = Path(output_dir)
    config_dir.mkdir(exist_ok=True)
    
    # Create custom_components directory
    custom_components_dir = config_dir / "custom_components"
    custom_components_dir.mkdir(exist_ok=True)
    
    # Copy the component
    component_source = Path("custom_components/nve_water_flow")
    component_dest = custom_components_dir / "nve_water_flow"
    
    if component_source.exists():
        if component_dest.exists():
            shutil.rmtree(component_dest)
        shutil.copytree(component_source, component_dest)
        print(f"✅ Component copied to {component_dest}")
    else:
        print("❌ Component source not found")
        return
    
    # Create configuration.yaml
    config_content = f"""# Test configuration for NVE Water Flow component
homeassistant:
  name: Test Home
  latitude: 59.9139
  longitude: 10.7522
  elevation: 0
  unit_system: metric
  time_zone: Europe/Oslo

# Enable the component
nve_water_flow:
  api_key: "{api_key}"
  stations:
    - name: "Gryta"
    - name: "Lierelv"
  scan_interval: 60  # Fast updates for testing

# Logging for debugging
logger:
  default: info
  logs:
    custom_components.nve_water_flow: debug
    homeassistant.components.nve_water_flow: debug

# HTTP interface
http:
  host: 0.0.0.0
  port: 8123
"""
    
    config_file = config_dir / "configuration.yaml"
    with open(config_file, "w") as f:
        f.write(config_content)
    
    print(f"✅ Configuration file created: {config_file}")
    print(f"✅ Test configuration ready in {output_dir}")
    print(f"   Run: cd {output_dir} && hass --open-ui")


async def test_api_connection(api_key: str) -> None:
    """Test the NVE API connection."""
    print("Testing NVE API connection...")
    
    api = NVEAPI(api_key)
    
    try:
        # Test connection
        await api.test_connection()
        print("✅ API connection successful!")
        
        # Test station resolution
        test_stations = ["Gryta", "Lierelv"]
        for station_name in test_stations:
            print(f"\nTesting station: {station_name}")
            station_id = await api.resolve_station_name(station_name)
            if station_id:
                print(f"✅ Resolved to ID: {station_id}")
                
                # Get water flow data
                data = await api.get_water_flow_data(station_id)
                if data:
                    print(f"✅ Water flow data: {data.get('value')} {data.get('unit')}")
                else:
                    print("⚠️  No water flow data available")
            else:
                print(f"❌ Could not resolve station: {station_name}")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
    finally:
        await api.close()


def start_home_assistant(config_dir: str = "test_config") -> None:
    """Start Home Assistant with the test configuration."""
    config_path = Path(config_dir)
    
    if not config_path.exists():
        print(f"❌ Configuration directory not found: {config_dir}")
        print("Run 'create_test_config' first")
        return
    
    print(f"Starting Home Assistant from {config_dir}...")
    
    try:
        # Change to config directory and start HA
        os.chdir(config_dir)
        subprocess.run([
            "hass", 
            "--open-ui", 
            "--skip-pip",
            "--verbose"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Home Assistant: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Home Assistant stopped by user")
    except FileNotFoundError:
        print("❌ 'hass' command not found. Make sure Home Assistant is installed.")


def main():
    """Main function for the development script."""
    print("NVE Water Flow Component - Development Tools")
    print("=" * 50)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python dev_scripts.py create_config <api_key>")
        print("  python dev_scripts.py test_api <api_key>")
        print("  python dev_scripts.py start_ha [config_dir]")
        print()
        print("Examples:")
        print("  python dev_scripts.py create_config YOUR_API_KEY")
        print("  python dev_scripts.py test_api YOUR_API_KEY")
        print("  python dev_scripts.py start_ha test_config")
        return
    
    command = sys.argv[1]
    
    if command == "create_config":
        if len(sys.argv) < 3:
            print("❌ API key required for create_config")
            return
        api_key = sys.argv[2]
        create_test_config(api_key)
        
    elif command == "test_api":
        if len(sys.argv) < 3:
            print("❌ API key required for test_api")
            return
        api_key = sys.argv[2]
        asyncio.run(test_api_connection(api_key))
        
    elif command == "start_ha":
        config_dir = sys.argv[2] if len(sys.argv) > 2 else "test_config"
        start_home_assistant(config_dir)
        
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
