// TopBar.jsx - Barra de navegación superior
import { useState } from 'react';
import '../styles/TopBar.css';

function TopBar() {
  const [activeLink, setActiveLink] = useState('inicio');

  const handleClick = (link) => {
    setActiveLink(link);
  };

  return (
    <nav className="topbar">
      <div className="topbar-container">
        {/* Logo / Nombre del proyecto */}
        <div className="topbar-logo">
          <span className="logo-text">Air Track</span>
          <span className="logo-subtitle">Apollo 5C</span>
        </div>

        {/* Links de navegación */}
        <ul className="topbar-menu">
          <li>
            <a
              href="#inicio"
              className={`topbar-link ${activeLink === 'inicio' ? 'active' : ''}`}
              onClick={() => handleClick('inicio')}
            >
              Inicio
            </a>
          </li>
          <li>
            <a
              href="#acerca-de"
              className={`topbar-link ${activeLink === 'acerca-de' ? 'active' : ''}`}
              onClick={() => handleClick('acerca-de')}
            >
              Acerca de
            </a>
          </li>
          <li>
            <a
              href="#datos"
              className={`topbar-link ${activeLink === 'datos' ? 'active' : ''}`}
              onClick={() => handleClick('datos')}
            >
              Datos
            </a>
          </li>
        </ul>

        {/* Botón móvil hamburguesa */}
        <button className="mobile-menu-btn" aria-label="Menú">
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>
      </div>
    </nav>
  );
}

export default TopBar;