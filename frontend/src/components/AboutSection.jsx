import '../styles/AboutSection.css';

function AboutSection() {
  return (
    <section id="acerca-de" className="about-section">
      <div className="about-container">
        <div className="about-header">
          <h2 className="about-title">Acerca de Air Track</h2>
          <div className="title-underline"></div>
        </div>

        <div className="about-content">
          <div className="about-text">
            <h3 className="about-subtitle">Nuestra Misión</h3>
            <p className="about-description">
              Air Track es una plataforma innovadora desarrollada para el NASA Space Apps Challenge 2025, 
              diseñada para monitorear y predecir la calidad del aire en tiempo real utilizando datos 
              de observación terrestre de la NASA.
            </p>
            <p className="about-description">
              Combinamos tecnologías de cloud computing con machine learning para analizar datos 
              satelitales y proporcionar predicciones precisas sobre la calidad del aire, ayudando 
              a comunidades y gobiernos a tomar decisiones informadas para proteger la salud pública.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🌍</div>
              <h4 className="feature-title">Datos Satelitales</h4>
              <p className="feature-description">
                Utilizamos datos de observación terrestre de la NASA para monitoreo global
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">☁️</div>
              <h4 className="feature-title">Cloud Computing</h4>
              <p className="feature-description">
                Procesamiento en la nube para análisis en tiempo real de grandes volúmenes de datos
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h4 className="feature-title">Machine Learning</h4>
              <p className="feature-description">
                Algoritmos predictivos para anticipar cambios en la calidad del aire
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h4 className="feature-title">Visualización</h4>
              <p className="feature-description">
                Dashboards interactivos para visualizar datos de forma clara y accesible
              </p>
            </div>
          </div>

          <div className="team-section">
            <h3 className="about-subtitle">El Equipo</h3>
            <p className="team-description">
              Apollo 5C Team nace gracias a la iniciativa de la NASA Space Apps Challenge, 
              con el objetivo de crear soluciones tecnológicas que contribuyan a un futuro más sostenible.
              Haciendo uso de los varios recursos proporcionados por la NASA.  
              
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default AboutSection;