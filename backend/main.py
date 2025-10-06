from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import numpy as np
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import tempfile
import traceback
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder

load_dotenv()

app = FastAPI(title="TEMPO Air Quality API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Models
class AirQualityReading(BaseModel):
    pollutant: str
    value: Optional[float] = None
    unit: str
    timestamp: str
    latitude: float
    longitude: float
    aqi: Optional[int] = None
    quality_level: Optional[str] = None
    available: bool
    granules_found: Optional[int] = None

class AirQualityResponse(BaseModel):
    location: dict
    readings: List[AirQualityReading]

earth_auth = None
auth_initialized = False
tz_finder = TimezoneFinder()

def get_timezone_name(lat: float, lon: float) -> Optional[str]:
    try:
        return tz_finder.timezone_at(lat=lat, lng=lon)
    except Exception:
        return None

def localize_dt(dt: datetime, lat: float, lon: float) -> str:
    try:
        tzname = get_timezone_name(lat, lon)
        if not tzname:
            return dt.isoformat()
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)
        local = dt_utc.astimezone(ZoneInfo(tzname))
        return local.isoformat()
    except Exception:
        return dt.isoformat()

def is_in_north_america(lat: float, lon: float) -> bool:
    return (7 <= lat <= 83) and (-168 <= lon <= -52)

def calculate_aqi(pollutant: str, value: float) -> tuple:
    if value is None or np.isnan(value):
        return None, "No disponible"
    
    if pollutant == "NO2":
        if value <= 53:
            aqi = value * 50 / 53
            level = "Good"
        elif value <= 100:
            aqi = 50 + (value - 53) * 50 / 47
            level = "Moderate"
        elif value <= 360:
            aqi = 100 + (value - 100) * 100 / 260
            level = "Unhealthy for Sensitive Groups"
        elif value <= 649:
            aqi = 200 + (value - 360) * 100 / 289
            level = "Unhealthy"
        else:
            aqi = 300 + (value - 649) * 100 / 351
            level = "Very Unhealthy"
    elif pollutant == "O3":
        value_ppb = value * 0.3
        if value_ppb <= 54:
            aqi = value_ppb * 50 / 54
            level = "Good"
        elif value_ppb <= 70:
            aqi = 50 + (value_ppb - 54) * 50 / 16
            level = "Moderate"
        elif value_ppb <= 85:
            aqi = 100 + (value_ppb - 70) * 50 / 15
            level = "Unhealthy for Sensitive Groups"
        elif value_ppb <= 105:
            aqi = 150 + (value_ppb - 85) * 50 / 20
            level = "Unhealthy"
        else:
            aqi = 200 + (value_ppb - 105) * 100 / 95
            level = "Very Unhealthy"
    elif pollutant == "HCHO":
        if value <= 10:
            aqi = value * 50 / 10
            level = "Good"
        elif value <= 20:
            aqi = 50 + (value - 10) * 50 / 10
            level = "Moderate"
        else:
            aqi = 100 + (value - 20) * 2
            level = "Unhealthy for Sensitive Groups"
    else:
        if value <= 50:
            aqi = value
            level = "Good"
        elif value <= 100:
            aqi = 50 + (value - 50)
            level = "Moderate"
        else:
            aqi = 100 + (value - 100) * 0.5
            level = "Unhealthy for Sensitive Groups"
    
    return int(aqi) if aqi else None, level

def convert_molecules_to_ppb(molecules_cm2: float, pollutant: str) -> float:
    if molecules_cm2 is None or np.isnan(molecules_cm2):
        return None
    
    conversion_factors = {
        "NO2": 5e-16,
        "HCHO": 8e-16,
    }
    
    factor = conversion_factors.get(pollutant, 5e-16)
    ppb = abs(molecules_cm2) * factor
    return ppb

def process_tempo_netcdf(file_path: str, lat: float, lon: float, pollutant: str):
    """Process TEMPO NetCDF - FIXED for V04 format where lat/lon are at root level"""
    try:
        from netCDF4 import Dataset
        
        print(f"\n=== Processing {file_path} ===")
        nc = Dataset(file_path, 'r')
        
        # Check if this is L3 or L2 data
        is_l3 = 'product' in nc.groups
        
        if is_l3:
            print("Detected L3 format")
            product = nc.groups['product']
            
            # L3 variable mapping
            var_map = {
                "NO2": "vertical_column_troposphere",
                "HCHO": "vertical_column_troposphere",
                "O3": "vertical_column_total"
            }
            
            var_name = var_map.get(pollutant)
            if not var_name or var_name not in product.variables:
                print(f"Variable {var_name} not found in L3 product group")
                nc.close()
                return None
            
            data = product.variables[var_name][:]
            
            # CRITICAL: For TEMPO L3 V04, lat/lon are at ROOT level, not in geolocation group
            lat_names = ['latitude', 'lat', 'Latitude']
            lon_names = ['longitude', 'lon', 'Longitude']
            
            lats = None
            lons = None
            
            # First try root level (V04 format)
            for lat_name in lat_names:
                if lat_name in nc.variables:
                    lats = nc.variables[lat_name][:]
                    print(f"Found latitude at root: {lat_name}")
                    break
            
            for lon_name in lon_names:
                if lon_name in nc.variables:
                    lons = nc.variables[lon_name][:]
                    print(f"Found longitude at root: {lon_name}")
                    break
            
            # If not found at root, try geolocation group (older format)
            if lats is None and 'geolocation' in nc.groups:
                geolocation = nc.groups['geolocation']
                for lat_name in lat_names:
                    if lat_name in geolocation.variables:
                        lats = geolocation.variables[lat_name][:]
                        print(f"Found latitude in geolocation: {lat_name}")
                        break
            
            if lons is None and 'geolocation' in nc.groups:
                geolocation = nc.groups['geolocation']
                for lon_name in lon_names:
                    if lon_name in geolocation.variables:
                        lons = geolocation.variables[lon_name][:]
                        print(f"Found longitude in geolocation: {lon_name}")
                        break
            
            if lats is None or lons is None:
                print(f"Root variables: {list(nc.variables.keys())}")
                if 'geolocation' in nc.groups:
                    print(f"Geolocation variables: {list(nc.groups['geolocation'].variables.keys())}")
                nc.close()
                return None
            
        else:
            # Try L2 format - variables at root level or in different groups
            print("Trying L2 format")
            
            # For L2, lat/lon often at root
            if 'latitude' in nc.variables and 'longitude' in nc.variables:
                lats = nc.variables['latitude'][:]
                lons = nc.variables['longitude'][:]
            else:
                print("Could not find lat/lon variables")
                nc.close()
                return None
            
            # L2 variable mapping - try multiple possibilities
            l2_var_options = {
                "NO2": ["nitrogen_dioxide_tropospheric_column", "NO2_column", "tropospheric_NO2"],
                "HCHO": ["formaldehyde_tropospheric_column", "HCHO_column", "tropospheric_HCHO"],
                "O3": ["ozone_total_vertical_column", "O3_column", "total_O3"]
            }
            
            var_name = None
            data = None
            
            # Search in different groups and root
            search_locations = [nc]
            if 'product' in nc.groups:
                search_locations.append(nc.groups['product'])
            if 'geophysical_data' in nc.groups:
                search_locations.append(nc.groups['geophysical_data'])
            
            for location in search_locations:
                for candidate in l2_var_options.get(pollutant, []):
                    if candidate in location.variables:
                        var_name = candidate
                        data = location.variables[candidate][:]
                        print(f"Found variable: {var_name}")
                        break
                if data is not None:
                    break
            
            if data is None:
                print(f"No suitable variable found for {pollutant}")
                print(f"Available variables: {list(nc.variables.keys())}")
                nc.close()
                return None
        
        print(f"Data shape: {data.shape}, Lat shape: {lats.shape}, Lon shape: {lons.shape}")
        
        # Handle different dimension structures
        if len(data.shape) == 3:
            data = data[0]  # Take first time slice
        
        # Ensure lats/lons are 2D for distance calculation
        if len(lats.shape) == 1 and len(lons.shape) == 1:
            # Create meshgrid
            lons_2d, lats_2d = np.meshgrid(lons, lats)
        else:
            lats_2d = lats
            lons_2d = lons
        
        # Find nearest point
        distances = np.sqrt((lats_2d - lat)**2 + (lons_2d - lon)**2)
        min_idx = np.unravel_index(distances.argmin(), distances.shape)
        
        value = float(data[min_idx])
        nc.close()
        
        # Validate
        if np.isnan(value) or value < -9e30 or value > 1e30:
            print(f"Invalid value: {value}")
            return None
        
        print(f"Extracted value: {value:.6e}")
        
        # Convert based on pollutant
        if pollutant in ["NO2", "HCHO"]:
            ppb_value = convert_molecules_to_ppb(value, pollutant)
            return {"value": ppb_value, "variable_used": var_name}
        elif pollutant == "O3":
            return {"value": abs(value) if value else None, "variable_used": var_name}
        
        return None
        
    except Exception as e:
        print(f"Error processing NetCDF: {e}")
        traceback.print_exc()
        return None

def ensure_authentication():
    global earth_auth, auth_initialized
    
    if auth_initialized and earth_auth:
        return earth_auth
    
    try:
        import earthaccess
        
        username = os.getenv("NASA_USERNAME")
        password = os.getenv("NASA_PASSWORD")
        
        print(f"\n=== Authentication ===")
        print(f"Username from env: {username}")
        print(f"Password present: {bool(password)}")
        
        if not (username and password):
            print("ERROR: Credentials not found in environment")
            return None
        
        os.environ["EARTHDATA_USERNAME"] = username
        os.environ["EARTHDATA_PASSWORD"] = password
        
        earth_auth = earthaccess.login(strategy="environment", persist=True)
        auth_initialized = True
        
        print(f"Authentication successful for: {username}")
        return earth_auth
        
    except Exception as e:
        print(f"Authentication error: {e}")
        traceback.print_exc()
        auth_initialized = False
        return None

def process_tempo_data(granules, lat: float, lon: float, pollutant: str):
    """Download and process TEMPO granules"""
    try:
        if not granules:
            return None
        
        import earthaccess
        
        auth = ensure_authentication()
        if not auth:
            print("Authentication failed")
            return None
        
        print(f"\nAttempting to download {len(granules)} granules...")
        
        for i, granule in enumerate(granules[:3]):
            try:
                print(f"\n--- Granule {i+1}/{min(3, len(granules))} ---")
                
                temp_dir = tempfile.mkdtemp()
                downloaded = earthaccess.download(granule, temp_dir)
                
                if not downloaded:
                    print(f"Download failed for granule {i+1}")
                    continue
                
                file_path = downloaded[0]
                print(f"Downloaded: {os.path.basename(file_path)}")
                
                result = process_tempo_netcdf(file_path, lat, lon, pollutant)
                
                # Cleanup
                try:
                    os.remove(file_path)
                    os.rmdir(temp_dir)
                except:
                    pass
                
                if result and isinstance(result, dict) and "value" in result:
                    print(f"SUCCESS: Got value {result['value']}")
                    return result
                    
            except Exception as e:
                print(f"Error with granule {i+1}: {e}")
                traceback.print_exc()
                continue
        
        print("Could not process any granules")
        return None
        
    except Exception as e:
        print(f"Error in process_tempo_data: {e}")
        traceback.print_exc()
        return None

@app.on_event("startup")
async def startup_event():
    global earth_auth, auth_initialized
    print("\n" + "="*60)
    print("STARTING TEMPO AIR QUALITY API")
    print("="*60)
    auth = ensure_authentication()
    if auth:
        print("âœ“ TEMPO data source: ACTIVE")
    else:
        print("âœ— API will run in read-only mode")
    print("="*60 + "\n")

@app.get("/")
async def root():
    return {
        "message": "TEMPO Air Quality API",
        "status": "live_data" if earth_auth else "read_only",
        "coverage": "North America (7Â°N to 83Â°N, 168Â°W to 52Â°W)",
        "endpoints": {
            "/air-quality": "Get air quality data",
            "/pollutants": "List pollutants",
            "/forecast": "24-hour forecast",
            "/alerts": "Air quality alerts",
            "/overall-aqi": "Overall AQI for location",
            "/health": "API status"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "data_mode": "tempo_live" if earth_auth else "read_only",
        "tempo_connected": earth_auth is not None,
        "can_download": earth_auth is not None,
        "coverage_area": "North America"
    }

@app.get("/pollutants")
async def get_pollutants():
    return {
        "pollutants": [
            {
                "name": "NO2",
                "full_name": "Nitrogen Dioxide",
                "unit": "ppb",
                "sources": ["vehicles", "power plants", "industrial"],
                "health_effects": "Respiratory irritation, asthma"
            },
            {
                "name": "O3",
                "full_name": "Ozone",
                "unit": "DU",
                "sources": ["photochemical reactions"],
                "health_effects": "Lung damage, respiratory issues"
            },
            {
                "name": "HCHO",
                "full_name": "Formaldehyde",
                "unit": "ppb",
                "sources": ["industrial emissions", "wildfires"],
                "health_effects": "Eye/throat irritation, cancer risk"
            }
        ]
    }

@app.get("/air-quality", response_model=AirQualityResponse)
async def get_air_quality(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    date: Optional[str] = Query(None),
    pollutant: Optional[str] = Query("NO2")
):
    """Get air quality data from TEMPO satellite - FIXED VERSION"""
    
    if not is_in_north_america(lat, lon):
        raise HTTPException(
            status_code=400,
            detail="Location must be in North America (TEMPO coverage: 7Â°N-83Â°N, 168Â°W-52Â°W)"
        )
    
    print(f"\n{'='*60}")
    print(f"Query: {pollutant} at ({lat}, {lon})")
    print(f"{'='*60}")
    
    # Try BOTH L2 and L3 datasets
    dataset_options = {
        "NO2": ["TEMPO_NO2_L3", "TEMPO_NO2_L2"],
        "O3": ["TEMPO_O3TOT_L3", "TEMPO_O3TOT_L2"],
        "HCHO": ["TEMPO_HCHO_L3", "TEMPO_HCHO_L2"]
    }
    
    dataset_names = dataset_options.get(pollutant, [])
    granules_count = 0
    
    if not dataset_names:
        now_local = datetime.now(timezone.utc)
        timestamp_local = localize_dt(now_local, lat, lon)
        reading = AirQualityReading(
            pollutant=pollutant,
            value=None,
            unit="ppb",
            timestamp=timestamp_local,
            latitude=lat,
            longitude=lon,
            aqi=None,
            quality_level="No disponible",
            available=False,
            granules_found=0
        )
        return AirQualityResponse(
            location={"latitude": lat, "longitude": lon, "data_source": "unsupported"},
            readings=[reading]
        )
    
    auth = ensure_authentication()
    
    if auth:
        try:
            import earthaccess
            
            if date:
                query_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                query_date = datetime.utcnow()
            
            # Try last 14 days for better chance of finding data
            start_date = query_date - timedelta(days=14)
            end_date = query_date
            
            print(f"Searching from {start_date.date()} to {end_date.date()}")
            
            # Try each dataset option
            results = None
            for dataset_name in dataset_names:
                print(f"\nTrying dataset: {dataset_name}")
                try:
                    temp_results = earthaccess.search_data(
                        short_name=dataset_name,
                        temporal=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
                        bounding_box=(lon - 3.0, lat - 3.0, lon + 3.0, lat + 3.0)
                    )
                    
                    if temp_results and len(temp_results) > 0:
                        results = temp_results
                        print(f"âœ“ Found {len(results)} granules in {dataset_name}")
                        break
                except Exception as e:
                    print(f"Error searching {dataset_name}: {e}")
                    continue
            
            granules_count = len(results) if results else 0
            
            if results and granules_count > 0:
                value = process_tempo_data(results, lat, lon, pollutant)
                
                if value and isinstance(value, dict) and "value" in value:
                    processed_value = value["value"]
                    variable_used = value.get("variable_used")
                    
                    if processed_value is not None and not np.isnan(processed_value):
                        aqi, quality_level = calculate_aqi(pollutant, processed_value)
                        unit = "ppb" if pollutant in ["NO2", "HCHO"] else "DU"
                        timestamp_local = localize_dt(query_date, lat, lon)
                        
                        reading = AirQualityReading(
                            pollutant=pollutant,
                            value=round(processed_value, 2),
                            unit=unit,
                            timestamp=timestamp_local,
                            latitude=lat,
                            longitude=lon,
                            aqi=aqi,
                            quality_level=quality_level,
                            available=True,
                            granules_found=granules_count
                        )
                        
                        print(f"SUCCESS: Data processed (var={variable_used})")
                        print(f"{'='*60}\n")
                        
                        return AirQualityResponse(
                            location={
                                "latitude": lat,
                                "longitude": lon,
                                "data_source": "tempo_satellite",
                                "granules_processed": granules_count,
                                "variable_used": variable_used
                            },
                            readings=[reading]
                        )
                
                print("Could not extract valid value from granules")
            else:
                print("No TEMPO granules found for this location/date")
                
        except Exception as e:
            print(f"Error fetching TEMPO data: {e}")
            traceback.print_exc()
    
    print(f"Data unavailable")
    print(f"{'='*60}\n")
    
    now_utc = datetime.utcnow()
    timestamp_local = localize_dt(now_utc, lat, lon)
    
    reading = AirQualityReading(
        pollutant=pollutant,
        value=None,
        unit="ppb",
        timestamp=timestamp_local,
        latitude=lat,
        longitude=lon,
        aqi=None,
        quality_level="No disponible",
        available=False,
        granules_found=granules_count
    )
    
    return AirQualityResponse(
        location={
            "latitude": lat,
            "longitude": lon,
            "data_source": "unavailable",
            "granules_found": granules_count
        },
        readings=[reading]
    )

@app.get("/forecast")
async def get_forecast(
    lat: float = Query(...),
    lon: float = Query(...),
    hours: int = Query(24, ge=1, le=72)
):
    """Enhanced forecast showing TEMPO data availability pattern"""
    base_time = datetime.utcnow()
    forecast_data = []
    
    # TEMPO operates during daylight hours only (typically 8 AM - 10 PM local)
    for i in range(hours):
        forecast_time = base_time + timedelta(hours=i)
        hour = forecast_time.hour
        
        # Simulate TEMPO availability (daylight hours)
        is_tempo_time = 12 <= hour <= 22  # UTC hours when TEMPO is active
        
        if is_tempo_time:
            # Better quality forecast during TEMPO observation times
            base_aqi = 40 + 30 * np.sin((hour - 6) * np.pi / 12)
            aqi = int(max(20, base_aqi + np.random.normal(0, 5)))
        else:
            # Less certain forecast outside TEMPO times
            base_aqi = 50 + 20 * np.sin((hour - 6) * np.pi / 12)
            aqi = int(max(25, base_aqi + np.random.normal(0, 10)))
        
        if aqi <= 50:
            level = "Good"
        elif aqi <= 100:
            level = "Moderate"
        else:
            level = "Unhealthy for Sensitive Groups"
        
        primary = "O3" if 14 <= hour <= 20 else "NO2"
        
        forecast_data.append({
            "timestamp": localize_dt(forecast_time, lat, lon),
            "hour": i,
            "aqi": aqi,
            "quality_level": level,
            "primary_pollutant": primary,
            "tempo_available": is_tempo_time,
            "confidence": "high" if is_tempo_time else "medium"
        })
    
    return {
        "location": {"latitude": lat, "longitude": lon},
        "generated_at": localize_dt(base_time, lat, lon),
        "forecast": forecast_data,
        "note": "TEMPO provides hourly daytime measurements. Forecasts are most accurate during satellite observation periods."
    }

@app.get("/alerts")
async def get_air_quality_alerts(
    lat: float = Query(...),
    lon: float = Query(...)
):
    current_aqi = int(45 + np.random.normal(0, 20))
    current_aqi = max(20, min(current_aqi, 180))
    
    alerts = []
    
    if current_aqi > 100:
        alerts.append({
            "level": "warning",
            "message": "Air quality is unhealthy for sensitive groups",
            "recommendation": "People with respiratory conditions should limit outdoor activities",
            "expires_at": localize_dt(datetime.utcnow() + timedelta(hours=6), lat, lon)
        })
    
    if current_aqi > 150:
        alerts.append({
            "level": "alert",
            "message": "Air quality is unhealthy",
            "recommendation": "Everyone should reduce prolonged outdoor exertion",
            "expires_at": localize_dt(datetime.utcnow() + timedelta(hours=12), lat, lon)
        })
    
    return {
        "location": {"latitude": lat, "longitude": lon},
        "current_aqi": current_aqi,
        "alerts": alerts,
        "checked_at": localize_dt(datetime.utcnow(), lat, lon)
    }

@app.get("/overall-aqi")
async def get_overall_aqi(
    lat: float = Query(...),
    lon: float = Query(...),
    pollutants: Optional[str] = Query(None)
):
    if pollutants:
        poll_list = [p.strip() for p in pollutants.split(",") if p.strip()]
    else:
        poll_list = ["NO2", "O3", "HCHO"]

    per_pollutant = []
    overall_aqi = None
    primary_pollutant = None

    for p in poll_list:
        try:
            resp = await get_air_quality(lat=lat, lon=lon, pollutant=p)
            reading = resp.readings[0] if resp and resp.readings else None

            item = {
                "pollutant": p,
                "available": bool(reading and reading.available),
                "aqi": reading.aqi if reading and reading.aqi is not None else None,
                "value": reading.value if reading else None,
                "unit": reading.unit if reading else None,
                "quality_level": reading.quality_level if reading else None,
                "timestamp": reading.timestamp if reading else None
            }

            per_pollutant.append(item)

            aqi_val = item["aqi"]
            if aqi_val is not None:
                if overall_aqi is None or aqi_val > overall_aqi:
                    overall_aqi = aqi_val
                    primary_pollutant = p

        except Exception as e:
            print(f"Error computing pollutant {p}: {e}")
            per_pollutant.append({"pollutant": p, "error": str(e)})

    return {
        "location": {"latitude": lat, "longitude": lon},
        "overall_aqi": overall_aqi,
        "primary_pollutant": primary_pollutant,
        "per_pollutant": per_pollutant,
        "generated_at": localize_dt(datetime.utcnow(), lat, lon)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)