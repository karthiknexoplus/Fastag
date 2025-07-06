#!/bin/bash

# Manual deployment script for troubleshooting
# Run each section manually if the main deploy.sh fails

echo "🔧 Manual deployment script for Fastag"
echo "Run each section manually if needed"
echo ""

# Section 1: System setup
echo "=== SECTION 1: System Setup ==="
echo "sudo apt update && sudo apt upgrade -y"
echo "sudo apt install -y python3 python3-pip python3-venv nginx sqlite3 git curl"
echo ""

# Section 2: Application setup
echo "=== SECTION 2: Application Setup ==="
echo "sudo mkdir -p /home/ubuntu/Fastag"
echo "sudo chown ubuntu:ubuntu /home/ubuntu/Fastag"
echo "cd /home/ubuntu/Fastag"
echo ""

# Section 3: Virtual environment
echo "=== SECTION 3: Virtual Environment ==="
echo "cd /home/ubuntu/Fastag"
echo "sudo -u ubuntu python3 -m venv venv"
echo "ls -la /home/ubuntu/Fastag/venv/bin/"
echo ""

# Section 4: Python executable check
echo "=== SECTION 4: Python Executable Check ==="
echo "echo 'Checking Python executables:'"
echo "ls -la /home/ubuntu/Fastag/venv/bin/python*"
echo ""

# Section 5: Install dependencies
echo "=== SECTION 5: Install Dependencies ==="
echo "# If python3 exists:"
echo "sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/python3 -m pip install --upgrade pip"
echo "sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/python3 -m pip install -r requirements.txt"
echo ""
echo "# If only python exists:"
echo "sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/python -m pip install --upgrade pip"
echo "sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/python -m pip install -r requirements.txt"
echo ""

# Section 6: Database setup
echo "=== SECTION 6: Database Setup ==="
echo "sudo -u ubuntu mkdir -p /home/ubuntu/Fastag/logs"
echo "cd /home/ubuntu/Fastag"
echo "# Use the correct Python executable:"
echo "sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/python3 init_database.py"
echo "# OR"
echo "sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/python init_database.py"
echo ""

# Section 7: Service setup
echo "=== SECTION 7: Service Setup ==="
echo "sudo cp /home/ubuntu/Fastag/fastag.service /etc/systemd/system/"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable fastag"
echo "sudo systemctl start fastag"
echo "sudo systemctl status fastag"
echo ""

# Section 8: Nginx setup
echo "=== SECTION 8: Nginx Setup ==="
echo "sudo cp /home/ubuntu/Fastag/nginx.conf /etc/nginx/sites-available/fastag"
echo "sudo ln -sf /etc/nginx/sites-available/fastag /etc/nginx/sites-enabled/"
echo "sudo rm -f /etc/nginx/sites-enabled/default"
echo "sudo nginx -t"
echo "sudo systemctl enable nginx"
echo "sudo systemctl restart nginx"
echo ""

# Section 9: Firewall setup
echo "=== SECTION 9: Firewall Setup ==="
echo "sudo ufw allow 'Nginx Full'"
echo "sudo ufw allow ssh"
echo "sudo ufw --force enable"
echo ""

# Section 10: Permissions
echo "=== SECTION 10: Permissions ==="
echo "sudo chown -R ubuntu:ubuntu /home/ubuntu/Fastag"
echo "sudo chmod -R 755 /home/ubuntu/Fastag"
echo ""

echo "✅ Manual deployment commands listed above"
echo "Run each section as needed for troubleshooting" 