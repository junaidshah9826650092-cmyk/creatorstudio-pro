import sys
import os

# Add the parent directory to the path so we can import server.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from server import app
except ImportError:
    # Try direct import if path is already set
    from server import app

# Match common gunicorn/WSGI entry points
application = app
wsgi = app
app = app
