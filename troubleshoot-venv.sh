#!/bin/bash

echo "🔍 Fastag Virtual Environment Troubleshooting"
echo "=============================================="
echo ""

# Check current directory
echo "📁 Current directory: $(pwd)"
echo ""

# Check if we're in the right place
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Make sure you're in the Fastag directory."
    exit 1
fi

echo "✅ Found requirements.txt - we're in the right place"
echo ""

# Check Python installation
echo "🐍 Checking Python installation:"
echo "Python3 version: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "Python3 location: $(which python3 2>/dev/null || echo 'Not found')"
echo ""

# Check if venv directory exists
echo "📂 Checking virtual environment:"
if [ -d "venv" ]; then
    echo "✅ venv directory exists"
    echo "Contents of venv/bin/:"
    ls -la venv/bin/ 2>/dev/null || echo "Cannot list venv/bin/"
    echo ""
    
    # Check Python executables
    echo "🔍 Python executables in venv:"
    if [ -f "venv/bin/python3" ]; then
        echo "✅ venv/bin/python3 exists"
        echo "Version: $(venv/bin/python3 --version 2>/dev/null || echo 'Cannot run')"
    else
        echo "❌ venv/bin/python3 not found"
    fi
    
    if [ -f "venv/bin/python" ]; then
        echo "✅ venv/bin/python exists"
        echo "Version: $(venv/bin/python --version 2>/dev/null || echo 'Cannot run')"
    else
        echo "❌ venv/bin/python not found"
    fi
    
    if [ -f "venv/bin/pip" ]; then
        echo "✅ venv/bin/pip exists"
    else
        echo "❌ venv/bin/pip not found"
    fi
else
    echo "❌ venv directory does not exist"
fi
echo ""

# Check permissions
echo "🔐 Checking permissions:"
echo "Current user: $(whoami)"
echo "Directory owner: $(ls -ld . | awk '{print $3}')"
echo "venv owner (if exists): $(ls -ld venv 2>/dev/null | awk '{print $3}' || echo 'N/A')"
echo ""

# Try to create a new venv
echo "🛠️ Attempting to create new virtual environment..."
echo "Removing existing venv if it exists..."
rm -rf venv 2>/dev/null

echo "Creating new venv with explicit Python path..."
/usr/bin/python3 -m venv venv

if [ $? -eq 0 ]; then
    echo "✅ Virtual environment created successfully"
    echo "New venv contents:"
    ls -la venv/bin/
    echo ""
    
    echo "🧪 Testing Python executable:"
    if [ -f "venv/bin/python3" ]; then
        echo "Testing venv/bin/python3:"
        venv/bin/python3 --version
        echo ""
    fi
    
    if [ -f "venv/bin/python" ]; then
        echo "Testing venv/bin/python:"
        venv/bin/python --version
        echo ""
    fi
    
    echo "🧪 Testing pip:"
    if [ -f "venv/bin/pip" ]; then
        echo "Testing venv/bin/pip:"
        venv/bin/pip --version
        echo ""
    fi
    
    echo "✅ Virtual environment is working correctly"
else
    echo "❌ Failed to create virtual environment"
    echo "Error code: $?"
fi 