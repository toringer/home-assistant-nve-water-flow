#!/usr/bin/env python3
"""Test script for NVE Water Flow component."""

import asyncio
import json
import sys
from pathlib import Path

# Add the custom_components directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

from nve_water_flow.nve_api import NVEAPI


async def test_nve_api():
    """Test the NVE API client."""
    # You'll need to get an API key from https://hydapi.nve.no
    api_key = input("Enter your NVE API key: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        return
    
    api = NVEAPI(api_key)
    
    try:
        print("Testing API connection...")
        await api.test_connection()
        print("✅ API connection successful!")
        
        # Test station name resolution
        test_stations = ["Gryta", "Lierelv", "Urula"]
        
        for station_name in test_stations:
            print(f"\nTesting station name resolution for: {station_name}")
            station_id = await api.resolve_station_name(station_name)
            
            if station_id:
                print(f"✅ Resolved '{station_name}' to ID: {station_id}")
                
                # Get water flow data
                print(f"Fetching water flow data for {station_name}...")
                water_flow_data = await api.get_water_flow_data(station_id)
                
                if water_flow_data:
                    print(f"✅ Water flow data retrieved:")
                    print(f"   Value: {water_flow_data.get('value')} {water_flow_data.get('unit')}")
                    print(f"   Time: {water_flow_data.get('time')}")
                    print(f"   Quality: {water_flow_data.get('quality')}")
                    print(f"   Method: {water_flow_data.get('method')}")
                else:
                    print(f"❌ No water flow data available for {station_name}")
            else:
                print(f"❌ Could not resolve station name: {station_name}")
        
        # Test getting station info
        print(f"\nTesting station info retrieval...")
        station_info = await api.get_station_info("6.10.0")  # Gryta station
        if station_info:
            print(f"✅ Station info retrieved:")
            print(f"   Name: {station_info.get('stationName')}")
            print(f"   ID: {station_info.get('stationId')}")
            print(f"   Active: {station_info.get('active')}")
        else:
            print("❌ Could not retrieve station info")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await api.close()


if __name__ == "__main__":
    print("NVE Water Flow Component Test")
    print("=" * 40)
    print("This script tests the NVE API client functionality.")
    print("Make sure you have an API key from https://hydapi.nve.no")
    print()
    
    asyncio.run(test_nve_api())
