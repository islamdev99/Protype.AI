
import os
import sys

# Add .pythonlibs to Python path
pythonlibs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.pythonlibs')
if os.path.exists(pythonlibs_path) and pythonlibs_path not in sys.path:
    sys.path.insert(0, pythonlibs_path)
    # Also add site-packages directory inside .pythonlibs if it exists
    site_packages = os.path.join(pythonlibs_path, 'lib', 'python3.11', 'site-packages')
    if os.path.exists(site_packages) and site_packages not in sys.path:
        sys.path.insert(0, site_packages)
    
    print(f"Local libraries directory added to Python path: {pythonlibs_path}")
else:
    print("Local libraries directory not found or already in path")
