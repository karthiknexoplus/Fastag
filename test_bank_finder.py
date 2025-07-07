#!/usr/bin/env python3

import requests
import json

def test_bank_finder():
    print("🔍 Testing Bank Finder")
    print("======================")
    
    # Test 1: Direct API call
    print("\n1. Testing direct API call...")
    try:
        url = "https://netc-acq.airtelbank.com:9443/MTMSPG/GetTagDetails?SearchType=VRN&SearchValue=KA04MJ6369"
        headers = {
            'Cookie': 'TS019079a3=01e33451e79286adff54e3e927f807bfcd9f7c80ddddd702e8b4f170cd048b04d65f9b970279e11be29a68140b39a5625463daed81'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
    
    # Test 2: Local web app
    print("\n2. Testing local web app...")
    try:
        response = requests.post('http://localhost:8000/find-bank', data={
            'search_type': 'VRN',
            'search_value': 'KA04MJ6369'
        })
        print(f"Status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        
    except Exception as e:
        print(f"❌ Local app failed: {e}")
    
    # Test 3: Check if service is running
    print("\n3. Checking if service is running...")
    try:
        response = requests.get('http://localhost:8000/')
        print(f"Service status: {response.status_code}")
    except Exception as e:
        print(f"❌ Service not responding: {e}")

if __name__ == "__main__":
    test_bank_finder() 