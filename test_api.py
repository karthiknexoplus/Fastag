#!/usr/bin/env python3
"""
Test script to demonstrate the FASTag Device API
This simulates how external devices would interact with the API
"""

import requests
import json
import time

# API base URL (adjust if running on different port)
BASE_URL = "http://localhost:8000/api"

def test_device_status():
    """Test the health check endpoint"""
    print("🔍 Testing device status...")
    try:
        response = requests.get(f"{BASE_URL}/device/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_device_lookup(mac_address):
    """Test the device lookup endpoint"""
    print(f"\n🔍 Looking up device with MAC: {mac_address}")
    
    payload = {
        "mac_address": mac_address
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/device/lookup",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                device_info = data['data']
                print(f"\n✅ Device found!")
                print(f"   Reader ID: {device_info['reader_id']}")
                print(f"   Type: {device_info['type']}")
                print(f"   IP: {device_info['reader_ip']}")
                print(f"   Lane: {device_info['lane']['lane_name']}")
                print(f"   Location: {device_info['lane']['location']['name']} ({device_info['lane']['location']['site_id']})")
            else:
                print("❌ Device lookup failed")
        elif response.status_code == 404:
            print("❌ Device not found in system")
        else:
            print("❌ Unexpected error")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_device_register(mac_address):
    """Test the device registration endpoint"""
    print(f"\n🔍 Testing device registration for MAC: {mac_address}")
    
    payload = {
        "mac_address": mac_address,
        "type": "reader"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/device/register",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code in [200, 404]  # Both are valid responses
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 FASTag Device API Test")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_device_status():
        print("❌ API is not available. Make sure the Flask app is running on port 8000")
        return
    
    # Test 2: Device lookup with valid MAC (you'll need to adjust this MAC address)
    # to match a reader that exists in your database
    test_mac = "00:1A:2B:3C:4D:5E"  # Replace with actual MAC from your database
    test_device_lookup(test_mac)
    
    # Test 3: Device lookup with invalid MAC
    test_device_lookup("FF:FF:FF:FF:FF:FF")
    
    # Test 4: Device registration
    test_device_register(test_mac)
    
    print("\n" + "=" * 50)
    print("✅ API test completed!")
    
    print("\n📋 Usage Examples for External Devices:")
    print("1. Health Check: GET /api/device/status")
    print("2. Device Lookup: POST /api/device/lookup")
    print("   Payload: {\"mac_address\": \"00:1A:2B:3C:4D:5E\"}")
    print("3. Device Register: POST /api/device/register")
    print("   Payload: {\"mac_address\": \"00:1A:2B:3C:4D:5E\", \"type\": \"reader\"}")

if __name__ == "__main__":
    main() 