import React, { useState,useRef,useEffect } from "react";
import "../styles/Dashboard.css"; 
import "../styles/Dissertation.css"; 
import Sidebar from '../components/Sidebar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBrain, faChartLine, faStar, faLightbulb,faBolt,faAddressCard,faPhone,faTasks,faLock } from '@fortawesome/free-solid-svg-icons';
import { faFacebook, faTwitter, faLinkedin, faInstagram } from '@fortawesome/free-brands-svg-icons'; // Import social media icons

function Dashboard() {
    const [isSidebarActive, setIsSidebarActive] = useState(false);
  const sidebarRef = useRef(null); 

  const DashBoard_Url = process.env.URL;

  
  const toggleSidebar = () => {
    setIsSidebarActive(!isSidebarActive);
  };

  const handleClickOutside = (event) => {
    if (
      sidebarRef.current && 
      !sidebarRef.current.contains(event.target) && 
      !document.getElementById('open-btn').contains(event.target)
    ) {
      setIsSidebarActive(false);
    }
  };

  useEffect(() => {
    // Add event listener for clicks outside the sidebar
    document.addEventListener('mousedown', handleClickOutside);
    
    // Cleanup listener on component unmount
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  return (
    <div className='main-container'>
    <div className="nav">
    <button id="open-btn" className="open-btn" onClick={toggleSidebar}>☰</button>
    <h1 className="nav-heading">Spanda Dashboard</h1>
  </div>
  <Sidebar isActive={isSidebarActive} toggleSidebar={toggleSidebar} setSidebarActive={setIsSidebarActive}/>
  <div className="chart-container">
  <iframe 
    src={`${DashBoard_Url}/?standalone=2`}
    width="100%" 
    height="1050px"
    frameBorder="1">
</iframe>

      </div>

      <footer className="footer">
    <div className="footer-content">
        <div className="branding">
        <h2><span className="highlight">[</span>  Spanda<span className="highlight">.</span>AI  <span className="highlight">]</span></h2>
            <p>Empowering insights and intelligence through AI-driven solutions.</p>
            <hr className="divider" />
        </div>
        
        <div className="footer-links">
            <h3>Quick Links</h3>
            <ul>
                <li><FontAwesomeIcon icon={faAddressCard} className="link-icon" /><a href="https://www.spanda.ai/about"> About Us</a></li>
                <li><FontAwesomeIcon icon={faTasks} className="link-icon" /><a href="https://www.spanda.ai/"> Services</a></li>
                <li><FontAwesomeIcon icon={faPhone} className="link-icon" /><a href="https://www.spanda.ai/contact"> Contact</a></li>
                <li><FontAwesomeIcon icon={faLock} className="link-icon" /><a href="https://www.spanda.ai/"> Privacy Policy</a></li>
            </ul>
            <hr className="divider" />
        </div>
        
        <div className="social-media">
            <h3>Connect with Us</h3>
            <div className="social-icons">
                <a href="https://www.facebook.com" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faFacebook} />
                </a>
                <a href="https://www.twitter.com" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faTwitter} />
                </a>
                <a href="https://www.linkedin.com/company/spandaAI" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faLinkedin} />
                </a>
                <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faInstagram} />
                </a>
            </div>
        </div>
    </div>
    
    <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} Spanda.AI. All Rights Reserved.</p>
    </div>
</footer>

      </div>
  )
}

export default Dashboard;
