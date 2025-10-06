#!/usr/bin/env python3
"""
Quick test script to verify TEMPO connection
Run: python test_connection.py
"""

import os
from datetime import datetime, timedelta

def test_credentials():
    """Test 1: Check if credentials are loaded"""
    print("\n" + "="*60)
    print("TEST 1: CREDENTIALS")
    print("="*60)
    
    # Try loading from .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ dotenv loaded")
    except ImportError:
        print("✗ python-dotenv not installed")
        return False
    
    username = os.getenv("NASA_USERNAME")
    password = os.getenv("NASA_PASSWORD")
    
    if username:
        print(f"✓ NASA_USERNAME: {username}")
    else:
        print("✗ NASA_USERNAME not found")
        return False
    
    if password:
        print(f"✓ NASA_PASSWORD: {'*' * len(password)}")
    else:
        print("✗ NASA_PASSWORD not found")
        return False
    
    return True

def test_earthaccess():
    """Test 2: Check earthaccess installation and auth"""
    print("\n" + "="*60)
    print("TEST 2: EARTHACCESS AUTHENTICATION")
    print("="*60)
    
    try:
        import earthaccess
        print("✓ earthaccess imported")
    except ImportError:
        print("✗ earthaccess not installed")
        print("  Install: pip install earthaccess")
        return False
    
    username = os.getenv("NASA_USERNAME")
    password = os.getenv("NASA_PASSWORD")
    
    try:
        os.environ["EARTHDATA_USERNAME"] = username
        os.environ["EARTHDATA_PASSWORD"] = password
        
        auth = earthaccess.login(strategy="environment", persist=True)
        print("✓ Authentication successful")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("\nCheck:")
        print("  1. Credentials are correct at https://urs.earthdata.nasa.gov/")
        print("  2. You've authorized the application")
        return False

def test_search_tempo():
    """Test 3: Search for TEMPO data"""
    print("\n" + "="*60)
    print("TEST 3: SEARCH TEMPO DATA")
    print("="*60)
    
    try:
        import earthaccess
        
        # Test locations with known TEMPO coverage
        locations = [
            ("New York", 40.7128, -74.0060),
            ("Los Angeles", 34.0522, -118.2437),
            ("Mexico City", 19.4326, -99.1332)
        ]
        
        # Try both L2 and L3 for NO2
        datasets = ["TEMPO_NO2_L3", "TEMPO_NO2_L2"]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)
        
        print(f"\nSearching from {start_date.date()} to {end_date.date()}")
        
        found_any = False
        for dataset in datasets:
            print(f"\n  Testing dataset: {dataset}")
            
            for city, lat, lon in locations:
                try:
                    results = earthaccess.search_data(
                        short_name=dataset,
                        temporal=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
                        bounding_box=(lon - 2, lat - 2, lon + 2, lat + 2)
                    )
                    
                    count = len(results) if results else 0
                    if count > 0:
                        print(f"    ✓ {city}: {count} granules found")
                        found_any = True
                    else:
                        print(f"    - {city}: 0 granules")
                        
                except Exception as e:
                    print(f"    ✗ {city}: Error - {str(e)[:50]}")
        
        if found_any:
            print("\n✓ TEMPO data is accessible!")
            return True
        else:
            print("\n⚠ No TEMPO data found")
            print("  This could mean:")
            print("  - Data processing delay")
            print("  - Limited coverage for selected dates/locations")
            print("  - Try locations in central USA (e.g., 38, -96)")
            return False
            
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return False

def test_download():
    """Test 4: Try downloading a small file"""
    print("\n" + "="*60)
    print("TEST 4: DOWNLOAD TEST (Optional)")
    print("="*60)
    
    try:
        import earthaccess
        import tempfile
        
        print("Searching for a single granule to test download...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)
        
        # Try to find any TEMPO granule
        results = earthaccess.search_data(
            short_name="TEMPO_NO2_L3",
            temporal=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
            bounding_box=(-98, 36, -94, 40)  # Central USA
        )
        
        if not results or len(results) == 0:
            print("⚠ No granules found for download test")
            return False
        
        print(f"Found {len(results)} granules, attempting download of first one...")
        
        temp_dir = tempfile.mkdtemp()
        downloaded = earthaccess.download(results[0], temp_dir)
        
        if downloaded:
            import os
            file_size = os.path.getsize(downloaded[0]) / (1024 * 1024)
            print(f"✓ Download successful!")
            print(f"  File: {os.path.basename(downloaded[0])}")
            print(f"  Size: {file_size:.2f} MB")
            
            # Cleanup
            os.remove(downloaded[0])
            os.rmdir(temp_dir)
            return True
        else:
            print("✗ Download failed")
            return False
            
    except Exception as e:
        print(f"✗ Download test failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("TEMPO CONNECTION TEST SUITE")
    print("="*60)
    
    results = {
        "Credentials": test_credentials(),
        "Authentication": False,
        "Data Search": False,
        "Download": False
    }
    
    if results["Credentials"]:
        results["Authentication"] = test_earthaccess()
    
    if results["Authentication"]:
        results["Data Search"] = test_search_tempo()
    
    if results["Data Search"]:
        print("\nDo you want to test download? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                results["Download"] = test_download()
        except:
            print("Skipping download test")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Your TEMPO connection is working.")
    elif results["Data Search"]:
        print("\n✓ Connection works! You can start using the API.")
    else:
        print("\n⚠ Some tests failed. Check the errors above.")
        print("\nNext steps:")
        print("1. Verify credentials at https://urs.earthdata.nasa.gov/")
        print("2. Ensure earthaccess is installed: pip install earthaccess")
        print("3. Check .env file is in the correct directory")
    
    print("="*60)

if __name__ == "__main__":
    main()