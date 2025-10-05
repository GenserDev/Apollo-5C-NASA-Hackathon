// Dashboard.jsx - Página de monitoreo de calidad del aire
import { useState, useEffect } from 'react';
import { Cloud, Wind, AlertTriangle, TrendingUp, MapPin, Clock, Activity, Eye, Droplets, ThermometerSun, Search, XCircle, Loader } from 'lucide-react';
import TopBar from '../components/TopBar';
import '../styles/Dashboard.css';

export default function Dashboard() {
  const [location, setLocation] = useState(null); // Iniciar sin ubicación
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [currentData, setCurrentData] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [pollutants, setPollutants] = useState([]);
  const [overallAQI, setOverallAQI] = useState(null);
  const [pollutantData, setPollutantData] = useState({});
  const [selectedPollutant, setSelectedPollutant] = useState('NO2');
  const [pollutantLoading, setPollutantLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [dataSource, setDataSource] = useState('');
  const [dataAvailable, setDataAvailable] = useState(true);
  const [localTime, setLocalTime] = useState(new Date());

  const API_BASE = 'http://localhost:8000';

  // Load Spline script for initial view
  useEffect(() => {
    const script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://unpkg.com/@splinetool/viewer@1.10.74/build/spline-viewer.js';
    document.head.appendChild(script);

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, []);

  // Fetch all pollutants data
  const fetchAllPollutantsData = async () => {
    const pollutantList = ['NO2', 'O3', 'HCHO'];
    const data = {};
    
    for (const p of pollutantList) {
      try {
        const response = await fetch(`${API_BASE}/air-quality?lat=${location.lat}&lon=${location.lon}&pollutant=${p}`);
        if (response.ok) {
          const result = await response.json();
          const reading = result.readings[0];
          data[p] = {
            value: reading.value,
            unit: reading.unit,
            aqi: reading.aqi,
            quality_level: reading.quality_level,
            available: reading.available,
            timestamp: reading.timestamp
          };
        }
      } catch (error) {
        console.error(`Error fetching ${p}:`, error);
        data[p] = { available: false };
      }
    }
    
    setPollutantData(data);
  };

  // Fetch all data when location changes
  useEffect(() => {
    if (location) {
      fetchAllData();
      const interval = setInterval(fetchAllData, 300000);
      return () => clearInterval(interval);
    }
  }, [location]);

  // Fetch selected pollutant data when it changes
  useEffect(() => {
    if (selectedPollutant && location) {
      fetchSelectedPollutantData();
    }
  }, [selectedPollutant]);

  // Update local time every second
  useEffect(() => {
    if (!location) return;
    
    const updateLocalTime = () => {
      const timezoneOffset = Math.round(location.lon / 15);
      const now = new Date();
      const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
      const localDate = new Date(utc + (3600000 * timezoneOffset));
      setLocalTime(localDate);
    };

    updateLocalTime();
    const interval = setInterval(updateLocalTime, 1000);
    return () => clearInterval(interval);
  }, [location]);

  const fetchSelectedPollutantData = async () => {
    setPollutantLoading(true);
    try {
      const response = await fetch(`${API_BASE}/air-quality?lat=${location.lat}&lon=${location.lon}&pollutant=${selectedPollutant}`);
      if (response.ok) {
        const airQuality = await response.json();
        const reading = airQuality.readings[0];
        
        if (reading.available) {
          setCurrentData(reading);
          setDataAvailable(true);
        } else {
          setCurrentData(null);
          setDataAvailable(false);
        }
        
        setDataSource(airQuality.location.data_source);
        
        setPollutantData(prev => ({
          ...prev,
          [selectedPollutant]: {
            value: reading.value,
            unit: reading.unit,
            aqi: reading.aqi,
            quality_level: reading.quality_level,
            available: reading.available,
            timestamp: reading.timestamp
          }
        }));
      }
    } catch (error) {
      console.error("Error fetching pollutant data:", error);
      setCurrentData(null);
      setDataAvailable(false);
    }
    setPollutantLoading(false);
  };

  const searchLocation = async (query) => {
    if (query.length < 3) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`
      );
      const data = await response.json();
      setSearchResults(data);
      setShowResults(true);
    } catch (error) {
      console.error('Error searching location:', error);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    searchLocation(query);
  };

  const selectLocation = (result) => {
    setLocation({
      lat: parseFloat(result.lat),
      lon: parseFloat(result.lon),
      name: result.display_name.split(',')[0],
      fullName: result.display_name
    });
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
  };

  const handleSelectPollutant = (pollutantName) => {
    setSelectedPollutant(pollutantName);
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          
          try {
            const response = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
            );
            const data = await response.json();
            
            setLocation({
              lat: lat,
              lon: lon,
              name: data.address.city || data.address.town || data.address.village || 'Tu ubicación'
            });
          } catch (error) {
            setLocation({
              lat: lat,
              lon: lon,
              name: 'Tu ubicación'
            });
          }
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('No se pudo obtener tu ubicación. Verifica los permisos del navegador.');
          setLoading(false);
        }
      );
    } else {
      alert('Geolocalización no soportada en este navegador');
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [airQuality, forecastData, alertsData, pollutantsData, overallData] = await Promise.all([
        fetch(`${API_BASE}/air-quality?lat=${location.lat}&lon=${location.lon}&pollutant=${selectedPollutant}`)
          .then(async r => {
            if (!r.ok) {
              const err = await r.json();
              throw new Error(err.detail || "Error cargando calidad del aire");
            }
            return r.json();
          }),
        fetch(`${API_BASE}/forecast?lat=${location.lat}&lon=${location.lon}&hours=24`).then(r => r.json()),
        fetch(`${API_BASE}/alerts?lat=${location.lat}&lon=${location.lon}`).then(r => r.json()),
        fetch(`${API_BASE}/pollutants`).then(r => r.json()),
        fetch(`${API_BASE}/overall-aqi?lat=${location.lat}&lon=${location.lon}`).then(r => r.json())
      ]);

      const reading = airQuality.readings[0];
      
      if (reading.available) {
        setCurrentData(reading);
        setDataAvailable(true);
      } else {
        setCurrentData(null);
        setDataAvailable(false);
      }
      
      setDataSource(airQuality.location.data_source);
      setForecast(forecastData.forecast);
      setAlerts(alertsData.alerts);
      setOverallAQI(overallData.overall_aqi);
      setPollutants(pollutantsData.pollutants);
      setLastUpdate(new Date());
      
      await fetchAllPollutantsData();
      
    } catch (error) {
      console.error("Error fetching data:", error.message);
      setCurrentData(null);
      setDataAvailable(false);
    }
    setLoading(false);
  };

  const getAQIColor = (aqi) => {
    if (aqi <= 50) return 'aqi-good';
    if (aqi <= 100) return 'aqi-moderate';
    if (aqi <= 150) return 'aqi-unhealthy-sensitive';
    if (aqi <= 200) return 'aqi-unhealthy';
    return 'aqi-very-unhealthy';
  };

  const getHealthRecommendation = (level) => {
    const recommendations = {
      'Good': 'La calidad del aire es satisfactoria. ¡Disfruta las actividades al aire libre!',
      'Moderate': 'La calidad del aire es aceptable. Las personas inusualmente sensibles deben considerar limitar el ejercicio prolongado.',
      'Unhealthy for Sensitive Groups': 'Los grupos sensibles deben reducir el ejercicio prolongado al aire libre.',
      'Unhealthy': 'Todos deben reducir el ejercicio prolongado al aire libre.',
      'Very Unhealthy': 'Evita las actividades al aire libre. Mantén las ventanas cerradas.',
      'Hazardous': 'Todos deben evitar cualquier actividad al aire libre.'
    };
    return recommendations[level] || 'Datos no disponibles';
  };

  const getDataSourceLabel = (source) => {
    const labels = {
      'tempo_satellite': '🛰️ Satélite NASA TEMPO',
      'unavailable': '⚠️ Datos no disponibles',
      'unsupported': '⚠️ Contaminante no soportado',
      'simulated': '🔬 Datos simulados'
    };
    return labels[source] || source;
  };

  if (loading && !currentData && dataAvailable === true) {
    return (
      <div className="dashboard-loading">
        <div className="loading-content">
          <div className="spinner-large"></div>
          <p className="loading-text">Cargando datos de calidad del aire...</p>
          <p className="loading-subtext">Conectando con satélite NASA TEMPO...</p>
        </div>
      </div>
    );
  }

  // Vista inicial sin ubicación - con fondo de Spline
  if (!location) {
    return (
      <div className="dashboard-container">
        <TopBar />
        
        {/* Spline Background */}
        <div className="spline-container">
          <spline-viewer 
            url="https://prod.spline.design/eB760BIfkgxR51h9/scene.splinecode"
          ></spline-viewer>
        </div>

        {/* Overlay gradient */}
        <div className="overlay-gradient"></div>

        {/* Search Interface */}
        <div style={{
          position: 'relative',
          zIndex: 20,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem'
        }}>
          <div style={{
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '24px',
            padding: '3rem 2.5rem',
            maxWidth: '600px',
            width: '100%',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            animation: 'fadeInUp 0.8s ease-out'
          }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <Cloud style={{ 
                width: '4rem', 
                height: '4rem', 
                color: '#60a5fa',
                margin: '0 auto 1rem'
              }} />
              <h1 style={{
                fontSize: '2.5rem',
                fontWeight: '700',
                background: 'linear-gradient(135deg, #fff 0%, #60a5fa 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                marginBottom: '0.75rem'
              }}>
                Monitoreo de Calidad del Aire
              </h1>
              <p style={{
                fontSize: '1.125rem',
                color: '#d1d5db',
                marginBottom: '0.5rem'
              }}>
                Busca una ciudad para comenzar
              </p>
              <p style={{
                fontSize: '0.95rem',
                color: '#9ca3af'
              }}>
                Datos en tiempo real del satélite NASA TEMPO
              </p>
            </div>

            {/* Search Input */}
            <div className="location-search-section" style={{ marginBottom: '1rem' }}>
              <div className="search-input-wrapper">
                <Search className="search-icon" />
                <input
                  type="text"
                  className="search-input"
                  placeholder="Buscar ubicación (ciudad, país)..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                  onFocus={() => searchResults.length > 0 && setShowResults(true)}
                  autoFocus
                />
              </div>

              {/* Search Results */}
              {showResults && searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.map((result, idx) => (
                    <div
                      key={idx}
                      className="search-result-item"
                      onClick={() => selectLocation(result)}
                    >
                      <MapPin className="result-icon" />
                      <div className="result-text">
                        <p className="result-name">{result.display_name.split(',')[0]}</p>
                        <p className="result-full">{result.display_name}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button 
              className="location-btn" 
              onClick={getCurrentLocation}
              style={{ width: '100%' }}
            >
              <MapPin className="location-btn-icon" />
              Usar mi ubicación
            </button>

            <div style={{
              marginTop: '2rem',
              padding: '1rem',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
              borderRadius: '0.75rem'
            }}>
              <p style={{
                fontSize: '0.875rem',
                color: '#d1d5db',
                textAlign: 'center',
                margin: 0
              }}>
                💡 TEMPO cubre principalmente América del Norte. Otras regiones pueden tener disponibilidad limitada.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <TopBar />
      
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <Cloud className="header-icon" />
            <div>
              <h1 className="header-title">Air Track Dashboard</h1>
              <p className="header-subtitle">Monitoreo de Calidad del Aire en Tiempo Real</p>
            </div>
          </div>
          <div className="header-right">
            <Clock className="clock-icon" />
            <span>
              {location 
                ? `Hora local: ${localTime.toLocaleTimeString()}`
                : `Actualizado: ${lastUpdate.toLocaleTimeString()}`
              }
            </span>
          </div>
        </div>

        <div className="header-content" style={{ paddingTop: '1rem', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', width: '100%' }}>
            <div style={{
              padding: '0.5rem 1rem',
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(12px)',
              borderRadius: '0.5rem',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <Activity style={{ width: '1rem', height: '1rem', color: '#60a5fa' }} />
              <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>AQI:</span>
              <span className={`${getAQIColor(overallAQI)}`} style={{
                fontWeight: 'bold',
                padding: '0.125rem 0.5rem',
                borderRadius: '0.25rem',
                fontSize: '0.875rem'
              }}>
                {overallAQI || '--'}
              </span>
            </div>

            {['NO2', 'O3', 'HCHO'].map((pollutant) => {
              const data = pollutantData[pollutant];
              const isSelected = selectedPollutant === pollutant;
              
              return (
                <button
                  key={pollutant}
                  onClick={() => handleSelectPollutant(pollutant)}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '0.5rem',
                    border: isSelected ? '2px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.1)',
                    background: isSelected ? 'rgba(59, 130, 246, 0.3)' : 'rgba(255, 255, 255, 0.05)',
                    backdropFilter: 'blur(12px)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    color: 'white',
                    boxShadow: isSelected ? '0 0 0 3px rgba(59, 130, 246, 0.3)' : 'none'
                  }}
                  className="pollutant-quick-btn"
                >
                  <span style={{ fontWeight: '600', fontSize: '0.875rem' }}>{pollutant}:</span>
                  {data?.available ? (
                    <>
                      <span style={{ fontSize: '0.875rem', fontWeight: 'bold' }}>{data.value?.toFixed(2)}</span>
                      <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{data.unit}</span>
                      <span className={getAQIColor(data.aqi)} style={{
                        padding: '0.125rem 0.375rem',
                        borderRadius: '0.25rem',
                        fontSize: '0.75rem',
                        fontWeight: 'bold'
                      }}>
                        {data.aqi || '--'}
                      </span>
                    </>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>No disponible</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        {pollutantLoading && (
          <div style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(4px)',
            zIndex: 50,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{
              background: 'rgba(30, 41, 59, 0.9)',
              borderRadius: '1rem',
              padding: '2rem',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
              textAlign: 'center'
            }}>
              <Loader style={{
                width: '3rem',
                height: '3rem',
                color: '#60a5fa',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 1rem'
              }} />
              <p style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                Cargando datos de {selectedPollutant}...
              </p>
              <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                Consultando satélite NASA TEMPO
              </p>
            </div>
          </div>
        )}

        {dataSource && (
          <div className={`data-source-banner ${dataAvailable ? 'source-active' : 'source-unavailable'}`}>
            <span className="source-label">{getDataSourceLabel(dataSource)}</span>
            {!dataAvailable && (
              <span className="source-message">
                No hay datos satelitales disponibles para {selectedPollutant} en esta ubicación en este momento. 
                Intenta con otra ciudad o vuelve más tarde.
              </span>
            )}
          </div>
        )}

        <div className="location-search-section">
          <div className="search-container">
            <div className="search-input-wrapper">
              <Search className="search-icon" />
              <input
                type="text"
                className="search-input"
                placeholder="Buscar ubicación (ciudad, país)..."
                value={searchQuery}
                onChange={handleSearchChange}
                onFocus={() => searchResults.length > 0 && setShowResults(true)}
              />
            </div>
            <button className="location-btn" onClick={getCurrentLocation}>
              <MapPin className="location-btn-icon" />
              Usar mi ubicación
            </button>
          </div>

          {showResults && searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((result, idx) => (
                <div
                  key={idx}
                  className="search-result-item"
                  onClick={() => selectLocation(result)}
                >
                  <MapPin className="result-icon" />
                  <div className="result-text">
                    <p className="result-name">{result.display_name.split(',')[0]}</p>
                    <p className="result-full">{result.display_name}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="location-banner">
          <div className="location-info">
            <MapPin className="location-icon" />
            <h2 className="location-name">{location.name}</h2>
          </div>
          <p className="location-coords">
            Lat: {location.lat.toFixed(4)}, Lon: {location.lon.toFixed(4)}
          </p>
        </div>

        {alerts.length > 0 && (
          <div className="alerts-section">
            {alerts.map((alert, idx) => (
              <div key={idx} className={`alert-card alert-${alert.level}`}>
                <div className="alert-content">
                  <AlertTriangle className="alert-icon" />
                  <div className="alert-text">
                    <h3 className="alert-title">{alert.message}</h3>
                    <p className="alert-description">{alert.recommendation}</p>
                    <p className="alert-expires">
                      Expira: {new Date(alert.expires_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="main-grid">
          <div className="aqi-card">
            <div className="card-header">
              <h3 className="card-title">
                <Activity className="title-icon" />
                AQI Actual - {selectedPollutant}
              </h3>
            </div>

            {dataAvailable && currentData ? (
              <div>
                <div className="aqi-display">
                  <div className={`aqi-circle ${getAQIColor(currentData?.aqi || 0)}`}>
                    <span className="aqi-value">{currentData?.aqi || '--'}</span>
                  </div>
                  <p className={`aqi-level ${getAQIColor(currentData?.aqi || 0)}`}>
                    {currentData?.quality_level || 'Desconocido'}
                  </p>
                </div>

                <div className="aqi-details">
                  <div className="detail-box">
                    <div className="detail-row">
                      <span className="detail-label">Contaminante</span>
                      <span className="detail-value">{currentData?.pollutant || '--'}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Concentración</span>
                      <span className="detail-value">
                        {currentData?.value?.toFixed(2)} {currentData?.unit || ''}
                      </span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Fuente de datos</span>
                      <span className="detail-value-small">{getDataSourceLabel(dataSource)}</span>
                    </div>
                  </div>

                  <div className="recommendation-box">
                    <Eye className="recommendation-icon" />
                    <p className="recommendation-text">
                      {getHealthRecommendation(currentData?.quality_level)}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="no-data">
                <XCircle className="no-data-icon" size={64} />
                <h3 className="no-data-title">Datos no disponibles</h3>
                <p className="no-data-message">
                  No se encontraron mediciones de {selectedPollutant} en esta ubicación de Norteamérica.
                </p>
                <p className="no-data-suggestion">
                  Intenta seleccionar otra ubicación o contaminante, o vuelve a consultar más tarde.
                </p>
              </div>
            )}
          </div>

          <div className="forecast-card">
            <h3 className="card-title">
              <TrendingUp className="title-icon" />
              Pronóstico 24 Horas
            </h3>
            
            <div className="forecast-scroll">
              <div className="forecast-items">
                {forecast.filter((_, idx) => idx % 3 === 0).slice(0, 8).map((item, idx) => {
                  const hour = new Date(item.timestamp).getHours();
                  return (
                    <div key={idx} className="forecast-item">
                      <span className="forecast-hour">{hour}:00</span>
                      <div className={`forecast-aqi ${getAQIColor(item.aqi)}`}>
                        {item.aqi}
                      </div>
                      <span className="forecast-pollutant">{item.primary_pollutant}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="weather-factors">
              <div className="factor-card">
                <Wind className="factor-icon" />
                <span className="factor-label">Impacto del Viento</span>
                <p className="factor-text">
                  Vientos moderados pueden mejorar la calidad del aire esta tarde
                </p>
              </div>
              <div className="factor-card">
                <ThermometerSun className="factor-icon factor-icon-orange" />
                <span className="factor-label">Temperatura</span>
                <p className="factor-text">
                  Altas temperaturas pueden aumentar la formación de ozono
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="pollutants-section">
          <h3 className="section-title">Contaminantes Monitoreados por TEMPO</h3>
          <div className="pollutants-grid">
            {pollutants.map((pollutant, idx) => {
              const data = pollutantData[pollutant.name];
              const isSelected = selectedPollutant === pollutant.name;
              
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectPollutant(pollutant.name)}
                  className={`pollutant-card ${isSelected ? 'selected' : ''}`}
                >
                  <div className="pollutant-header">
                    <h4 className="pollutant-name">{pollutant.name}</h4>
                    <Droplets className="pollutant-icon" />
                    </div>
                  <p className="pollutant-full-name">{pollutant.full_name}</p>
                  
                  {data?.available ? (
                    <div style={{ marginBottom: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{data.value?.toFixed(2)}</span>
                        <span style={{ fontSize: '0.875rem', color: '#9ca3af' }}>{data.unit}</span>
                      </div>
                      <div className={getAQIColor(data.aqi)} style={{
                        display: 'inline-block',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.25rem',
                        fontSize: '0.875rem',
                        fontWeight: 'bold',
                        marginBottom: '0.25rem'
                      }}>
                        AQI: {data.aqi}
                      </div>
                      <p style={{ fontSize: '0.75rem', color: '#9ca3af', margin: 0 }}>{data.quality_level}</p>
                    </div>
                  ) : (
                    <div style={{ padding: '0.5rem 0' }}>
                      <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>No disponible</p>
                    </div>
                  )}
                  
                  <div className="pollutant-info">
                    <p className="pollutant-sources">
                      Fuentes: {pollutant.sources.slice(0, 2).join(', ')}
                    </p>
                    <p className="pollutant-health">
                      ⚠️ {pollutant.health_effects}
                    </p>
                  </div>
                  {isSelected && (
                    <div className="pollutant-badge">Seleccionado</div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div className="weather-section">
          <h3 className="section-title">
            <Cloud className="title-icon" />
            Factores Meteorológicos y Ambientales
          </h3>
          <div className="weather-grid">
            <div className="weather-card">
              <div className="weather-header">
                <Wind className="weather-icon" />
                <span className="weather-label">Velocidad del Viento</span>
              </div>
              <p className="weather-value">12 km/h</p>
              <p className="weather-description">
                Dirección NE, ayuda a dispersar contaminantes
              </p>
            </div>
            <div className="weather-card">
              <div className="weather-header">
                <ThermometerSun className="weather-icon weather-icon-orange" />
                <span className="weather-label">Temperatura</span>
              </div>
              <p className="weather-value">24°C</p>
              <p className="weather-description">
                Moderada, condiciones favorables
              </p>
            </div>
            <div className="weather-card">
              <div className="weather-header">
                <Droplets className="weather-icon weather-icon-cyan" />
                <span className="weather-label">Humedad</span>
              </div>
              <p className="weather-value">65%</p>
              <p className="weather-description">
                Niveles normales, sin precipitación esperada
              </p>
            </div>
          </div>
        </div>

        <div className="info-section">
          <h3 className="section-title">Acerca de los Datos</h3>
          <div className="info-content">
            <div className="info-card">
              <h4 className="info-title">🛰️ Satélite NASA TEMPO</h4>
              <p className="info-text">
                TEMPO (Tropospheric Emissions: Monitoring of Pollution) es el primer instrumento espacial 
                que monitorea la contaminación del aire sobre América del Norte cada hora durante el día.
              </p>
            </div>
            <div className="info-card">
              <h4 className="info-title">📊 Disponibilidad de Datos</h4>
              <p className="info-text">
                Los datos satelitales pueden no estar disponibles para todas las ubicaciones en todo momento 
                debido a cobertura de nubes, horarios de paso del satélite, o procesamiento de datos. 
                TEMPO cubre principalmente América del Norte.
              </p>
            </div>
            <div className="info-card">
              <h4 className="info-title">🔬 Mediciones</h4>
              <p className="info-text">
                Los valores se miden en partes por billón (ppb) y se convierten a índice de calidad del aire (AQI) 
                para facilitar su interpretación. El AQI varía de 0 a 500, donde valores más altos indican mayor contaminación.
              </p>
            </div>
          </div>
        </div>

        <div className="dashboard-footer">
          <p>Datos impulsados por satélite NASA TEMPO • Mediciones en tiempo real • Integración meteorológica</p>
          <p>Apollo 5C Team - NASA Space Apps Challenge 2025</p>
        </div>
      </div>
    </div>
  );
}