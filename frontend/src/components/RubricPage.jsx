import React, { useState, useEffect ,useRef} from 'react';
import '../styles/RubricPage.css';
import Sidebar from '../components/Sidebar';
import axios from 'axios';
import myUrl from './url';
const RubricManagementApp = () => {
  const [rubrics, setRubrics] = useState([]);
  const [currentView, setCurrentView] = useState('list');
  const [currentRubric, setCurrentRubric] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSidebarActive, setIsSidebarActive] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const sidebarRef = useRef(null); 
  const BACKEND_URL = myUrl;
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
    fetchRubrics();
  }, []);

  const fetchRubrics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/dissertation/api/rubrics`, {
        credentials: "include",  // ✅ Correct way to send cookies
      });
  
      if (!response.ok) {
        throw new Error("UNAUTHORISED");
      }
      const data = await response.json();
      setRubrics(data);
    } catch (err) {
      setError(err.message);
      console.error("Error fetching rubrics:", err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleAddRubric = async (newRubric) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/dissertation/api/rubrics`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",  // ✅ Ensure cookies are sent
        body: JSON.stringify(newRubric),
      });
  
      if (!response.ok) {
        throw new Error("UNAUTHORISED");
      }
      await fetchRubrics();
      setCurrentView("list");
    } catch (err) {
      setError(err.message);
      console.error("Error adding rubric:", err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleUpdateRubric = async (updatedRubric) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/dissertation/api/rubrics/${updatedRubric.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedRubric),
        credentials: "include",  // ✅ Ensure cookies are sent

      });
      if (!response.ok) {
        throw new Error('Failed to update rubric');
      }
      await fetchRubrics();
      setCurrentView('list');
    } catch (err) {
      setError(err.message);
      console.error('Error updating rubric:', err);
    } finally {
      setIsLoading(false);
    }
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

  const handleDeleteRubric = async (rubricId) => {
    if (!window.confirm('Are you sure you want to delete this rubric?')) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/dissertation/api/rubrics/${rubricId}`, {
        credentials: "include",  // ✅ Ensure cookies are sent
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('UNAUTHORISED');
      }
      await fetchRubrics();
    } catch (err) {
      setError(err.message);
      console.error('Error deleting rubric:', err);
    } finally {
      setIsLoading(false);
    }
  };
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

<>
  {userRole === 'STAFF' || userRole === 'staff' ? (
    <div className="app-container">
    <div className="nav">
   <button id="open-btn" className="open-btn" onClick={toggleSidebar}>☰</button>
   <h1 className="nav-heading">Rubric Management System</h1>
   <button id="logout-btn" className="logout-btn"  onClick={handleLogout}>
     <span className="logout-icon">⏻</span>
     <span className="logout-text">Logout</span>
   </button>
</div>
      <Sidebar isActive={isSidebarActive} toggleSidebar={toggleSidebar} setSidebarActive={setIsSidebarActive} />

      <header className="app-header">
        <h1></h1>
        <div className="header-actions">
          {currentView !== 'list' && (
            <button className="btn btn-secondary" onClick={() => setCurrentView('list')}>
              Back to List
            </button>
          )}
          {currentView === 'list' && (
            <button
              className="btn btn-primary"
              onClick={() => {
                setCurrentRubric(null);
                setCurrentView('add');
              }}
            >
              Create New Rubric
            </button>
          )}
        </div>
      </header>

      <main className="app-content">
        {error && <div className="error-message">{error}</div>}

        {isLoading ? (
          <div className="loading-spinner">Loading...</div>
        ) : (
          <>
            {currentView === 'list' && (
              <RubricsList
                rubrics={rubrics}
                onEdit={(rubric) => {
                  setCurrentRubric(rubric);
                  setCurrentView('edit');
                }}
                onDelete={handleDeleteRubric}
              />
            )}

            {currentView === 'add' && (
              <RubricForm
                onSubmit={handleAddRubric}
                initialData={{
                  name: '',
                  dimensions: [],
                }}
                formTitle="Create New Rubric"
              />
            )}

            {currentView === 'edit' && currentRubric && (
              <RubricForm
                onSubmit={handleUpdateRubric}
                initialData={currentRubric}
                formTitle={`Edit Rubric: ${currentRubric.name}`}
              />
            )}
          </>
        )}
      </main>
    </div>
  ) : (
<div className="unauthorized">
  <div className="unauthorized-card">
    <h2>🚫 Unauthorized Access</h2>
    <p>You do not have permission to access this page.</p>
    <button className="go-back-btn" onClick={() => window.location.href = '/'}>
      Go to Homepage
    </button>
  </div>
</div>

  )}
</>


  );
};

const RubricsList = ({ rubrics, onEdit, onDelete }) => {
  if (rubrics.length === 0) {
    return (
      <div className="empty-state">
        <p>No rubrics found. Create your first rubric to get started.</p>
      </div>
    );
  }

  return (


    <div className="rubrics-list">
      <h2>Available Rubrics</h2>
      {rubrics.map((rubric) => (
        <div key={rubric.id} className="rubric-card">
          <h3>{rubric.name}</h3>
          <div className="dimensions-preview">
            <p>{rubric.dimensions.length} dimension(s)</p>
            <ul>
              {rubric.dimensions.slice(0, 3).map((dimension, index) => (
                <li key={index}>{dimension.name}</li>
              ))}
              {rubric.dimensions.length > 3 && <li>...</li>}
            </ul>
          </div>
          <div className="card-actions">
            <button className="btn btn-secondary" onClick={() => onEdit(rubric)}>
              Edit
            </button>
            <button className="btn btn-danger" onClick={() => onDelete(rubric.id)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>


  );
};

const RubricForm = ({ onSubmit, initialData, formTitle }) => {
  const [formData, setFormData] = useState(initialData);
  
  const handleNameChange = (e) => {
    setFormData({ ...formData, name: e.target.value });
  };

  const addDimension = () => {
    setFormData({
      ...formData,
      dimensions: [
        ...formData.dimensions,
        {
          name: '',
          criteria_explanation: '',
          criteria_output: {},
          score_explanation: {
            "Score 1": { Description: '', Examples: '', Explanation: '' },
            "Score 2": { Description: '', Examples: '', Explanation: '' },
            "Score 3": { Description: '', Examples: '', Explanation: '' },
            "Score 4": { Description: '', Examples: '', Explanation: '' },
            "Score 5": { Description: '', Examples: '', Explanation: '' }
          }
        }
      ]
    });
  };

  const removeDimension = (index) => {
    const newDimensions = [...formData.dimensions];
    newDimensions.splice(index, 1);
    setFormData({ ...formData, dimensions: newDimensions });
  };

  const updateDimension = (index, field, value) => {
    const newDimensions = [...formData.dimensions];
    newDimensions[index][field] = value;
    setFormData({ ...formData, dimensions: newDimensions });
  };

  const addCriteriaOutput = (dimensionIndex) => {
    const newDimensions = [...formData.dimensions];
    const criteriaKey = `Criteria ${Object.keys(newDimensions[dimensionIndex].criteria_output).length + 1}`;
    newDimensions[dimensionIndex].criteria_output[criteriaKey] = '';
    setFormData({ ...formData, dimensions: newDimensions });
  };

  const removeCriteriaOutput = (dimensionIndex, criteriaKey) => {
    const newDimensions = [...formData.dimensions];
    const newCriteriaOutput = { ...newDimensions[dimensionIndex].criteria_output };
    delete newCriteriaOutput[criteriaKey];
    newDimensions[dimensionIndex].criteria_output = newCriteriaOutput;
    setFormData({ ...formData, dimensions: newDimensions });
  };

  const updateCriteriaOutput = (dimensionIndex, criteriaKey, value) => {
    const newDimensions = [...formData.dimensions];
    newDimensions[dimensionIndex].criteria_output[criteriaKey] = value;
    setFormData({ ...formData, dimensions: newDimensions });
  };

  const updateScoreExplanation = (dimensionIndex, scoreKey, field, value) => {
    const newDimensions = [...formData.dimensions];
    newDimensions[dimensionIndex].score_explanation[scoreKey][field] = value;
    setFormData({ ...formData, dimensions: newDimensions });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (

    <form className="rubric-form" onSubmit={handleSubmit}>
      <h2>{formTitle}</h2>
      
      <div className="form-group">
        <label htmlFor="rubricName">Rubric Name</label>
        <input
          type="text"
          id="rubricName"
          value={formData.name}
          onChange={handleNameChange}
          required
          className="form-control"
          placeholder="Enter rubric name"
        />
      </div>
      
      <div className="dimensions-section">
        <div className="section-header">
          <h3>Dimensions</h3>
          <button 
            type="button" 
            className="btn btn-secondary btn-sm"
            onClick={addDimension}
          >
            Add Dimension
          </button>
        </div>
        
        {formData.dimensions.map((dimension, dimIndex) => (
          <div key={dimIndex} className="dimension-card">
            <div className="dimension-header">
              <h4>Dimension {dimIndex + 1}</h4>
              <button 
                type="button" 
                className="btn btn-danger btn-sm"
                onClick={() => removeDimension(dimIndex)}
              >
                Remove
              </button>
            </div>
            
            <div className="form-group">
              <label>Dimension Name</label>
              <input
                type="text"
                value={dimension.name}
                onChange={(e) => updateDimension(dimIndex, 'name', e.target.value)}
                required
                className="form-control"
                placeholder="Enter dimension name"
              />
            </div>
            
            <div className="form-group">
              <label>Criteria Explanation</label>
              <textarea
                value={dimension.criteria_explanation}
                onChange={(e) => updateDimension(dimIndex, 'criteria_explanation', e.target.value)}
                className="form-control"
                rows="4"
                placeholder="Explain what this dimension evaluates"
              />
            </div>
            
            <div className="criteria-output-section">
              <div className="section-header">
                <h5>Criteria Output</h5>
                <button 
                  type="button" 
                  className="btn btn-secondary btn-sm"
                  onClick={() => addCriteriaOutput(dimIndex)}
                >
                  Add Criteria
                </button>
              </div>
              
              {Object.entries(dimension.criteria_output).map(([criteriaKey, criteriaValue]) => (
                <div key={criteriaKey} className="criteria-item">
                  <div className="criteria-header">
                    <input
                      type="text"
                      value={criteriaKey}
                      onChange={(e) => {
                        const newDimensions = [...formData.dimensions];
                        const oldValue = newDimensions[dimIndex].criteria_output[criteriaKey];
                        delete newDimensions[dimIndex].criteria_output[criteriaKey];
                        newDimensions[dimIndex].criteria_output[e.target.value] = oldValue;
                        setFormData({ ...formData, dimensions: newDimensions });
                      }}
                      className="form-control"
                      placeholder="Criteria title"
                    />
                    <button 
                      type="button" 
                      className="btn btn-danger btn-sm"
                      onClick={() => removeCriteriaOutput(dimIndex, criteriaKey)}
                    >
                      Remove
                    </button>
                  </div>
                  <textarea
                    value={criteriaValue}
                    onChange={(e) => updateCriteriaOutput(dimIndex, criteriaKey, e.target.value)}
                    className="form-control"
                    rows="3"
                    placeholder="Criteria description"
                  />
                </div>
              ))}
            </div>
            
            <div className="score-explanation-section">
              <h5>Score Explanations</h5>
              {Object.entries(dimension.score_explanation).map(([scoreKey, scoreData]) => (
                <div key={scoreKey} className="score-item">
                  <h6>{scoreKey}</h6>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      value={scoreData.Description}
                      onChange={(e) => updateScoreExplanation(dimIndex, scoreKey, 'Description', e.target.value)}
                      className="form-control"
                      rows="2"
                      placeholder="Score description"
                    />
                  </div>
                  <div className="form-group">
                    <label>Examples</label>
                    <textarea
                      value={scoreData.Examples}
                      onChange={(e) => updateScoreExplanation(dimIndex, scoreKey, 'Examples', e.target.value)}
                      className="form-control"
                      rows="2"
                      placeholder="Score examples"
                    />
                  </div>
                  <div className="form-group">
                    <label>Explanation</label>
                    <textarea
                      value={scoreData.Explanation}
                      onChange={(e) => updateScoreExplanation(dimIndex, scoreKey, 'Explanation', e.target.value)}
                      className="form-control"
                      rows="2"
                      placeholder="Score explanation"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
        
        {formData.dimensions.length === 0 && (
          <div className="empty-state">
            <p>No dimensions added yet. Add dimensions to define your rubric structure.</p>
          </div>
        )}
      </div>
      
      <div className="form-actions">
        <button type="submit" className="btn btn-primary">
          Save Rubric
        </button>
      </div>
    </form> 

  );
};

export default RubricManagementApp;