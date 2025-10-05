import TopBar from '../components/TopBar';
import HomeSection from '../components/HomeSection';
import AboutSection from '../components/AboutSection';
import '../styles/global.css';

export default function App() {
  return (
    <div style={{ width: '100%', overflowX: 'hidden' }}>
      <TopBar />
      <HomeSection />
      <AboutSection />
    </div>
  );
}