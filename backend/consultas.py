"""
Script de prueba para verificar descarga y procesamiento de datos TEMPO
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("TEST COMPLETO DE DESCARGA Y PROCESAMIENTO TEMPO")
print("="*70)

# 1. Verificar credenciales
print("\n1. Verificando credenciales...")
username = os.getenv("NASA_USERNAME")
password = os.getenv("NASA_PASSWORD")

if username and password:
    print(f"   ✓ NASA_USERNAME: {username}")
    print(f"   ✓ NASA_PASSWORD: {'*' * len(password)}")
else:
    print("   ❌ Credenciales no encontradas en .env")
    exit(1)

# 2. Autenticar
print("\n2. Autenticando con NASA Earthdata...")
try:
    import earthaccess
    os.environ["EARTHDATA_USERNAME"] = username
    os.environ["EARTHDATA_PASSWORD"] = password
    auth = earthaccess.login(strategy="environment")
    print("   ✓ Autenticación exitosa")
except Exception as e:
    print(f"   ❌ Error de autenticación: {e}")
    exit(1)

# 3. Buscar granulos recientes
print("\n3. Buscando granulos TEMPO recientes...")

locations = [
    ("Ciudad de México", 19.4326, -99.1332),
    ("Nueva York", 40.7128, -74.0060),
    ("Los Ángeles", 34.0522, -118.2437),
]

datasets = ["TEMPO_NO2_L2", "TEMPO_HCHO_L2", "TEMPO_O3TOT_L2"]

end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\n   Período: {start_date.date()} a {end_date.date()}")

best_granule = None
best_location = None
best_dataset = None

for dataset in datasets:
    print(f"\n   📊 Dataset: {dataset}")
    
    for loc_name, lat, lon in locations:
        try:
            results = earthaccess.search_data(
                short_name=dataset,
                temporal=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
                bounding_box=(lon - 2, lat - 2, lon + 2, lat + 2)
            )
            
            count = len(results) if results else 0
            print(f"      {loc_name}: {count} granulos")
            
            if count > 0 and best_granule is None:
                best_granule = results[0]
                best_location = (loc_name, lat, lon)
                best_dataset = dataset
                
        except Exception as e:
            print(f"      {loc_name}: Error - {e}")

if not best_granule:
    print("\n   ❌ No se encontraron granulos en ninguna ubicación")
    print("\n   💡 POSIBLES RAZONES:")
    print("      - TEMPO es muy nuevo (lanzado en 2023)")
    print("      - Los datos pueden tener delay de procesamiento")
    print("      - La cobertura puede ser limitada")
    exit(1)

print(f"\n   ✓ Mejor resultado encontrado:")
print(f"      Dataset: {best_dataset}")
print(f"      Ubicación: {best_location[0]}")
print(f"      Coordenadas: ({best_location[1]}, {best_location[2]})")

# 4. Descargar y procesar
print(f"\n4. Descargando y procesando archivo TEMPO...")
try:
    import tempfile
    import xarray as xr
    import numpy as np
    
    temp_dir = tempfile.mkdtemp()
    print(f"   📁 Directorio temporal: {temp_dir}")
    
    print(f"   📥 Descargando...")
    downloaded = earthaccess.download(best_granule, temp_dir)
    
    if not downloaded:
        print("   ❌ Descarga falló")
        exit(1)
    
    file_path = downloaded[0]
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    print(f"   ✓ Descargado: {os.path.basename(file_path)}")
    print(f"   ✓ Tamaño: {file_size:.2f} MB")
    
    # Abrir con NetCDF4 primero para ver la estructura
    print(f"\n5. Analizando estructura del archivo NetCDF...")
    from netCDF4 import Dataset
    
    nc = Dataset(file_path, 'r')
    print(f"   ✓ Archivo NetCDF abierto")
    
    print(f"\n   📊 GRUPOS EN EL ARCHIVO:")
    print(f"   {'─'*60}")
    
    def print_groups(group, indent=0):
        for group_name in group.groups:
            print(f"   {'  '*indent}📁 {group_name}/")
            subgroup = group.groups[group_name]
            if subgroup.variables:
                for var_name in list(subgroup.variables.keys())[:5]:
                    var = subgroup.variables[var_name]
                    print(f"   {'  '*(indent+1)}└─ {var_name}: {var.shape} ({var.dtype})")
            print_groups(subgroup, indent + 1)
    
    print_groups(nc)
    
    # Buscar grupos comunes en TEMPO L2
    target_groups = ['product', 'geolocation', 'support_data']
    
    print(f"\n6. Buscando datos en grupos estándar...")
    
    product_group = None
    geo_group = None
    
    for group_name in nc.groups:
        print(f"   Explorando grupo: {group_name}")
        group = nc.groups[group_name]
        
        if 'product' in group_name.lower():
            product_group = group
            print(f"   ✓ Grupo de producto encontrado: {group_name}")
            print(f"      Variables: {list(group.variables.keys())[:10]}")
        
        if 'geo' in group_name.lower():
            geo_group = group
            print(f"   ✓ Grupo de geolocalización encontrado: {group_name}")
            print(f"      Variables: {list(group.variables.keys())[:10]}")
    
    nc.close()
    
    # Ahora intentar procesar con NetCDF4 directamente
    print(f"\n7. Procesando datos para Ciudad de México...")
    
    try:
        # Reabrir archivo
        nc = Dataset(file_path, 'r')
        
        product = nc.groups['product']
        geolocation = nc.groups['geolocation']
        
        # Obtener datos
        data = product.variables['vertical_column_troposphere'][:]
        lats = geolocation.variables['latitude'][:]
        lons = geolocation.variables['longitude'][:]
        
        # Encontrar punto más cercano
        lat, lon = best_location[1], best_location[2]
        distances = np.sqrt((lats - lat)**2 + (lons - lon)**2)
        min_idx = np.unravel_index(distances.argmin(), distances.shape)
        
        value = float(data[min_idx])
        
        print(f"   ✓ Índices encontrados: {min_idx}")
        print(f"   ✓ Valor extraído: {value:.6e}")
        
        # Obtener unidades
        if hasattr(product.variables['vertical_column_troposphere'], 'units'):
            units = product.variables['vertical_column_troposphere'].units
            print(f"   ✓ Unidades: {units}")
        
        # Convertir a ppb (aproximado)
        ppb_value = abs(value) * 5e-16
        print(f"   ✓ Valor en ppb (aprox): {ppb_value:.2f}")
        
        nc.close()
        
        print(f"\n   {'─'*60}")
        print(f"   ✅ ÉXITO: Datos procesados correctamente")
        print(f"   {'─'*60}")
        
    except Exception as e:
        print(f"   ⚠️ Error procesando: {e}")
        import traceback
        traceback.print_exc()
    
    # Limpiar
    print(f"\n8. Limpiando archivos temporales...")
    try:
        os.remove(file_path)
        os.rmdir(temp_dir)
        print(f"   ✓ Archivos temporales eliminados")
    except:
        print(f"   ⚠️ No se pudieron eliminar archivos temporales")
    
except Exception as e:
    print(f"\n   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST COMPLETADO")
print("="*70)

print("\n💡 CONCLUSIONES:")
print("   Si este test fue exitoso, la API debería funcionar correctamente.")
print("   Si falló, revisa:")
print("      1. Credenciales NASA Earthdata")
print("      2. Aplicaciones autorizadas en tu perfil NASA")
print("      3. Conectividad a internet")
print("      4. Estructura de los archivos TEMPO (pueden cambiar)")

print("\n🚀 SIGUIENTE PASO:")
print("   Inicia la API con: python main.py")
print("   Y prueba una consulta a: http://localhost:8000/air-quality?lat=40.7128&lon=-74.0060&pollutant=NO2")
print()