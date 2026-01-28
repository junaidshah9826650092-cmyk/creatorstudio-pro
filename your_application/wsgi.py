import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app as application
except ImportError:
    # Fallback if structure is different on Render
    from ..main import app as application
