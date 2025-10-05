"""
Test script to verify NASA Earthdata credentials work
Run this before starting Docker: python test_setup.py
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

username = os.getenv("NASA_USERNAME")
password = os.getenv("NASA_PASSWORD")

print("Testing NASA Earthdata Setup...")
print("-" * 50)

# Check if credentials are set
if not username or not password:
    print("❌ ERROR: NASA credentials not found in .env file")
    print("\nMake sure your backend/.env file contains:")
    print("NASA_USERNAME=your_username")
    print("NASA_PASSWORD=your_password")
    exit(1)

print(f"✓ Username found: {username}")
print(f"✓ Password found: {'*' * len(password)}")

# Test earthaccess authentication
try:
    import earthaccess
    print("\n✓ earthaccess library installed")
    
    # Try to authenticate
    print("\nAttempting to authenticate with NASA Earthdata...")
    auth = earthaccess.login(strategy="environment")
    
    if auth:
        print("✅ SUCCESS! Authentication worked!")
        print("\nYou're ready to run: docker-compose up --build")
    else:
        print("❌ Authentication failed")
        print("Please check your credentials at: https://urs.earthdata.nasa.gov/")
        
except ImportError:
    print("\n❌ earthaccess not installed")
    print("Run: pip install -r requirements.txt")
except Exception as e:
    print(f"\n❌ Error during authentication: {e}")
    print("\nPossible issues:")
    print("1. Wrong username/password")
    print("2. No internet connection")
    print("3. NASA Earthdata services down")
    print("\nVerify credentials at: https://urs.earthdata.nasa.gov/")

print("-" * 50)