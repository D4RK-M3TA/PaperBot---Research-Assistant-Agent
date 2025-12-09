"""
Gunicorn configuration for Render deployment.
Optimized for memory-constrained environments.
"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
# Use only 1 worker to reduce memory usage on Render free tier
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 180  # Increased timeout for model loading (3 minutes)
keepalive = 5
max_requests = 1000  # Restart worker after N requests to prevent memory leaks
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "paperbot"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None
