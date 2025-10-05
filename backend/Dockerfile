# Imagen base de Python
FROM python:3.12-slim

# Instalar dependencias del sistema necesarias para NetCDF4 y otros paquetes
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libhdf5-dev \
    libnetcdf-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Crear el directorio de trabajo
WORKDIR /app

# Evitar logs bufferizados
ENV PYTHONUNBUFFERED=1

# Actualizar pip y setuptools primero
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copiar e instalar dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . /app

# Exponer puerto 8000
EXPOSE 8000

# Ejecutar el servidor FastAPI
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]