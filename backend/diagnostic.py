#!/usr/bin/env python3
"""
Quick diagnostic - Run this if API isn't working
Usage: python diagnostic.py
"""

import os
import sys

print("TEMPO API DIAGNOSTIC")
print("=" * 60)

# Check 1: Python version
print("\n1. Python Version")
print(f"   {sys.version}")
if sys.version_info < (3, 10):
    print("   ⚠ WARNING: Python 3.10+ recommended")

# Check 2: Required packages
print("\n2. Required Packages")
packages = {
    'fastapi': 'FastAPI',
    'earthaccess': 'NASA Earthdata Access',
    'netCDF4': 'NetCDF4',
    'numpy': 'NumPy',
    'dotenv': 'python-dotenv'
}

missing = []
for pkg, name in packages.items():
    try:
        __import__(pkg if pkg != 'dotenv' else 'dotenv')
        print(f"   ✓ {name}")
    except ImportError:
        print(f"   ✗ {name} - MISSING")
        missing.append(pkg if pkg != 'dotenv' else 'python-dotenv')

if missing:
    print(f"\n   Install missing: pip install {' '.join(missing)}")

# Check 3: .env file
print("\n3. Environment File")
env_paths = ['.env', 'backend/.env', '../.env']
env_found = False

for path in env_paths:
    if os.path.exists(path):
        print(f"   ✓ Found at: {path}")
        env_found = True
        
        # Load and check
        try:
            from dotenv import load_dotenv
            load_dotenv(path)
            
            username = os.getenv('NASA_USERNAME')
            password = os.getenv('NASA_PASSWORD')
            
            if username:
                print(f"   ✓ NASA_USERNAME: {username}")
            else:
                print("   ✗ NASA_USERNAME not set")
            
            if password:
                print(f"   ✓ NASA_PASSWORD: {'*' * len(password)}")
            else:
                print("   ✗ NASA_PASSWORD not set")
        except:
            pass
        break

if not env_found:
    print("   ✗ No .env file found")
    print("   Create backend/.env with:")
    print("   NASA_USERNAME=your_username")
    print("   NASA_PASSWORD=your_password")

# Check 4: Network connectivity
print("\n4. Network Connectivity")
try:
    import urllib.request
    urllib.request.urlopen('https://urs.earthdata.nasa.gov', timeout=5)
    print("   ✓ Can reach NASA Earthdata")
except Exception as e:
    print(f"   ✗ Cannot reach NASA Earthdata: {e}")

# Check 5: Quick auth test
print("\n5. Authentication Test")
try:
    from dotenv import load_dotenv
    import earthaccess
    
    load_dotenv()
    username = os.getenv('NASA_USERNAME')
    password = os.getenv('NASA_PASSWORD')
    
    if username and password:
        os.environ['EARTHDATA_USERNAME'] = username
        os.environ['EARTHDATA_PASSWORD'] = password
        auth = earthaccess.login(strategy='environment')
        print("   ✓ Authentication successful!")
    else:
        print("   ✗ Credentials not found")
except Exception as e:
    print(f"   ✗ Authentication failed: {e}")
    print("   Check credentials at: https://urs.earthdata.nasa.gov/")

# Check 6: Data search test
print("\n6. Data Availability Test")
try:
    import earthaccess
    from datetime import datetime, timedelta
    
    end = datetime.now()
    start = end - timedelta(days=7)
    
    results = earthaccess.search_data(
        short_name='TEMPO_NO2_L3',
        temporal=(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')),
        bounding_box=(-98, 36, -94, 40)
    )
    
    count = len(results) if results else 0
    if count > 0:
        print(f"   ✓ Found {count} TEMPO granules")
    else:
        print("   ⚠ No granules found (may be normal)")
        print("   Try: lat=38, lon=-96 in central USA")
except Exception as e:
    print(f"   ✗ Search failed: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("\nIf all checks passed:")
print("  → Run: python main.py")
print("  → Test: curl http://localhost:8000/health")
print("\nIf checks failed:")
print("  → Fix the issues shown above")
print("  → Run: python test_connection.py for detailed tests")
print("=" * 60)