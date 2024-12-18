import React, { useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Import useNavigate
import '../styles/Sidebar.css'; 
import bitsLogo from '../styles/images/bitslogo.png'; 
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faBarChart} from '@fortawesome/free-solid-svg-icons';

function Sidebar({ isActive, toggleSidebar, setSidebarActive }) {
  console.log(isActive)
  const sidebarRef = useRef(null);
  const navigate = useNavigate(); // Hook to programmatically navigate

  const handleClickOutside = (event) => {
    if (sidebarRef.current && !sidebarRef.current.contains(event.target)) {
      setSidebarActive(false);
    }
  };

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const logout = () => {
    // Add any necessary logout logic here (e.g., clearing tokens)
    
    navigate('/'); // Navigate to the home page
  };

  return (
<div id="sidebar" className={`sidebar ${isActive ? 'active' : 'inactive'}`} ref={sidebarRef}>
    <button className="close-btn" onClick={toggleSidebar}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11 7L6 12l5 5-1.5 1.5L3 12l6.5-6.5L11 7zM17 7l-5 5 5 5-1.5 1.5L9 12l6.5-6.5L17 7z" fill="#ffffff" />
        </svg>
    </button>
    <div>
        <div className="profile-container">
            <img src={bitsLogo} alt="Profile Picture" className="profile-img" />
            <div style={{ color: '#eee', fontSize: '25px', marginTop: '25px', fontWeight: '600' }}>
                Dissertation Analysis
            </div>
        </div>
        <div>
            <ul className="sidebar-menu">
                <li> 
                    <Link to="/">
                        <FontAwesomeIcon icon={faHome} className="card-icon-sidebar" /> Home
                    </Link>
                </li>
                <li>
                    <Link to="/Spanda_Dashboard">
                        <FontAwesomeIcon icon={faBarChart} className="card-icon-sidebar" /> Spanda Dashboard
                    </Link>
                </li>
            </ul>
        </div>
    </div>
</div>
  );
}

export default Sidebar;
