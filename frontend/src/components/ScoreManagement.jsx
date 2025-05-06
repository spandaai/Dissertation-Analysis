import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import "../styles/ScoreManagement.css";
import Sidebar from '../components/Sidebar';
import url from './url.js';

const ScoreManagement = () => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const sidebarRef = useRef(null); 
  const [error, setError] = useState(null);
  const [editingUserId, setEditingUserId] = useState(null);
  const [currentDimension, setCurrentDimension] = useState(null);
  const [editedScores, setEditedScores] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [isSidebarActive, setIsSidebarActive] = useState(false);
  const [showModal, setShowModal] = useState(false);
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [usersPerPage] = useState(5);

  const BACKEND_URL = url;
  const MAX_DIMENSION_SCORE = 5; // Maximum score limit for dimensions
  const [userRole, setUserRole] = useState(null);
  const [isExpanded, setIsExpanded] = useState(true);

  const toggleTable = () => {
    setIsExpanded(!isExpanded);
  }; 
      // In your useEffect where you fetch users:
useEffect(() => {
  const fetchUsers = async () => {
    try {
      setLoading(true);
      
      // No need to pass any parameters - the backend will use the session cookie
      const response = await axios.get(`${BACKEND_URL}/dissertation/api/users`, {
        withCredentials: true  // Important: ensures cookies are sent with the request
      });
      
      setUsers(response.data);
      setFilteredUsers(response.data);
    
      // Initialize edited scores structure
      const initialEditedScores = {};
      response.data.forEach(user => {
        initialEditedScores[user.id] = [...user.scores];
      });
      setEditedScores(initialEditedScores);
    } catch (err) {
      console.error("Error fetching data:", err);
      // Convert error to string before setting state
      if (err.response?.data?.detail) {
        // If it's an object with a detail property
        setError(typeof err.response.data.detail === 'string' 
          ? err.response.data.detail 
          : JSON.stringify(err.response.data.detail));
      } else {
        setError('Failed to fetch user data');
      }
    } finally {
      setLoading(false);
    }
  };

  fetchUsers();
}, []);

    
   useEffect(() => {
     // Get user role from cookies
     const getCookieValue = (name) => {
       const value = `; ${document.cookie}`;
       const parts = value.split(`; ${name}=`);
       if (parts.length === 2) return parts.pop().split(';').shift();
       return null;
     };
     
     const role = getCookieValue('user_role');
     setUserRole(role);
   }, []);

  useEffect(() => {
    // Filter users based on search term
    const filtered = users.filter(user => 
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.degree.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.topic.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredUsers(filtered);
    setCurrentPage(1); // Reset to first page when search changes
  }, [searchTerm, users]);

  const handleScoreChange = (userId, scoreIndex, newValue) => {
    // Ensure score doesn't exceed the maximum limit
    const limitedValue = Math.min(parseInt(newValue) || 0, MAX_DIMENSION_SCORE);
    
    setEditedScores(prev => ({
      ...prev,
      [userId]: prev[userId].map((score, index) => 
        index === scoreIndex 
          ? { ...score, score: limitedValue }
          : score
      )
    }));
  };

  const handleLogout = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/dissertation/api/logout`, { withCredentials: true });
      
      // Check for success response and handle redirect
      if (response.data && response.data.success) {
        window.location.href = response.data.redirect_url;
      }
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const calculateTotalScore = (userId) => {
    return editedScores[userId].reduce((sum, score) => sum + score.score, 0);
  };

  // Pagination logic
  const indexOfLastUser = currentPage * usersPerPage;
  const indexOfFirstUser = indexOfLastUser - usersPerPage;
  const currentUsers = filteredUsers.slice(indexOfFirstUser, indexOfLastUser);
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

// Also fix your handleSave function:
const handleSave = async (userId) => {
  try {
    setIsSaving(true);
    
    if (!editedScores[userId]) {
      setError('No changes to save.');
      return;
    }

    await axios.put(
      `${BACKEND_URL}/dissertation/api/users/${userId}/scores`,  
      editedScores[userId], // Corrected payload
      { withCredentials: true } // Moved to config
    );

    // Update users state after successful save
    setUsers(prev => prev.map(user => 
      user.id === userId 
        ? { ...user, scores: [...editedScores[userId]], total_score: calculateTotalScore(userId) }
        : user
    ));
    
    setEditingUserId(null);
  } catch (err) {
    // Convert error to string before setting state
    setError(err.response?.data?.detail 
      ? (typeof err.response.data.detail === 'string' 
        ? err.response.data.detail 
        : JSON.stringify(err.response.data.detail)) 
      : 'Failed to update scores'
    );
  } finally {
    setIsSaving(false);
  }
};


  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
      </div>
    );
  }
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

  const renderMarkdown = (text) => {
    return { __html: parseMarkdown(text) };
  };
  
  // Simple markdown parser - could be replaced with a more robust library
  const parseMarkdown = (text) => {
    let html = text
      // Headers
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold my-4">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold my-3">$1</h3>')
      .replace(/^#### (.*$)/gm, '<h4 class="text-base font-bold my-2">$1</h4>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Lists
      .replace(/^\d+\. (.*$)/gm, '<li class="ml-8 list-decimal my-1">$1</li>')
      // Paragraphs
      .replace(/^(?!<[hl]|<li)(.+$)/gm, '<p class="my-2">$1</p>');
    
    return html;
  };
  
  return (
  
    <>
    {/*userRole === 'STAFF' || userRole === 'staff' ? (*/}
      <div className="score-management">
    <div className="nav">
   <button id="open-btn" className="open-btn" onClick={toggleSidebar}>☰</button>
   <h1 className="nav-heading">Score Management System</h1>
   <button id="logout-btn" className="logout-btn"  onClick={handleLogout}>
     <span className="logout-icon">⏻</span>
     <span className="logout-text">Logout</span>
   </button>
  </div>
        <Sidebar isActive={isSidebarActive} toggleSidebar={toggleSidebar} setSidebarActive={setIsSidebarActive} />
        <div className="container-search">
          {/* Added Search Bar */}
          <div className="search-container">
            <input
              type="text"
              placeholder="Search by name, degree, or topic..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
  
          {currentUsers.map((user) => (
            <div className="card" key={user.id}>
              <div className="card-header">
                {editingUserId !== user.id ? (
                  <button onClick={() => setEditingUserId(user.id)} className="btn btn-primary">
                    Edit Scores
                  </button>
                ) : (
                  <div className="button-group">
                    <button onClick={() => handleSave(user.id)} disabled={isSaving} className="btn btn-primary">
                      {isSaving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      onClick={() => {
                        setEditedScores((prev) => ({
                          ...prev,
                          [user.id]: [...user.scores],
                        }));
                        setEditingUserId(null);
                      }}
                      className="btn btn-secondary"
                    >
                      Cancel
                    </button>
                  </div>
                )}
                               <div style={{display:"flex",alignItems:"center",gap:"10px"}}>
                  <h2 className="subtitle">Total Score:  </h2>
                  <div className="total-score-value">
                    {editingUserId === user.id ? calculateTotalScore(user.id) : user.total_score}
                  </div>
                </div>
              </div>
  
              <div className="user-info">
                <div className="info-card">
                  <p className="info-label">Name:</p>
                  <p className="info-value">{user.name}</p>
                </div>
                <div className="info-card">
                  <p className="info-label">Degree:</p>
                  <p className="info-value">{user.degree}</p>
                </div>
                <div className="info-card">
                  <p className="info-label">Topic:</p>
                  <p className="info-value">{user.topic}</p>
                </div>
              </div>
  
 
           
                <div style={{display:"flex", justifyContent:"space-between"}}> 
              <h2 className="subtitle"> Dimension Scores</h2>
              <h2 className="subtitle">Rubric Used: {user.rubric_name}</h2>
              </div>
              <div className="table-container">
      <div className="table-header" onClick={toggleTable} style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px', backgroundColor: '#2b2b2b', borderRadius: '4px', marginBottom: '8px' }}>
        <h3 style={{ margin: 0, fontWeight: 'bold' }}>Scores Table</h3>
        <div className="dropdown-arrow">
          {isExpanded ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 15l-6-6-6 6" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          )}
        </div>
      </div>
      
      {isExpanded && (
        <table className="scores-table">
          <thead>
            <tr>
              <th>Dimension</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {(editingUserId === user.id ? editedScores[user.id] : user.scores).map((score, index) => (
              <tr key={score.dimension_name}>
                <td>{score.dimension_name}</td>
                <td>
                  {editingUserId === user.id ? (
                    <input
                      type="number"
                      value={score.score}
                      onChange={(e) => handleScoreChange(user.id, index, e.target.value)}
                      className="score-input"
                      min="0"
                      max={MAX_DIMENSION_SCORE}
                    />
                  ) : (
                    <div className="score-container">
                      <div className="score-value">{score.score}</div>
                      <div 
                        className="info-icon"
                        onClick={() => {
                          setCurrentDimension(score);
                          setShowModal(true);
                        }}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <line x1="12" y1="16" x2="12" y2="12"></line>
                          <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                      </div>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
            </div>
          ))}

          {/* Pagination Component */}
          {filteredUsers.length > 0 && (
            <div className="pagination-container">
              <button 
                onClick={() => paginate(currentPage - 1)} 
                disabled={currentPage === 1}
                className="pagination-btn pagination-prev"
              >
                &laquo; 
              </button>
              
              <div className="pagination-info">
                <span>Page {currentPage} of {totalPages}</span>
              </div>
              
              <button 
                onClick={() => paginate(currentPage + 1)} 
                disabled={currentPage === totalPages}
                className="pagination-btn pagination-next"
              >
                 &raquo;
              </button>
            </div>
          )}

          {filteredUsers.length === 0 && (
            <div className="no-results">
              <p>No users found matching your search criteria.</p>
            </div>
          )}
        </div>
        
        {showModal && currentDimension && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-header">
                <div className="modal-title">{currentDimension.dimension_name}</div>
                <div className="score-display">
                  <span className="score-label">Score:</span>
                  <span className="score-number">{currentDimension.score}</span>
                  <button 
                    className="close-button"
                    onClick={() => setShowModal(false)}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                  </button>
                </div>
              </div>
              <div className="modal-body">
                <div 
                  className="markdown-content"
                  dangerouslySetInnerHTML={renderMarkdown(currentDimension.data)}
                />
              </div>
            </div>
          </div>
        )}
      </div>
   {/* ) : (
  <div className="unauthorized">
    <div className="unauthorized-card">
      <h2>🚫 Unauthorized Access</h2>
      <p>You do not have permission to access this page.</p>
      <button className="go-back-btn" onClick={() => window.location.href = '/'}>
        Go to Homepage
      </button>
    </div>
  </div>
  
    )*/}
  </>
  
  );
  };

export default ScoreManagement;