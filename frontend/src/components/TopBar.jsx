import { useState } from 'react';
import '../styles/TopBar.css';

function TopBar() {
  const [activeLink, setActiveLink] = useState('inicio');
  const [menuOpen, setMenuOpen] = useState(false);

  const handleClick = (link, sectionId) => {
    setActiveLink(link);
    setMenuOpen(false);
    
    // Scroll suave a la sección
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <nav className="topbar">
      <div className="topbar-container">
        <div className="topbar-logo">
          <span className="logo-text">Air Track</span>
          <span className="logo-subtitle">Apollo 5C</span>
        </div>

        <ul className={`topbar-menu ${menuOpen ? 'active' : ''}`}>
          <li>
            <a
              href="#inicio"
              className={`topbar-link ${activeLink === 'inicio' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleClick('inicio', 'inicio');
              }}
            >
              Inicio
            </a>
          </li>
          <li>
            <a
              href="#acerca-de"
              className={`topbar-link ${activeLink === 'acerca-de' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleClick('acerca-de', 'acerca-de');
              }}
            >
              Acerca de
            </a>
          </li>
        </ul>

        <button 
          className="mobile-menu-btn" 
          aria-label="Menú"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>
      </div>
    </nav>
  );
}

export default TopBar;