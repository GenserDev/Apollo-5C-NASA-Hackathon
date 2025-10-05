// NASA Space Apps Challenge 2025
// Pagina principal para visualizar la calidad del aire
// "From EarthData to Action: Cloud Computing with Earth Observation Data for Predicting Cleaner, Safer Skies"

import { useEffect, useState } from 'react';
import TopBar from '../components/TopBar';
import '../styles/Home.css';

export default function Home() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Cargar el script de Spline
    const script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://unpkg.com/@splinetool/viewer@1.10.74/build/spline-viewer.js';
    
    script.onload = () => {
      setTimeout(() => setIsLoading(false), 1000);
    };

    document.head.appendChild(script);

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, []);

  return (
    <div className="home-container">
      {/* TopBar */}
      <TopBar />

      {/* Loading State */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="spinner"></div>
            <p className="loading-text">Cargando Air Track...</p>
          </div>
        </div>
      )}

      {/* Spline Background - Pantalla completa */}
      <div className="spline-container">
        <spline-viewer 
          url="https://prod.spline.design/eB760BIfkgxR51h9/scene.splinecode"
        ></spline-viewer>
      </div>

      {/* Overlay con gradiente sutil */}
      <div className="overlay-gradient"></div>

      {/* Layout con dos columnas */}
      <div className="content-layout">
        {/* Columna izquierda - Contenido */}
        <div className="content-side">
          <div className="content-card">
            <h1 className="main-title">
              Air Track
            </h1>
            <p className="subtitle">
              Monitoreo de Calidad del Aire en Tiempo Real
            </p>
            <p className="description">
              Predice cielos más limpios y seguros con datos de observación terrestre
            </p>
            
            <div className="button-group">
              <button className="btn-primary">
                Explorar Datos
              </button>
              <button className="btn-secondary">
                Saber más
              </button>
            </div>

            <div className="team-badge">
              By: Apollo 5C Team
            </div>
          </div>
        </div>

        {/* Columna derecha - Espacio para el planeta (vacía) */}
        <div className="planet-space"></div>
      </div>

      {/* Indicador de scroll */}
      <div className="scroll-indicator">
        <svg 
          className="scroll-arrow" 
          fill="none" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth="2" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
        </svg>
      </div>
    </div>
  );
}