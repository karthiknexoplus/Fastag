#!/bin/bash

echo "🔧 Quick Fix for Fastag Application"
echo "==================================="
echo ""

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: wsgi.py not found. Make sure you're in the Fastag directory."
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo ""

# Check virtual environment
echo "🐍 Checking virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    echo "Python executables in venv/bin/:"
    ls -la venv/bin/python*
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Determine Python executable
if [ -f "venv/bin/python" ]; then
    PYTHON_EXEC="venv/bin/python"
    echo "✅ Using: venv/bin/python"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_EXEC="venv/bin/python3"
    echo "✅ Using: venv/bin/python3"
else
    echo "❌ No Python executable found in venv"
    exit 1
fi

echo ""

# Check and create instance directory
echo "📂 Checking instance directory..."
if [ ! -d "instance" ]; then
    echo "Creating instance directory..."
    mkdir -p instance
    echo "✅ Instance directory created"
else
    echo "✅ Instance directory exists"
fi

# Check database file
echo "🗄️ Checking database file..."
if [ ! -f "instance/fastag.db" ]; then
    echo "Creating database..."
    $PYTHON_EXEC init_database.py
    echo "✅ Database created"
else
    echo "✅ Database file exists"
fi

# Fix permissions
echo "🔐 Fixing permissions..."
sudo chown -R ubuntu:ubuntu .
sudo chmod -R 755 .

# Test database connection
echo "🧪 Testing database connection..."
$PYTHON_EXEC -c "
import os
print(f'Current directory: {os.getcwd()}')
print(f'Instance directory exists: {os.path.exists(\"instance\")}')
print(f'Database file exists: {os.path.exists(\"instance/fastag.db\")}')
if os.path.exists('instance/fastag.db'):
    print(f'Database size: {os.path.getsize(\"instance/fastag.db\")} bytes')
"

echo ""

# Test application
echo "🧪 Testing application..."
$PYTHON_EXEC -c "
from fastag import create_app
app = create_app()
print('✅ Application created successfully')
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    locations = db.execute('SELECT * FROM locations').fetchall()
    print(f'✅ Database connection successful - Found {len(locations)} locations')
"

echo ""

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart fastag
sudo systemctl status fastag --no-pager

echo ""
echo "✅ Quick fix completed!"
echo ""
echo "🌐 Test your application:"
echo "   http://your-ec2-public-ip" 