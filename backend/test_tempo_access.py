"""
Script para verificar acceso a datos TEMPO de NASA
Ejecutar: python test_tempo_access.py
"""

from datetime import datetime, timedelta
import os

# Cargar .env manualmente
def load_env_file():
    """Carga variables desde .env sin dependencias externas"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        return True
    return False

def test_tempo_connection():
    """Prueba la conexión a TEMPO y muestra datasets disponibles"""
    
    print("=" * 60)
    print("TEST DE ACCESO A TEMPO")
    print("=" * 60)
    
    # Cargar variables de entorno
    print("\n0. Cargando credenciales desde .env...")
    if load_env_file():
        print("   ✓ Archivo .env encontrado")
    else:
        print("   ✗ Archivo .env no encontrado")
    
    nasa_user = os.getenv("NASA_USERNAME")
    nasa_pass = os.getenv("NASA_PASSWORD")
    
    if nasa_user:
        print(f"   ✓ NASA_USERNAME: {nasa_user}")
    else:
        print("   ✗ NASA_USERNAME no encontrado en .env")
    
    if nasa_pass:
        print(f"   ✓ NASA_PASSWORD: {'*' * len(nasa_pass)}")
    else:
        print("   ✗ NASA_PASSWORD no encontrado en .env")
    
    if not (nasa_user and nasa_pass):
        print("\n   ERROR: Asegúrate que tu .env contenga:")
        print("   NASA_USERNAME=tu_username")
        print("   NASA_PASSWORD=tu_password")
        return
    
    # Intentar importar earthaccess
    print("\n1. Importando earthaccess...")
    try:
        import earthaccess
        print("   ✓ earthaccess importado correctamente")
    except ImportError:
        print("   ✗ earthaccess no está instalado")
        print("   Instala con: pip install earthaccess")
        return
    
    # Autenticar
    print("\n2. Intentando autenticar con NASA Earthdata...")
    try:
        # Configurar variables de entorno para earthaccess
        os.environ["EARTHDATA_USERNAME"] = nasa_user
        os.environ["EARTHDATA_PASSWORD"] = nasa_pass
        
        auth = earthaccess.login(strategy="environment")
        print("   ✓ Autenticación exitosa")
    except Exception as e:
        print(f"   ✗ Error de autenticación: {e}")
        print("\n   Verifica que tus credenciales sean correctas en:")
        print("   https://urs.earthdata.nasa.gov/")
        return
    
    # Buscar datasets TEMPO disponibles
    print("\n3. Buscando datasets TEMPO disponibles...")
    try:
        datasets = earthaccess.search_datasets(keyword="TEMPO")
        
        if datasets:
            print(f"   ✓ Encontrados {len(datasets)} datasets TEMPO")
            print("\n   Primeros 10 datasets:")
            for i, ds in enumerate(datasets[:10], 1):
                short_name = ds.get('umm', {}).get('ShortName', 'N/A')
                title = ds.get('umm', {}).get('EntryTitle', 'N/A')
                print(f"\n   {i}. {short_name}")
                print(f"      {title[:70]}")
        else:
            print("   ⚠ No se encontraron datasets TEMPO")
            
    except Exception as e:
        print(f"   ✗ Error buscando datasets: {e}")
        return
    
    # Probar búsqueda de granulos para Ciudad de México
    print("\n4. Probando búsqueda de granulos...")
    
    test_locations = [
        ("Ciudad de México", 19.4326, -99.1332),
        ("Nueva York", 40.7128, -74.0060),
        ("Los Ángeles", 34.0522, -118.2437)
    ]
    
    # Buscar datos recientes (últimos 30 días)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Probar diferentes formatos de nombres
    possible_names = [
        "TEMPO_NO2_L2",
        "TEMPO_L2_NO2", 
        "TEMPO_NO2",
        "TEMPO-NO2-L2",
        "TEMPO_NO2_L3"
    ]
    
    for city, lat, lon in test_locations:
        print(f"\n   Probando: {city} ({lat}°N, {lon}°W)")
        
        found_data = False
        for dataset_name in possible_names:
            try:
                results = earthaccess.search_data(
                    short_name=dataset_name,
                    temporal=(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d")
                    ),
                    bounding_box=(lon - 1, lat - 1, lon + 1, lat + 1)
                )
                
                if results:
                    print(f"      ✓ {dataset_name}: {len(results)} granulos encontrados")
                    found_data = True
                    break
                    
            except Exception as e:
                continue
        
        if not found_data:
            print(f"      ✗ No se encontraron datos para ningún formato")
    
    # Información adicional
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print("\nCobertura de TEMPO:")
    print("  - Región: América del Norte")
    print("  - Latitud: ~18°N a 57°N")
    print("  - Longitud: ~126°W a 55°W")
    print("\nSi no se encontraron granulos:")
    print("  1. TEMPO es muy reciente (lanzado en 2023)")
    print("  2. Los datos pueden no estar disponibles aún")
    print("  3. Puede haber delays en procesamiento")
    print("\nAlternativa: Usar OpenAQ API (datos reales, sin autenticación)")
    print("  - Cobertura global")
    print("  - Datos de estaciones terrestres")
    print("  - API pública gratuita")
    print("=" * 60)

if __name__ == "__main__":
    test_tempo_connection()