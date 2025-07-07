#!/bin/bash

echo "🔍 Network Connectivity Test"
echo "=========================="

echo ""
echo "🔍 Step 1: Testing basic connectivity..."
echo "Pinging netc-acq.airtelbank.com:"
ping -c 3 netc-acq.airtelbank.com || echo "❌ Ping failed"

echo ""
echo "🔍 Step 2: Testing port connectivity..."
echo "Testing port 9443:"
nc -zv netc-acq.airtelbank.com 9443 || echo "❌ Port 9443 not reachable"

echo ""
echo "🔍 Step 3: Testing HTTPS connection..."
echo "Testing HTTPS to port 9443:"
curl -v --connect-timeout 10 https://netc-acq.airtelbank.com:9443/ || echo "❌ HTTPS connection failed"

echo ""
echo "🔍 Step 4: Testing with our exact API call..."
echo "Testing API endpoint:"
curl -v --connect-timeout 15 \
  --header 'Cookie: TS019079a3=01e33451e7b854085a12a2adda21afb8b67e65bff140d6ffc9e52d261b87f3ac2b3e82a63ad5d64082b9384016fc1d05aceca47d2c' \
  'https://netc-acq.airtelbank.com:9443/MTMSPG/GetTagDetails?SearchType=VRN&SearchValue=KA04MJ6369' || echo "❌ API call failed"

echo ""
echo "🔍 Step 5: Checking outbound connections..."
echo "Current outbound connections:"
netstat -an | grep :443 || echo "No HTTPS connections found"

echo ""
echo "🎯 Summary:"
echo "If curl works but Python doesn't, it's a Python/requests issue"
echo "If curl also fails, it's a network/firewall issue" 