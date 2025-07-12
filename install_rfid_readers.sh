#!/bin/bash

# Set variables
USER_TO_RUN=ubuntu
WORKDIR="/home/ubuntu/Fastag/fastag/rfid"
PYTHON_PATH="/home/ubuntu/Fastag/venv/bin/python"
VENV_PATH="/home/ubuntu/Fastag/venv/bin"
LAUNCHER="$WORKDIR/launcher_readers.py"
SERVICE_FILE="/etc/systemd/system/rfid_readers.service"

# 1. Create launcher_readers.py
cat > "$LAUNCHER" <<EOF
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
READER1 = os.path.join(BASE_DIR, "rfid_reader1_service.py")
READER2 = os.path.join(BASE_DIR, "rfid_reader2_service.py")

procs = []
for script in [READER1, READER2]:
    print(f"Starting {script} ...")
    procs.append(subprocess.Popen([sys.executable, script]))

try:
    for proc in procs:
        proc.wait()
except KeyboardInterrupt:
    print("Shutting down both readers...")
    for proc in procs:
        proc.terminate()
    for proc in procs:
        proc.wait()
EOF

chmod +x "$LAUNCHER"
echo "Created $LAUNCHER"

# 2. Create systemd service file
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=RFID Readers Launcher Service
After=network.target

[Service]
Type=simple
User=$USER_TO_RUN
WorkingDirectory=$WORKDIR
Environment=PATH=$VENV_PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$PYTHON_PATH $LAUNCHER
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "Created $SERVICE_FILE"

# 3. Reload systemd, enable and start the new service
sudo systemctl daemon-reload
sudo systemctl enable rfid_readers.service
sudo systemctl restart rfid_readers.service

echo "Enabled and started rfid_readers.service"

# 4. Disable and stop old rfid_services.service if it exists
if systemctl list-unit-files | grep -q rfid_services.service; then
    sudo systemctl stop rfid_services.service
    sudo systemctl disable rfid_services.service
    echo "Disabled and stopped old rfid_services.service"
fi

echo "Done! Use 'sudo systemctl status rfid_readers.service' to check status." 