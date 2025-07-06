#!/bin/bash

echo "🔧 Fixing Database Issues"
echo "========================"
echo ""

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: wsgi.py not found. Make sure you're in the Fastag directory."
    exit 1
fi

echo "📁 Checking database directory and file..."
echo ""

# Check instance directory
if [ ! -d "instance" ]; then
    echo "📂 Creating instance directory..."
    mkdir -p instance
    echo "✅ Instance directory created"
else
    echo "✅ Instance directory exists"
fi

# Check database file
if [ ! -f "instance/fastag.db" ]; then
    echo "🗄️ Database file not found. Creating new database..."
    cd /home/ubuntu/Fastag
    source venv/bin/activate
    python3 init_database.py
    echo "✅ Database created successfully"
else
    echo "✅ Database file exists"
fi

# Fix permissions
echo "🔐 Fixing permissions..."
sudo chown -R ubuntu:ubuntu instance/
sudo chmod -R 755 instance/
echo "✅ Permissions fixed"

# Test database
echo "🧪 Testing database..."
cd /home/ubuntu/Fastag
source venv/bin/activate
python3 -c "
from fastag import create_app
app = create_app()
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    locations = db.execute('SELECT * FROM locations').fetchall()
    print(f'✅ Database test successful - Found {len(locations)} locations')
"

echo ""
echo "🔄 Restarting application..."
sudo systemctl restart fastag
sudo systemctl status fastag --no-pager

echo ""
echo "✅ Database fix completed!"
echo ""
echo "🌐 Test your application now:"
echo "   http://your-ec2-public-ip" 