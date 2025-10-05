import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/TopBar.css';

function TopBar() {
  const location = useLocation();
  const [activeLink, setActiveLink] = useState('inicio');
  const [menuOpen, setMenuOpen] = useState(false);

  const handleClick = (link, sectionId) => {
    setActiveLink(link);
    setMenuOpen(false);
    
    // Solo scroll si estamos en la página principal
    if (location.pathname === '/') {
      const section = document.getElementById(sectionId);
      if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  };

  const handleLogoClick = () => {
    setActiveLink('inicio');
    setMenuOpen(false);
  };

  return (
    <nav className="topbar">
      <div className="topbar-container">
        <Link to="/" className="topbar-logo" onClick={handleLogoClick} style={{ textDecoration: 'none', color: 'inherit' }}>
          <span className="logo-text">Air Track</span>
          <span className="logo-subtitle">Apollo 5C</span>
        </Link>

        <ul className={`topbar-menu ${menuOpen ? 'active' : ''}`}>
          <li>
            <Link
              to="/"
              className={`topbar-link ${activeLink === 'inicio' ? 'active' : ''}`}
              onClick={() => {
                handleClick('inicio', 'inicio');
              }}
            >
              Inicio
            </Link>
          </li>
          <li>
            <a
              href="#acerca-de"
              className={`topbar-link ${activeLink === 'acerca-de' ? 'active' : ''}`}
              onClick={(e) => {
                if (location.pathname === '/') {
                  e.preventDefault();
                  handleClick('acerca-de', 'acerca-de');
                } else {
                  // Si estamos en otra página, redirigir al home con el anchor
                  window.location.href = '/#acerca-de';
                }
              }}
            >
              Acerca de
            </a>
          </li>
          <li>
            <Link
              to="/dashboard"
              className={`topbar-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
              onClick={() => {
                setActiveLink('dashboard');
                setMenuOpen(false);
              }}
            >
              Dashboard
            </Link>
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