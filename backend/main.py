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
    allow_origins=["http://localhost:3000"],
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

# Variables globales
earth_auth = None
auth_initialized = False
tz_finder = TimezoneFinder()


def get_timezone_name(lat: float, lon: float) -> Optional[str]:
    """Obtiene el nombre de la zona horaria para coordenadas dadas."""
    try:
        return tz_finder.timezone_at(lat=lat, lng=lon)
    except Exception:
        return None


def localize_dt(dt: datetime, lat: float, lon: float) -> str:
    """Retorna timestamp ISO localizado a la zona horaria de (lat, lon).

    Los datetime naive se asumen como UTC para propósitos de conversión.
    Si no se encuentra zona horaria, regresa ISO sin info de tz.
    """
    try:
        tzname = get_timezone_name(lat, lon)
        if not tzname:
            return dt.isoformat()

        # Asegurar que dt es timezone-aware en UTC, luego convertir
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)

        local = dt_utc.astimezone(ZoneInfo(tzname))
        return local.isoformat()
    except Exception:
        return dt.isoformat()


def is_in_north_america(lat: float, lon: float) -> bool:
    """Verifica si las coordenadas están dentro de Norteamérica.
    
    Límites aproximados de cobertura TEMPO:
    - Latitud: 7°N a 83°N
    - Longitud: 168°W a 52°W
    """
    return (7 <= lat <= 83) and (-168 <= lon <= -52)


def calculate_aqi(pollutant: str, value: float) -> tuple:
    """Calcula el Índice de Calidad del Aire (AQI)."""
    if value is None or np.isnan(value):
        return None, "No disponible"
    
    if pollutant == "NO2":
        # NO2 en ppb a AQI
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
        # O3: TEMPO reporta en DU (Dobson Units)
        # Convertir a ppb para cálculo de AQI (1 DU ≈ 0.3 ppb aproximadamente)
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
        # HCHO en ppb a AQI
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
        # Genérico
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
    """Convierte moléculas/cm² a ppb."""
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
    """Procesa archivo NetCDF de TEMPO."""
    try:
        from netCDF4 import Dataset
        
        print(f"Abriendo archivo: {file_path}")
        
        nc = Dataset(file_path, 'r')
        
        if 'product' not in nc.groups or 'geolocation' not in nc.groups:
            print(f"Grupos necesarios no encontrados")
            nc.close()
            return None
        
        product = nc.groups['product']
        geolocation = nc.groups['geolocation']
        
        print(f"Grupos encontrados: product, geolocation")
        
        # Candidatos de nombres de variables por contaminante
        candidates = {
            "NO2": ["vertical_column_troposphere", "tropospheric_column", "NO2_column"],
            "HCHO": ["vertical_column_troposphere", "formaldehyde_column", "HCHO_column"],
            "O3": ["vertical_column_total", "ozone_column", "O3_total", "O3_column", "step2_o3", "step1_o3"]
        }

        var_candidates = candidates.get(pollutant, [])

        # Para O3, verificar tanto product como support_data
        data_group = product
        if pollutant == "O3" and 'support_data' in nc.groups:
            data_group = nc.groups['support_data']

        # Listar variables disponibles para diagnóstico
        vars_available = list(data_group.variables.keys())

        var_name = None
        for cand in var_candidates:
            if cand in data_group.variables:
                var_name = cand
                break

        if not var_name:
            print(f"Variable esperada no encontrada. Variables disponibles: {vars_available}")
            nc.close()
            return {"diagnostic": True, "variables_available": vars_available}

        print(f"Variable encontrada: {var_name}")

        data = data_group.variables[var_name][:]
        lats = geolocation.variables['latitude'][:]
        lons = geolocation.variables['longitude'][:]
        
        print(f"Datos cargados - Shape: {data.shape}")
        
        # Encontrar punto más cercano
        distances = np.sqrt((lats - lat)**2 + (lons - lon)**2)
        min_idx = np.unravel_index(distances.argmin(), distances.shape)
        
        value = float(data[min_idx])

        nc.close()

        # Validar valor
        if np.isnan(value) or value < -9e30 or value > 1e30:
            print(f"Valor inválido: {value}")
            return None

        print(f"Valor extraído: {value:.6e}")

        # Conversión según contaminante
        if pollutant in ["NO2", "HCHO"]:
            ppb_value = convert_molecules_to_ppb(value, pollutant)
            return {"value": ppb_value, "variable_used": var_name}
        elif pollutant == "O3":
            # O3 está típicamente en Dobson Units (DU), no necesita conversión
            return {"value": abs(value) if value else None, "variable_used": var_name}

        return None
        
    except Exception as e:
        print(f"Error procesando NetCDF: {e}")
        traceback.print_exc()
        return None


def ensure_authentication():
    """Asegura que la autenticación esté activa."""
    global earth_auth, auth_initialized
    
    if auth_initialized and earth_auth:
        return earth_auth
    
    try:
        import earthaccess
        
        username = os.getenv("NASA_USERNAME")
        password = os.getenv("NASA_PASSWORD")
        
        if not (username and password):
            print("Credenciales no encontradas")
            return None
        
        # Forzar re-autenticación
        os.environ["EARTHDATA_USERNAME"] = username
        os.environ["EARTHDATA_PASSWORD"] = password
        
        # Usar persist=True para guardar credenciales
        earth_auth = earthaccess.login(strategy="environment", persist=True)
        auth_initialized = True
        
        print(f"Autenticación completada: {username}")
        return earth_auth
        
    except Exception as e:
        print(f"Error de autenticación: {e}")
        auth_initialized = False
        return None


def process_tempo_data(granules, lat: float, lon: float, pollutant: str):
    """Descarga y procesa granulos de TEMPO."""
    try:
        if not granules:
            return None
        
        import earthaccess
        
        # Re-autenticar antes de descargar
        auth = ensure_authentication()
        if not auth:
            print("No se pudo autenticar")
            return None
        
        print(f"Intentando descargar {len(granules)} granulos...")

        variables_seen = set()
        for i, granule in enumerate(granules[:3]):
            try:
                print(f"\nProcesando granulo {i+1}/{min(3, len(granules))}...")

                temp_dir = tempfile.mkdtemp()
                
                # Descargar con el objeto de auth
                downloaded = earthaccess.download(granule, temp_dir)
                
                if not downloaded:
                    print(f"No se pudo descargar granulo {i+1}")
                    continue
                
                file_path = downloaded[0]
                print(f"Archivo descargado: {os.path.basename(file_path)}")
                
                value = process_tempo_netcdf(file_path, lat, lon, pollutant)
                
                try:
                    os.remove(file_path)
                    os.rmdir(temp_dir)
                except:
                    pass
                
                if value is not None:
                    # Si retorna objeto con info de diagnóstico
                    if isinstance(value, dict) and value.get("diagnostic"):
                        vars_av = value.get('variables_available') or []
                        print(f"Diagnóstico NetCDF: variables disponibles: {vars_av}")
                        for v in vars_av:
                            variables_seen.add(v)
                        continue

                    # Caso normal: dict con value y variable_used
                    if isinstance(value, dict) and "value" in value:
                        print(f"Datos procesados exitosamente: {value['value']}")
                        return value

                    # Valor numérico legacy
                    print(f"Datos procesados exitosamente: {value}")
                    return value
                else:
                    print(f"No se pudo extraer valor del granulo {i+1}")
                    
            except Exception as e:
                print(f"Error con granulo {i+1}: {e}")
                continue
        
        if variables_seen:
            return {"diagnostic": True, "variables_available": sorted(list(variables_seen))}

        print(f"No se pudo procesar ningún granulo")
        return None
        
    except Exception as e:
        print(f"Error general procesando datos TEMPO: {e}")
        traceback.print_exc()
        return None


@app.on_event("startup")
async def startup_event():
    """Inicializa autenticación NASA Earthdata."""
    global earth_auth, auth_initialized
    
    auth = ensure_authentication()
    
    if auth:
        print("TEMPO data source: ACTIVE")
    else:
        print("API funcionará en modo solo consulta")


@app.get("/")
async def root():
    return {
        "message": "TEMPO Air Quality API",
        "status": "live_data" if earth_auth else "read_only",
        "coverage": "North America (7°N to 83°N, 168°W to 52°W)",
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
    """Obtiene datos de calidad del aire del satélite TEMPO."""
    
    # Verificar que está dentro de Norteamérica
    if not is_in_north_america(lat, lon):
        raise HTTPException(
            status_code=400,
            detail="La ubicación debe estar dentro de Norteamérica (cobertura TEMPO: 7°N-83°N, 168°W-52°W)"
        )
    
    print(f"\n{'='*60}")
    print(f"Consulta: {pollutant} en ({lat}, {lon})")
    print(f"{'='*60}")
    
    dataset_map = {
        "NO2": "TEMPO_NO2_L2",
        "O3": "TEMPO_O3TOT_L2",
        "HCHO": "TEMPO_HCHO_L2"
    }
    
    dataset_name = dataset_map.get(pollutant)
    granules_count = 0
    
    if not dataset_name:
        # Obtener hora local para el timestamp
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
    
    # Re-autenticar antes de buscar
    auth = ensure_authentication()
    
    if auth:
        try:
            import earthaccess
            
            # Usar hora actual UTC o fecha especificada
            if date:
                query_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                query_date = datetime.utcnow()
            
            # Buscar datos de los últimos 7 días
            start_date = query_date - timedelta(days=7)
            end_date = query_date
            
            print(f"Buscando datos desde {start_date.date()} hasta {end_date.date()}")
            
            results = earthaccess.search_data(
                short_name=dataset_name,
                temporal=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
                bounding_box=(lon - 2.0, lat - 2.0, lon + 2.0, lat + 2.0)
            )

            granules_count = len(results) if results else 0
            print(f"Granulos encontrados: {granules_count}")

            if results and granules_count > 0:
                print(f"Encontrados {granules_count} archivos TEMPO")
                
                value = process_tempo_data(results, lat, lon, pollutant)
                
                processed_value = None
                variable_used = None

                if value is not None:
                    if isinstance(value, dict) and "value" in value:
                        processed_value = value["value"]
                        variable_used = value.get("variable_used")
                    elif isinstance(value, (int, float)):
                        processed_value = value

                if processed_value is not None and not np.isnan(processed_value):
                    aqi, quality_level = calculate_aqi(pollutant, processed_value)
                    
                    unit = "ppb" if pollutant in ["NO2", "HCHO"] else "DU"
                    
                    # Timestamp localizado a la zona horaria del lugar
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
                    
                    print(f"ÉXITO: Datos procesados correctamente (variable_used={variable_used})")
                    print(f"{'='*60}\n")
                    
                    location_meta = {
                        "latitude": lat,
                        "longitude": lon,
                        "data_source": "tempo_satellite",
                        "granules_processed": granules_count
                    }
                    if variable_used:
                        location_meta["variable_used"] = variable_used

                    return AirQualityResponse(
                        location=location_meta,
                        readings=[reading]
                    )
                else:
                    print(f"No se pudo extraer valor válido de los granulos")
            else:
                print(f"No se encontraron granulos TEMPO para esta ubicación/fecha")
                
        except Exception as e:
            print(f"Error fetching TEMPO data: {e}")
            traceback.print_exc()
    
    print(f"Datos no disponibles")
    print(f"{'='*60}\n")
    
    # Timestamp localizado
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
    """Pronóstico de 24 horas con timestamps localizados."""
    base_time = datetime.utcnow()
    forecast_data = []
    
    for i in range(hours):
        forecast_time = base_time + timedelta(hours=i)
        hour = forecast_time.hour
        
        # Simulación de AQI
        base_aqi = 45 + 25 * np.sin((hour - 6) * np.pi / 12)
        aqi = int(max(20, base_aqi + np.random.normal(0, 8)))
        
        if aqi <= 50:
            level = "Good"
        elif aqi <= 100:
            level = "Moderate"
        else:
            level = "Unhealthy for Sensitive Groups"
        
        primary = "O3" if 10 <= hour <= 18 else "NO2"
        
        forecast_data.append({
            "timestamp": localize_dt(forecast_time, lat, lon),
            "hour": i,
            "aqi": aqi,
            "quality_level": level,
            "primary_pollutant": primary
        })
    
    return {
        "location": {"latitude": lat, "longitude": lon},
        "generated_at": localize_dt(base_time, lat, lon),
        "forecast": forecast_data
    }


@app.get("/alerts")
async def get_air_quality_alerts(
    lat: float = Query(...),
    lon: float = Query(...)
):
    """Alertas de calidad del aire con timestamps localizados."""
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
    """Calcula AQI general consultando por cada contaminante y tomando el máximo.

    pollutants: lista opcional separada por comas como "NO2,O3,HCHO". 
    Si no se provee, se usan valores por defecto.
    """
    # Lista de contaminantes por defecto
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