from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List
import earthaccess
import numpy as np
from pydantic import BaseModel
import os

app = FastAPI(title="TEMPO Air Quality API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Models
class AirQualityReading(BaseModel):
    pollutant: str
    value: float
    unit: str
    timestamp: str
    latitude: float
    longitude: float
    aqi: Optional[int] = None
    quality_level: Optional[str] = None

class AirQualityResponse(BaseModel):
    location: dict
    readings: List[AirQualityReading]
    forecast: Optional[List[dict]] = None

# Initialize earthaccess (will need NASA Earthdata credentials)
# Users need to register at: https://urs.earthdata.nasa.gov/
earth_auth = None

def calculate_aqi(pollutant: str, value: float) -> tuple:
    """
    Calculate Air Quality Index based on pollutant concentration
    Returns (AQI value, quality level)
    """
    # Simplified AQI calculation - NO2 example (ppb)
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
    
    # Simplified O3 calculation (ppb, 8-hour average)
    elif pollutant == "O3":
        if value <= 54:
            aqi = value * 50 / 54
            level = "Good"
        elif value <= 70:
            aqi = 50 + (value - 54) * 50 / 16
            level = "Moderate"
        elif value <= 85:
            aqi = 100 + (value - 70) * 50 / 15
            level = "Unhealthy for Sensitive Groups"
        elif value <= 105:
            aqi = 150 + (value - 85) * 50 / 20
            level = "Unhealthy"
        else:
            aqi = 200 + (value - 105) * 100 / 95
            level = "Very Unhealthy"
    else:
        aqi = None
        level = "Unknown"
    
    return int(aqi) if aqi else None, level

@app.on_event("startup")
async def startup_event():
    """Initialize NASA Earthdata authentication on startup"""
    global earth_auth
    try:
        # Option 1: Use environment variables
        # Set NASA_USERNAME and NASA_PASSWORD in your environment
        username = os.getenv("NASA_USERNAME")
        password = os.getenv("NASA_PASSWORD")
        
        if username and password:
            earth_auth = earthaccess.login(strategy="environment")
        else:
            # Option 2: Use netrc file (~/.netrc)
            earth_auth = earthaccess.login(strategy="netrc")
            
        print("✓ NASA Earthdata authentication successful")
    except Exception as e:
        print(f"⚠ NASA Earthdata authentication failed: {e}")
        print("You'll need to set up credentials to access TEMPO data")

@app.get("/")
async def root():
    return {
        "message": "TEMPO Air Quality API",
        "endpoints": {
            "/air-quality": "Get air quality data for a location",
            "/pollutants": "List available pollutants",
            "/health": "Check API health and NASA connection"
        }
    }

@app.get("/health")
async def health_check():
    """Check API and NASA Earthdata connection status"""
    nasa_connected = earth_auth is not None
    return {
        "status": "healthy",
        "nasa_earthdata_connected": nasa_connected,
        "message": "Set NASA_USERNAME and NASA_PASSWORD env vars" if not nasa_connected else "Ready"
    }

@app.get("/pollutants")
async def get_pollutants():
    """List pollutants monitored by TEMPO"""
    return {
        "pollutants": [
            {
                "name": "NO2",
                "full_name": "Nitrogen Dioxide",
                "unit": "molecules/cm²",
                "sources": ["vehicles", "power plants", "industrial"],
                "health_effects": "Respiratory irritation, asthma"
            },
            {
                "name": "O3",
                "full_name": "Ozone",
                "unit": "Dobson Units",
                "sources": ["photochemical reactions"],
                "health_effects": "Lung damage, respiratory issues"
            },
            {
                "name": "HCHO",
                "full_name": "Formaldehyde",
                "unit": "molecules/cm²",
                "sources": ["industrial emissions", "wildfires"],
                "health_effects": "Eye/throat irritation, cancer risk"
            },
            {
                "name": "SO2",
                "full_name": "Sulfur Dioxide",
                "unit": "molecules/cm²",
                "sources": ["coal combustion", "volcanic activity"],
                "health_effects": "Respiratory problems"
            }
        ]
    }

@app.get("/air-quality", response_model=AirQualityResponse)
async def get_air_quality(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
    pollutant: Optional[str] = Query("NO2", description="Pollutant type (NO2, O3, HCHO, SO2)")
):
    """
    Get air quality data for a specific location
    
    Example: /air-quality?lat=14.6349&lon=-90.5069&pollutant=NO2
    (Guatemala City coordinates)
    """
    
    if not earth_auth:
        raise HTTPException(
            status_code=503,
            detail="NASA Earthdata not configured. Set NASA_USERNAME and NASA_PASSWORD environment variables."
        )
    
    # Parse date
    if date:
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        query_date = datetime.now()
    
    try:
        # Search for TEMPO data
        # TEMPO short name varies by product: TEMPO_NO2_L2, TEMPO_O3_L2, etc.
        results = earthaccess.search_data(
            short_name=f"TEMPO_{pollutant}_L2",
            temporal=(
                query_date.strftime("%Y-%m-%d"),
                (query_date + timedelta(days=1)).strftime("%Y-%m-%d")
            ),
            bounding_box=(lon - 0.5, lat - 0.5, lon + 0.5, lat + 0.5)
        )
        
        if not results:
            # Return mock data for demonstration if no real data available
            mock_value = np.random.uniform(20, 80)  # Mock NO2 value in ppb
            aqi, level = calculate_aqi(pollutant, mock_value)
            
            return AirQualityResponse(
                location={"latitude": lat, "longitude": lon},
                readings=[
                    AirQualityReading(
                        pollutant=pollutant,
                        value=mock_value,
                        unit="ppb" if pollutant in ["NO2", "O3"] else "molecules/cm²",
                        timestamp=query_date.isoformat(),
                        latitude=lat,
                        longitude=lon,
                        aqi=aqi,
                        quality_level=level
                    )
                ],
                forecast=[
                    {
                        "time": (query_date + timedelta(hours=i)).isoformat(),
                        "aqi": int(np.random.uniform(50, 150)),
                        "level": "Moderate"
                    }
                    for i in range(1, 25)
                ]
            )
        
        # Process real TEMPO data
        readings = []
        for granule in results[:5]:  # Limit to 5 most recent
            # Download and process the data
            # Note: This is simplified - actual processing requires reading NetCDF files
            readings.append(
                AirQualityReading(
                    pollutant=pollutant,
                    value=0.0,  # Extract from actual data
                    unit="molecules/cm²",
                    timestamp=query_date.isoformat(),
                    latitude=lat,
                    longitude=lon
                )
            )
        
        return AirQualityResponse(
            location={"latitude": lat, "longitude": lon},
            readings=readings
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching TEMPO data: {str(e)}")

@app.get("/forecast")
async def get_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    hours: int = Query(24, description="Forecast hours", ge=1, le=72)
):
    """
    Get air quality forecast for the next N hours
    (This would integrate with weather models in production)
    """
    
    base_time = datetime.now()
    forecast_data = []
    
    for i in range(hours):
        # In production: integrate weather data, ML models, etc.
        forecast_time = base_time + timedelta(hours=i)
        base_aqi = 50 + 30 * np.sin(i / 12 * np.pi)  # Mock diurnal pattern
        
        forecast_data.append({
            "timestamp": forecast_time.isoformat(),
            "hour": i,
            "aqi": int(base_aqi + np.random.normal(0, 10)),
            "quality_level": "Good" if base_aqi < 50 else "Moderate",
            "primary_pollutant": "O3" if 10 <= forecast_time.hour <= 18 else "NO2"
        })
    
    return {
        "location": {"latitude": lat, "longitude": lon},
        "generated_at": base_time.isoformat(),
        "forecast": forecast_data
    }

@app.get("/alerts")
async def get_air_quality_alerts(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get air quality alerts for a location
    """
    
    # Mock alert system - in production, check against thresholds
    current_aqi = np.random.randint(50, 150)
    
    alerts = []
    if current_aqi > 100:
        alerts.append({
            "level": "warning",
            "message": "Air quality is unhealthy for sensitive groups",
            "recommendation": "People with respiratory conditions should limit outdoor activities",
            "expires_at": (datetime.now() + timedelta(hours=6)).isoformat()
        })
    
    if current_aqi > 150:
        alerts.append({
            "level": "alert",
            "message": "Air quality is unhealthy",
            "recommendation": "Everyone should reduce prolonged outdoor exertion",
            "expires_at": (datetime.now() + timedelta(hours=12)).isoformat()
        })
    
    return {
        "location": {"latitude": lat, "longitude": lon},
        "current_aqi": current_aqi,
        "alerts": alerts,
        "checked_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)