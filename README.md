<h1 align="center">Apollo-5C-NASA-Hackathon</h1>


<p align="center">
<img width="400" height="588" alt="nasa" src="https://github.com/user-attachments/assets/55f5bb1f-e11c-4a2c-a1e6-d5ba03d60f46" />
</p>


# 🌎 TEMPO Air Quality Forecasting App

NASA’s **Tropospheric Emissions: Monitoring of Pollution (TEMPO)** mission is transforming air quality observation across North America.  
Our project integrates **real-time TEMPO satellite data** with **ground-based sensors** and **weather data** to forecast air quality and help communities make healthier decisions.

---

## 🚀 Project Overview

The **TEMPO Air Quality App** provides:
- 🌤️ **Real-time air quality data** from NASA’s TEMPO mission.
- 📈 **Forecasts and alerts** to help users plan their day.
- 💡 **Data-driven insights** to improve public health decisions.
- ☁️ **Seamless scaling** between local and cloud systems using **Docker + FastAPI + React**.

The app automatically retrieves pollutant data (NO₂, O₃, HCHO, SO₂), calculates the Air Quality Index (AQI), and generates hourly forecasts using a hybrid data model.

---

## 🛰️ How It Works

1. **NASA Earthdata Connection**  
   The backend authenticates with NASA’s Earthdata API via the `earthaccess` library.  
   You’ll need to register at [https://urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov).

2. **Data Retrieval**  
   FastAPI queries TEMPO Level 2 products (e.g., `TEMPO_NO2_L2`) using latitude, longitude, and date.

3. **Air Quality Index (AQI) Calculation**  
   AQI is computed for pollutants (NO₂, O₃, etc.) using simplified U.S. EPA formulas.

4. **Forecast Generation**  
   The system generates a short-term forecast (1–72 hours) with modeled air quality variations.

5. **React Frontend Visualization**  
   The React dashboard displays AQI levels, forecasts, and alerts for each region.

---

## ⚙️ Tech Stack

- **Frontend:** React + Vite  
- **Backend:** FastAPI (Python 3.12)  
- **Data Source:** NASA TEMPO Mission via Earthaccess  
- **Containerization:** Docker & Docker Compose  
- **Mock Data:** Numpy (when no live data is available)  
- **Deployment Ready:** Cloud-compatible (AWS, GCP, Azure, or local)

---

## 🧩 Features

| Feature | Description |
|----------|--------------|
| 🌍 **/air-quality** | Retrieve air quality data by latitude/longitude |
| 📡 **/forecast** | Get hourly AQI predictions (up to 72 hours) |
| ⚠️ **/alerts** | Receive health warnings based on AQI thresholds |
| 🧬 **/pollutants** | List monitored pollutants and health effects |
| 💚 **/health** | Check NASA Earthdata connection and API status |

---

## 🐳 Running the App with Docker

### 1. Clone the repository
```bash
git clone https://github.com/<your-org>/tempo-air-quality.git
cd tempo-air-quality
```

### 2. Create your `.env` file
```
NASA_USERNAME=your_nasa_username
NASA_PASSWORD=your_nasa_password
```

### 3. Build and start containers
```bash
docker-compose up --build
```

### 4. Access the app
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)

---



## 👥 Team

**Team: Apollo5c**  
Created for the **NASA International Space Apps Challenge** 🛰️  

---



🛰️ *"Improving air quality awareness, one pixel at a time."*

