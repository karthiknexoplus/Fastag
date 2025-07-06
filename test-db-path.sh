#!/bin/bash

echo "🔍 Database Path Test (Shell Script)"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: wsgi.py not found. Make sure you're in the Fastag directory."
    exit 1
fi

# Determine the correct Python executable
if [ -f "venv/bin/python3" ]; then
    PYTHON_EXEC="venv/bin/python3"
elif [ -f "venv/bin/python" ]; then
    PYTHON_EXEC="venv/bin/python"
else
    echo "❌ Error: No Python executable found in virtual environment"
    echo "Contents of venv/bin/:"
    ls -la venv/bin/
    exit 1
fi

echo "✅ Using Python executable: $PYTHON_EXEC"
echo ""

# Test database path
echo "🧪 Testing database path..."
$PYTHON_EXEC test-db-path.py

echo ""
echo "🧪 Testing application..."
$PYTHON_EXEC debug-app.py 