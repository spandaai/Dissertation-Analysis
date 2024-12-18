import React from 'react'
import "../styles/Modal.css";
import {url} from './url';
const Modal = ({ show, onClose, selectedText, handleInputChange, feedback, loading, setLoading,setShowModal,preAnalysisData }) => {
  const apiUrl = window?.env?.REACT_APP_API_URL || url;
    const handleFeedback = async () => {
      setLoading(true); // Set loading state
      // Construct the payload
      const payload = {
        selectedText: selectedText,
        feedback: feedback,
        preAnalysisData: preAnalysisData['pre_analyzed_summary']
      };
  
      try {
     
        
        const response = await fetch(`${apiUrl}/api/submitFeedback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload), // Send payload to backend
        });
  
        if (response.ok) {
          // Handle success
          const data = await response.json();
          console.log('Feedback stored successfully:', data);
        } else {
          // Handle errors
          console.error('Error storing feedback:', response.statusText);
        }
      } catch (error) {
        console.error('Network error:', error);
      } finally {
        setLoading(false); 
        setShowModal(false);
        
      }
    };
  
    if (!show) {
      return null;
    }
  
    return (
  <div className="modal-backdrop">
        <div className="modal">
          <h3>Selected Text</h3>
          <p style={{ "maxHeight": "40vh", "overflowY": "scroll", "textAlign": "justify", "border": "1px solid #eee" }}>
            {selectedText}
          </p>
  
                    <textarea
              placeholder="Type your feedback here..."
              onChange={handleInputChange}
              value={feedback}
             className="feedback_box"
            /> 
  
          <div className="button-container">
            <button onClick={onClose}>
              Close
            </button>
            <button onClick={handleFeedback}>
              {loading ? "..." : "Store Feedback"}
            </button>
          </div>
        </div>
      </div>
    );
  };

export default Modal
