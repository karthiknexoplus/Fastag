#!/usr/bin/env python3
"""
Test script for SSH functionality
"""

import requests
import json
import sys

def test_ssh_apis():
    """Test the SSH APIs to ensure they're working correctly"""
    
    base_url = "http://localhost:5000"  # Adjust if your server runs on different port
    
    print("🔌 Testing SSH APIs...")
    print("=" * 50)
    
    # Test 1: Connect to SSH
    print("\n🔗 Testing SSH connection...")
    try:
        response = requests.post(f"{base_url}/api/ssh/connect", 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                connection_id = data.get('connection_id')
                print(f"   ✅ SSH connection successful")
                print(f"   Connection ID: {connection_id}")
                
                # Test 2: Execute a simple command
                print("\n💻 Testing command execution...")
                cmd_response = requests.post(f"{base_url}/api/ssh/execute", 
                                          headers={'Content-Type': 'application/json'},
                                          json={
                                              'connection_id': connection_id,
                                              'command': 'pwd'
                                          },
                                          timeout=10)
                print(f"   Status: {cmd_response.status_code}")
                if cmd_response.status_code == 200:
                    cmd_data = cmd_response.json()
                    if cmd_data.get('success'):
                        print(f"   ✅ Command executed successfully")
                        print(f"   Output: {cmd_data.get('output', 'No output')}")
                        print(f"   Exit code: {cmd_data.get('exit_code')}")
                    else:
                        print(f"   ❌ Command failed: {cmd_data.get('error')}")
                else:
                    print(f"   ❌ Command execution failed: {cmd_response.status_code}")
                
                # Test 3: Disconnect SSH
                print("\n🔌 Testing SSH disconnect...")
                disconnect_response = requests.post(f"{base_url}/api/ssh/disconnect", 
                                                headers={'Content-Type': 'application/json'},
                                                json={'connection_id': connection_id},
                                                timeout=10)
                print(f"   Status: {disconnect_response.status_code}")
                if disconnect_response.status_code == 200:
                    disconnect_data = disconnect_response.json()
                    if disconnect_data.get('success'):
                        print(f"   ✅ SSH disconnected successfully")
                    else:
                        print(f"   ❌ Disconnect failed: {disconnect_data.get('error')}")
                else:
                    print(f"   ❌ Disconnect failed: {disconnect_response.status_code}")
                
            else:
                print(f"   ❌ SSH connection failed: {data.get('error')}")
        else:
            print(f"   ❌ SSH connection failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ SSH API testing completed!")
    
    return True

if __name__ == "__main__":
    success = test_ssh_apis()
    sys.exit(0 if success else 1) 