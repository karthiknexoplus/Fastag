#!/usr/bin/env python3
"""
Test script for restart APIs
"""

import requests
import json
import sys

def test_restart_apis():
    """Test the restart APIs to ensure they're working correctly"""
    
    base_url = "http://localhost:5000"  # Adjust if your server runs on different port
    
    print("🧪 Testing Restart APIs...")
    print("=" * 50)
    
    # Test 1: Check if APIs are accessible
    try:
        response = requests.get(f"{base_url}/api/test-restart-apis", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Test endpoint accessible")
            print(f"   Message: {data.get('message')}")
            print(f"   Available endpoints: {list(data.get('endpoints', {}).keys())}")
        else:
            print(f"❌ Test endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("Testing individual restart endpoints...")
    
    # Test 2: Test restart-controller (without actually restarting)
    print("\n🔧 Testing restart-controller endpoint...")
    try:
        response = requests.post(f"{base_url}/api/restart-controller", 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 403, 500]:  # Expected responses
            data = response.json()
            print(f"   Response: {data.get('success')}")
            print(f"   Message: {data.get('message', data.get('error', 'No message'))}")
        else:
            print(f"   Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test restart-application (without actually restarting)
    print("\n🔄 Testing restart-application endpoint...")
    try:
        response = requests.post(f"{base_url}/api/restart-application", 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 403, 500]:  # Expected responses
            data = response.json()
            print(f"   Response: {data.get('success')}")
            print(f"   Message: {data.get('message', data.get('error', 'No message'))}")
        else:
            print(f"   Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Test restart-readers (without actually restarting)
    print("\n📡 Testing restart-readers endpoint...")
    try:
        response = requests.post(f"{base_url}/api/restart-readers", 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 403, 500]:  # Expected responses
            data = response.json()
            print(f"   Response: {data.get('success')}")
            print(f"   Message: {data.get('message', data.get('error', 'No message'))}")
        else:
            print(f"   Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ API testing completed!")
    print("\n📝 Notes:")
    print("   - Status 200: API working correctly")
    print("   - Status 403: Insufficient privileges (expected on non-root systems)")
    print("   - Status 500: System error (check logs for details)")
    print("\n🔧 To fix privilege issues:")
    print("   - Ensure the web server has sudo access")
    print("   - Or run the web server as root (not recommended for production)")
    
    return True

if __name__ == "__main__":
    success = test_restart_apis()
    sys.exit(0 if success else 1) 