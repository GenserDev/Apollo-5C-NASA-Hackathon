import { useEffect, useState, useRef } from 'react';
import '../styles/Home.css';

function HomeSection() {
  const [isLoading, setIsLoading] = useState(true);
  const splineViewerRef = useRef(null);

  useEffect(() => {
    const script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://unpkg.com/@splinetool/viewer@1.10.74/build/spline-viewer.js';
    
    script.onload = () => {
      setTimeout(() => {
        setIsLoading(false);
        
        setTimeout(() => {
          const splineViewer = splineViewerRef.current?.querySelector('spline-viewer');
          if (splineViewer) {
            splineViewer.addEventListener('load', () => {
              if (splineViewer.play) {
                splineViewer.play();
              }
              
              const canvas = splineViewer.shadowRoot?.querySelector('canvas');
              if (canvas) {
                canvas.style.pointerEvents = 'auto';
              }
            });
          }
        }, 500);
      }, 1000);
    };

    document.head.appendChild(script);

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, []);

  const handleExploreData = () => {
    const datosSection = document.getElementById('datos');
    if (datosSection) {
      datosSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLearnMore = () => {
    const aboutSection = document.getElementById('acerca-de');
    if (aboutSection) {
      aboutSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Generar estrellas aleatorias
  const generateStars = () => {
    const stars = [];
    for (let i = 0; i < 150; i++) {
      const style = {
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 3}s`,
        animationDuration: `${2 + Math.random() * 3}s`,
      };
      stars.push(<div key={i} className="star" style={style}></div>);
    }
    return stars;
  };

  return (
    <>
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="spinner"></div>
            <p className="loading-text">Cargando Air Track...</p>
          </div>
        </div>
      )}

      <section id="inicio" className="home-container">
        {/* Capa de estrellas */}
        <div className="stars-container">
          {generateStars()}
        </div>

        <div className="spline-container" ref={splineViewerRef}>
          <spline-viewer 
            url="https://prod.spline.design/eB760BIfkgxR51h9/scene.splinecode"
            loading-anim-type="spinner-big-light"
          ></spline-viewer>
        </div>

        <div className="overlay-gradient"></div>

        <div className="content-layout">
          <div className="content-side">
            <div className="content-card">
              <h1 className="main-title">Air Track</h1>
              <p className="subtitle">Monitoreo de Calidad del Aire en Tiempo Real</p>
              <p className="description">
                Predice cielos más limpios y seguros con datos de observación terrestre
              </p>
              
              <div className="button-group">
                <button className="btn-primary" onClick={handleExploreData}>
                  Explorar Datos
                </button>
                <button className="btn-secondary" onClick={handleLearnMore}>
                  Saber más
                </button>
              </div>

              <div className="team-badge">By: Apollo 5C Team</div>
            </div>
          </div>

          <div className="planet-space"></div>
        </div>

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
      </section>
    </>
  );
}

export default HomeSection;