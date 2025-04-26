import React, { useState,useRef,useEffect } from "react";
import "../styles/BatchProcess.css";
import "../styles/Modal.css";
import axios from 'axios';
import url from './url.js';
import Sidebar from '../components/Sidebar';
import { faUpload } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBrain, faChartLine, faStar, faLightbulb,faBolt,faAddressCard,faPhone,faTasks,faLock } from '@fortawesome/free-solid-svg-icons';
import { 
    faPaperclip, 
    faSearch, 
    faFilePdf, 
    faTimes, 
    faChevronLeft, 
    faChevronRight 
  } from '@fortawesome/free-solid-svg-icons';
const iconList = [faBrain, faChartLine, faStar, faLightbulb,faBolt];


const BatchProcess = () => {
      const [isSidebarActive, setIsSidebarActive] = useState(false);
      const sidebarRef = useRef(null); 
      const [error, setError] = useState(null);
      const [rubrics, setRubrics] = useState([]);
      const [loading, setLoading] = useState(false);
      const [Evaluate, setEvaluate] = useState(false);
      const [transformedRubric, setTransformedRubric] = useState(null);
      const [selectedRubric, setSelectedRubric] = useState(null);
      const [isModalOpen, setIsModalOpen] = useState(false);
      const [modalContent, setModalContent] = useState(null);  
      const apiUrl = url;
      const [files, setFiles] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const itemsPerPage = 12;
  const [selectedFileNames, setSelectedFileNames] = useState("");
  const [removedFiles, setRemovedFiles] = useState([]);


  
  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length === 0) return;
    
    const pdfFiles = selectedFiles.filter(file => file.type === 'application/pdf');
    
    // Set the names of selected files for display
    if (pdfFiles.length > 0) {
      const fileNames = pdfFiles.map(file => file.name).join(", ");
      setSelectedFileNames(fileNames);
    }
    
    setFiles(prev => [...prev, ...pdfFiles]);
    e.target.value = '';
  };

  // Function to submit files to the API
  const submitFiles = async () => {
    try {
      setEvaluate(true)
      // Filter out removed files
      const filesToUpload = files.filter((file, index) => 
        !removedFiles.includes(index)
      );
      
      if (filesToUpload.length === 0) {
        alert("Please select at least one file to upload");
        return;
      }
      
      // Check if transformedRubric exists and is not null
      if (!transformedRubric) {
        alert("Please select the rubric before moving forward");
        return;
      }
      
      // Create form data
      const formData = new FormData();
      
      // Add files
      filesToUpload.forEach(file => {
        formData.append("files", file);
      });
      
      // Add the rubric as a string, but as a proper JSON object when parsed
      formData.append("rubric", JSON.stringify(transformedRubric));
      
      const response = await fetch(`${apiUrl}/dissertation/api/batch_input`, {
        method: "POST",
        body: formData,
        credentials: "include"
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Upload failed: ${JSON.stringify(errorData)}`);
      }
      
      const results = await response.json();
      console.log("Upload successful:", results);
      
      // Handle successful upload
      setFiles([]);
      setSelectedFileNames("");
      setEvaluate(false)
      
    } catch (error) {
      console.error("Error uploading files:", error);
      setEvaluate(false)
      // Handle error
    }
  };
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    const pdfFiles = droppedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length > 0) {
      setFiles(prev => [...prev, ...pdfFiles]);
    }
  };

  // Update your removeFile function
  const removeFile = (index) => {
    // Track removed file indices
    setRemovedFiles(prev => [...prev, index]);
    
    // Update UI for removed files
    const updatedFiles = [...files];
    updatedFiles.splice(index, 1);
    setFiles(updatedFiles);
    
    // Adjust current page if needed
    const newTotalPages = Math.ceil(updatedFiles.length / itemsPerPage);
    if (currentPage > newTotalPages && newTotalPages > 0) {
      setCurrentPage(newTotalPages);
    }
  };
  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  // Filter files by search term
  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Calculate pagination
  const totalPages = Math.max(1, Math.ceil(filteredFiles.length / itemsPerPage));
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedFiles = filteredFiles.slice(startIndex, startIndex + itemsPerPage);
  
  const nextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };
  
  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

      const openRubricModal = (dimension) => {
        setModalContent(dimension);
        setIsModalOpen(true);
      };
    
      const closeRubricModal = () => {
        setIsModalOpen(false);
        setModalContent(null);
      };
    

      const fetchSamlData = async () => {
        try {
          const response = await axios.get(`${apiUrl}/dissertation/api/get-saml-data`, {
            withCredentials: true, // Important for session-based auth
          });
      
        } catch (error) {
          console.error("Error fetching SAML data:", error);
        }
      };
      
      // ✅ Automatically fetch SAML data when the page loads after SSO redirection
      window.onload = () => {
        fetchSamlData();
      };

      const transformRubric = (rubric) => {
        const transformedData = {};
      
        rubric.dimensions.forEach((dimension) => {
          transformedData[dimension.name] = {
            criteria_explanation: dimension.criteria_explanation,
            criteria_output: Object.entries(dimension.criteria_output)
              .map(([key, value], index) => `${index + 1}. ${value}`)
              .join("\n"),
            score_explanation: Object.entries(dimension.score_explanation)
              .map(
                ([score, details]) =>
                  `${score}: ${details.Description}.\n   ${details.Examples}\n   ${details.Explanation}`
              )
              .join("\n\n"),
          };
        });
      
        return transformedData;
      };
    
    
    
      
      useEffect(() => {
        const fetchRubrics = async () => {
          try {
            setLoading(true);
            const response = await fetch(`${url}/dissertation/api/rubrics`, {
              credentials: "include",  // ✅ Ensure cookies are sent
            });
            
            if (!response.ok) {
              throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            setRubrics(data);
            setLoading(false);
          } catch (err) {
            setError(err.message);
            setLoading(false);
            console.error('Error fetching rubrics:', err);
          }
        };
    
        fetchRubrics();
      }, []);
    
      // Fetch specific rubric when selected
      const handleSelectChange = async (e) => {
        const rubricId = e.target.value;
        
        if (rubricId === "") {
          setSelectedRubric(null);
          return;
        }
        
        try {
          const response = await fetch(`${url}/dissertation/api/rubrics/${rubricId}`, {
            credentials: "include",  // ✅ Ensure cookies are sent
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          
          const rubricData = await response.json();
          setSelectedRubric(rubricData);
          setTransformedRubric(transformRubric(rubricData));
          console.log("Transformed Rubric",transformedRubric)
          // You can add a callback here or use context/redux to make this data available to other components
          // onRubricSelect(rubricData);
          
        } catch (err) {
          console.error('Error fetching selected rubric:', err);
          setError(err.message);
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


    const handleLogout = async () => {
        try {
        const response = await axios.get(`${apiUrl}/dissertation/api/logout`, { withCredentials: true });
        
        // Check for success response and handle redirect
        if (response.data && response.data.success) {
            window.location.href = response.data.redirect_url;
        }
        } catch (error) {
        console.error('Logout failed:', error);
        }
    };

  return (
    <div className="main-container">
        <div className="nav">
   <button id="open-btn" className="open-btn" onClick={toggleSidebar}>☰</button>
   <h1 className="nav-heading">Bulk Process</h1>
   <button id="logout-btn" className="logout-btn"  onClick={handleLogout}>
     <span className="logout-icon">⏻</span>
     <span className="logout-text">Logout</span>
   </button>
</div>
<div className="evaluator-container">
<Sidebar isActive={isSidebarActive} toggleSidebar={toggleSidebar} setSidebarActive={setIsSidebarActive}/>
      
      <div className="input-container">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
      <select
    style={{
      padding: "5px",
      borderRadius: "4px",
      marginLeft: "20px",
      width: "250px",
      background: "linear-gradient(to bottom, #e0e0e0, #c0c0c0)",
      fontWeight: "bold",
      border: "1px solid #a0a0a0",
      color: "#000",
    }}
    onChange={handleSelectChange}
    defaultValue=""
  >
  <option value="">Select a Rubric</option>
            {rubrics.map((rubric) => (
              <option key={rubric.id} value={rubric.id}>
                {rubric.name}
              </option>
            ))}
  </select>
  
  
    <h2 style={{ flexGrow: 1, textAlign: "center", margin: 0 }}>AI Grading Rubric</h2>
  </div>
  
  {selectedRubric && selectedRubric.dimensions && (
      <div className="rubric-scroll-container">
          <div className="rubric-cards">
          {selectedRubric.dimensions.map((dimension, index) => {
                  const handleClick = () => openRubricModal(dimension);
  
                  return (
                      <div 
                          key={index} 
                          className="rubric-card" 
                          onClick={handleClick}
                      >
                          <FontAwesomeIcon 
                              icon={iconList[index % iconList.length]} 
                              className="card-icon" 
                          />
                      <h3>{dimension.name}</h3>
                      <p>
                      {typeof dimension.criteria_explanation === 'string'
                          ? dimension.criteria_explanation.slice(0, 150)
                                  : "Description not available"}...
                          </p>
                      </div>
                  );
              })}
          </div>
      </div>
        )}
  
  {isModalOpen && modalContent && (
          <div className="modal_rubric-overlay" onClick={closeRubricModal}>
            <div className="modal_rubric-content" onClick={(e) => e.stopPropagation()}>
              <button className="modal_rubric-close-btn" onClick={closeRubricModal}>
                &times;
              </button>
              <h2 className="heading2">{modalContent.name}</h2>
              
              <h3 className="heading3">Criteria Explanation</h3>
              <p style={{backgroundColor:'#eee', padding:'15px', borderRadius:'10px', color:'#000'}}>
                {modalContent.criteria_explanation}
              </p>
  
              <h3 className="heading3">Criteria Output</h3>
              <div style={{backgroundColor:'#eee', padding:'15px', borderRadius:'10px', color:'#000'}}>
                {Object.entries(modalContent.criteria_output || {})
                  .map(([key, value]) => (
                    <div key={key}>
                      <strong>{key}:</strong> {value}
                    </div>
                  ))}
              </div>
  
              <h3 className="heading3">Score Explanation</h3>
              <div style={{backgroundColor:'#eee', padding:'15px', borderRadius:'10px', color:'#000'}}>
                {Object.entries(modalContent.score_explanation || {})
                  .map(([score, details]) => (
                    <div key={score} style={{marginBottom: '15px'}}>
                      <strong>{score}:</strong> {details.Description} <br />
                      <em>Examples:</em> {details.Examples} <br />
                      <em>Explanation:</em> {details.Explanation}
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
  
  </div>


  <div className="pdf-uploader-container">
      <h2 className="uploader-title">PDF Upload</h2>
      
      
      {/* Drop Zone - removed onClick from the container div */}
      <div 
        className={`drop-zone ${isDragging ? 'dragging' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className="icon-container">
          <FontAwesomeIcon icon={faPaperclip} size="3x" />
        </div>
        <p className="drop-zone-title">Drop PDF files here or click to browse</p>
        <p className="drop-zone-subtitle">Upload multiple PDF files</p>
        {/* Added a button to trigger file input explicitly */}
        <button 
          className="browse-button" 
          onClick={triggerFileInput}
          type="button"
        >
          Browse Files
        </button>
      <input 
          type="file" 
          ref={fileInputRef}
          className="file-input" 
          accept="application/pdf" 
          multiple 
          onChange={handleFileChange}
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="file-list-container">
          <div className="file-list-header">
            <h3 className="file-list-title">Uploaded Files ({files.length})</h3>

            <div className="search-sort-container">
              {files.length > 10 && (
                <div className="file-search">
                  <div className="search-icon-container">
                    <FontAwesomeIcon icon={faSearch} />
                  </div>
                  <input 
                    type="text" 
                    placeholder="Search files..." 
                    className="search-input" 
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setCurrentPage(1); // Reset to first page on search
                    }}
                  />
                </div>
              )}
            </div>
          </div>
          
          <div className="file-grid">
            {paginatedFiles.length > 0 ? (
              paginatedFiles.map((file, index) => {
                const actualIndex = startIndex + index;
                return (
                  <div key={`${file.name}-${actualIndex}`} className="file-card">
                    <div className="file-icon">
                      <FontAwesomeIcon icon={faFilePdf} />
                    </div>
                    <div className="file-info">
                      <p className="file-name" title={file.name}>{file.name}</p>
                      <p className="file-size">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(actualIndex);
                      }}
                      className="remove-file-btn"
                      aria-label="Remove file"
                    >
                      <FontAwesomeIcon icon={faTimes} />
                    </button>
                  </div>
                );
              })
            ) : (
              <div className="no-results">No files match your search</div>
            )}

          </div>
          
          {filteredFiles.length > itemsPerPage && (
            <div className="pagination">
              <button 
                className={`pagination-btn ${currentPage === 1 ? 'disabled' : ''}`}
                onClick={prevPage}
                disabled={currentPage === 1}
              >
                <FontAwesomeIcon icon={faChevronLeft} />
              </button>
              <span className="pagination-info">
                Page {currentPage} of {totalPages}
              </span>
              <button 
                className={`pagination-btn ${currentPage === totalPages ? 'disabled' : ''}`}
                onClick={nextPage}
                disabled={currentPage === totalPages}
              >
                <FontAwesomeIcon icon={faChevronRight} />
              </button>
            </div>
          )}
        </div>
      )}
                                {files.length > 0 && (
  <button 
    className="submit-button"
    onClick={submitFiles}
    type="button"
  >
   {Evaluate?"Evaluating...":"Evaluate"} 
  </button>
)}
    </div>

</div>
    </div>
  )
}

export default BatchProcess
