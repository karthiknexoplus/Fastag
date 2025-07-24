# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes - use fewer workers for stability
workers = min(multiprocessing.cpu_count(), 2)
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging - use stdout/stderr instead of files to avoid permission issues
loglevel = "info"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Process naming
proc_name = "fastag"

# Server mechanics
daemon = False
user = None
group = None
tmp_upload_dir = None

# Preload app for better performance
preload_app = True

# SSL (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile" 