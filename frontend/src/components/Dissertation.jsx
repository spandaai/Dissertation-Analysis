import React, { useState,useRef,useEffect } from "react";
import { getDocument } from 'pdfjs-dist';
import {pdfjsWorker} from 'pdfjs-dist';
import mammoth from "mammoth";
import "../styles/Dissertation.css";
import "../styles/Modal.css";
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import axios from 'axios';
import { faUpload } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleNotch } from '@fortawesome/free-solid-svg-icons';


import { faBrain, faChartLine, faStar, faLightbulb,faBolt,faAddressCard,faPhone,faTasks,faLock } from '@fortawesome/free-solid-svg-icons';
import { useDropzone } from 'react-dropzone';
import { CircularProgress, Typography, Box, IconButton, Button } from '@mui/material'; // Consolidated imports here
import DeleteIcon from '@mui/icons-material/Delete';
import { styled, width } from '@mui/system'; // Import styled from @mui/system
import Sidebar from '../components/Sidebar';
import { faFacebook, faTwitter, faLinkedin, faInstagram } from '@fortawesome/free-brands-svg-icons'; // Import social media icons
import rubrics from "../utils/rubricData";

import rubricpayloadreceived from "../utils/payload";
import Modal from "./Modal";
import { marked } from 'marked';
import {url} from './url';
const iconList = [faBrain, faChartLine, faStar, faLightbulb,faBolt];
const { constantRubric, businessRubric } = rubrics;
const { constantRubricpayload, businessRubricpayload } = rubricpayloadreceived;

const Dissertation = () => {
  const [file, setFile] = useState(null);
  const [responseData, setResponseData] = useState(null);
  const [pdfContent, setPdfContent] = useState("");
  const [preAnalysisData, setPreAnalysisData] = useState(null);
  const [response, setResponse] = useState("");
  const [isEditable, setIsEditable] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isPreanalyzing, setIsPreanalyzing] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [responseloading, setResponseloading] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [userData, setUserData] = useState("");
  const [files, setFiles] = useState([]);
  const [progress, setProgress] = useState({});
  const [isSidebarActive, setIsSidebarActive] = useState(false);
  const sidebarRef = useRef(null); 
  const [analyzing, setAnalyzing] = useState(false);
  const [queueStatus, setQueueStatus] = useState({ queue: false, position: 0 });
  const [fileUrls, setFileUrls] = useState({});
  const [streamingActive, setStreamingActive] = useState(false); 
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedRubric, setSelectedRubric] = useState(null);
  const [showRubric, setShowRubric] = useState(constantRubric); // Default state
  const [rubricpayload, setRubricpayload] = useState(rubricpayloadreceived.constantRubricpayload); // Default state
  const apiUrl = window?.env?.REACT_APP_API_URL || url;
  console.log(apiUrl);
  //console.log(window.env.REACT_APP_API_URL);
  console.log(url);
  const handleSelectChange = (event) => {
    const selectedOption = event.target.value;
    if (selectedOption === "option1") {
      setShowRubric(rubrics.constantRubric);
      setRubricpayload(rubricpayloadreceived.constantRubricpayload);
    } else if (selectedOption === "option2") {
      setShowRubric(rubrics.businessRubric);
      setRubricpayload(rubricpayloadreceived.businessRubricpayload);
    }

  };

  
  
  const countDimensions = (rubric) => {
    // Check if rubric is a valid object
    if (typeof rubric === "object" && rubric !== null) {
      return Object.keys(rubric).length;
    }
    return 0; // Return 0 if rubric is not valid
  };
  
  const numberOfDimensions = countDimensions(showRubric);
  useEffect(() => {
    const newFileUrls = {};
    files.forEach(file => {
      if (!fileUrls[file.id]) {
        newFileUrls[file.id] = URL.createObjectURL(file.file);
      }
    });
    setFileUrls(prevUrls => ({ ...prevUrls, ...newFileUrls }));

    // Clean up URLs when component unmounts
    return () => {
      Object.values(newFileUrls).forEach(url => URL.revokeObjectURL(url));
    };
  }, [files]);

  const getSessionId = () => {
    return sessionStorage.getItem("sessionId");
  };
  
  const setSessionId = (id) => {
    sessionStorage.setItem("sessionId", id); // Save sessionId to sessionStorage
  };
  
  const initializeSessionId = () => {
    const existingSessionId = getSessionId();
    if (!existingSessionId) {
      const newSessionId = generateSessionId(); // Function to generate a unique sessionId
      setSessionId(newSessionId);
      return newSessionId;
    }
    return existingSessionId;
  };
  
  // Utility to generate sessionId (if needed)
  const generateSessionId = () => {
    return `session-${Math.random().toString(36).substr(2, 9)}-${Date.now()}`;
  };
  

  // Reset analyzing state once the response is loaded
  if (response && analyzing) {
    setAnalyzing(false);
  }

  const downloadPDF = () => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
  
    const greyTextColor = [50, 50, 50];
    const goldenYellowColor = [255, 204, 0];
  
    // Title
    doc.setFontSize(24);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(...greyTextColor);
    doc.text("Dissertation Evaluation", 14, 20);
  
    // Current Date
    const currentDate = new Date().toLocaleDateString();
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(100);
    doc.text(`Date: ${currentDate}`, pageWidth - 20, 30, { align: 'right' });
  
    // Horizontal Line
    doc.setDrawColor(200);
    doc.line(10, 35, pageWidth - 10, 35);
  
    // Total Score
    doc.setFontSize(16);
    doc.setTextColor(0);
    const normalizedScore = response?.total_score && numberOfDimensions
    ? (response.total_score / numberOfDimensions).toFixed(2)
    : 'N/A';
  
  doc.text(`Total Score: ${normalizedScore}/5`, 14, 50);
  
    // Criteria Evaluations
    if (response?.criteria_evaluations) {
      const tableData = Object.keys(response.criteria_evaluations).map((criterion) => {
        const evaluation = response.criteria_evaluations[criterion];
  
        // Process feedback using marked
        const feedbackMarkdown = evaluation?.feedback || "No justification provided.";
        const feedbackHtml = marked(feedbackMarkdown); // Convert markdown to HTML
        const feedbackText = feedbackHtml.replace(/<[^>]+>/g, ''); // Remove HTML tags for PDF
  
        const score = evaluation?.score !== undefined ? evaluation.score : "No score available.";
  
        return [
          criterion,
          feedbackText, // Use cleaned feedback text
          score
        ];
      });
  
      // Set a title for the table
      doc.setFontSize(14);
      doc.setTextColor(...greyTextColor);
  
      // Create the table with updated text formatting
      doc.autoTable({
        startY: 60,
        head: [['Criterion', 'Feedback', 'Score']],
        body: tableData,
        theme: 'grid',
        styles: { fontSize: 10, cellPadding: 5, halign: 'left' },
        headStyles: { fillColor: [100, 100, 100], textColor: 255, fontStyle: 'bold' },
        bodyStyles: { fillColor: [245, 245, 245], textColor: 50 },
        alternateRowStyles: { fillColor: [255, 255, 255] },
        columnStyles: {
          0: { cellWidth: 40, halign: 'left' },
          1: { cellWidth: 125, halign: 'left' }, // Align feedback to left
          2: { cellWidth: 20, halign: 'center' }
        }
      });
    }
  
    // Page footer with page numbers
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
  
      doc.setFontSize(14);
      doc.setFont("helvetica", "normal");
  
      doc.setTextColor(...goldenYellowColor);
      doc.text("[", pageWidth - 37, 10);
      doc.text(".", pageWidth - 18, 10);
      doc.text("]", pageWidth - 11, 10);
  
      doc.setTextColor(...greyTextColor);
      doc.text("Spanda AI", pageWidth - 35, 10);
  
      doc.setFontSize(10);
      doc.setTextColor(100);
      doc.text(`Page ${i} of ${pageCount}`, pageWidth / 2, doc.internal.pageSize.getHeight() - 10, { align: 'center' });
    }
  
    // Save the PDF
    doc.save("Dissertation_Evaluation.pdf");
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

  useEffect(() => {
    initializeSessionId();

    connectToNotificationWebSocket();
  }, []);
  
  const handleTextSelection = () => {
    if (isEditable) {
      const selection = window.getSelection();
      const selectedText = selection.toString();
      const anchorNode = selection.anchorNode;
  
      const isInCriteriaBox = anchorNode && (anchorNode.nodeType === 3
        ? anchorNode.parentNode.closest('.criteria-box')
        : anchorNode.closest('.criteria-box'));
  
      if (isInCriteriaBox && selectedText) {
        setSelectedText(selectedText);
      }
    }
  };
  

  const handleInputChange = (e) => {
    setFeedback(e.target.value);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedText("");
    
  };


  const openrubricModal = (section, content) => {
    setSelectedRubric({ section, content });
    setModalOpen(true);
  };

  const closerubricModal = () => {
    setModalOpen(false);
    setSelectedRubric(null);
  };




  const onDrop = (acceptedFiles) => {
    const updatedFiles = acceptedFiles.map(file => {
        if (file.type !== 'application/pdf') {
            // If the file is not a PDF, show an alert and skip adding it
            alert('Only PDF files are accepted');
            return null; // return null or skip the file
        }

        return {
            file,
            id: Math.random(),
            progress: 0
        };
    }).filter(file => file !== null); // Remove null values (non-PDF files)

    // Only update the state if there are valid PDF files
    if (updatedFiles.length > 0) {
        setFiles(prevFiles => [...prevFiles, ...updatedFiles]);

        updatedFiles.forEach(file => {
            handleUpload({ target: { files: [file.file] } }); // Trigger parsing and content extraction
            uploadFile(file);
        });
    }
};


const handleUpload = async (e) => {
  const selectedFile = e.target.files[0];
  if (!selectedFile) {
    alert("Please select a file.");
    return;
  }
  setFile(selectedFile); 
};

const extractTextAndImages = async (file) => {
  setIsExtracting(true);
  const formData = new FormData();
  formData.append("file", file);

  const apiHost = `${apiUrl}/api/extract_text_from_file_and_analyze_images`;  

  try {
    const response = await fetch(apiHost, { 
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to extract text and images");
    }

    return await response.json();
  } catch (error) {
    console.error("An error occurred:", error);
    throw error;  
  } finally {
    setIsExtracting(false);
  }
};


const preAnalyzeText = async (extractedData) => {
  setIsPreanalyzing(true);
  const thesisText = extractedData?.text_and_image_analysis || "";

  const apiHost = `${apiUrl}/api/pre_analyze`; // Append the endpoint path

  try {
    const response = await fetch(apiHost, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thesis: thesisText,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to pre-analyze text");
    }

    return await response.json();
  } catch (error) {
    console.error("An error occurred during pre-analysis:", error);
    throw error; // Re-throw if further handling is needed
  } finally {
    setIsPreanalyzing(false);
  }
};


const uploadFile = (file) => {
    const formData = new FormData();
    formData.append('file', file.file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload'); // Change to your upload URL

    xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
            const progressValue = (event.loaded / event.total) * 100;
            setProgress(prevProgress => ({
                ...prevProgress,
                [file.id]: progressValue
            }));
        }
    };

    xhr.onload = () => {
        if (xhr.status === 200) {
            console.log('Upload successful!');
        }
    };

    xhr.send(formData);
};

const { getRootProps, getInputProps } = useDropzone({ onDrop });

const removeFile = (id) => {
    setFiles(files.filter(file => file.id !== id));
    setProgress(prevProgress => {
        const newProgress = { ...prevProgress };
        delete newProgress[id]; // Remove progress entry for the deleted file
        return newProgress;
    });
};

const postDataToBackend = async (postData) => {
 
  const apiHost = `${apiUrl}/api/postUserData`;  // Append the endpoint path

  try {
    const response = await axios.post(apiHost, postData);  // Use the dynamic URL
    console.log('Data posted successfully', response.data);
  } catch (error) {
    console.error('There was an error posting the data!', error);
  }
};

const extractAndPostData = (result) => {
  // Check if name and degree are found in the result
  if (!result.name || !result.degree) {
    alert('Name or Degree not found in PDF');
    return; // Stop further execution if either is missing
  }

  const userData = {
    name: result.name,
    degree: result.degree,
    topic: result.topic,
    total_score: result.total_score / numberOfDimensions
  };

  const userScores = Object.entries(result.criteria_evaluations).map(([dimensionName, evaluation]) => ({
    dimension_name: dimensionName,
    score: evaluation.score
  }));

  const postData = {
    userData,    
    userScores   
  };

  setUserData(postData);

  postDataToBackend(postData);
};


const connectToNotificationWebSocket = () => {
    const notificationUrl = `${apiUrl.replace("http", "ws")}/api/ws/notifications`;
    const notificationWebSocket = new WebSocket(notificationUrl);
  
    notificationWebSocket.onopen = () => {
      console.log("Connected to notification WebSocket");
      const sessionId = getSessionId();
      if (sessionId) {
        notificationWebSocket.send(sessionId);
      } else {
        console.warn("No sessionId available to send. Skipping.");
      }
    };
  
    notificationWebSocket.onmessage = (event) => {
      const notification = JSON.parse(event.data);
  
      if (notification.type === "reconnect" && notification.session_id) {
        console.log(`Reconnect notification received for session: ${notification.session_id}`);
        reconnectToProcessing(notification.session_id);
      }
    };
  
    notificationWebSocket.onclose = () => {
      console.log("Notification WebSocket closed.");
    };
  
    notificationWebSocket.onerror = (error) => {
      console.error("Error with notification WebSocket:", error);
    };
  };  


const handleWebSocketMessage = (response) => {
  switch (response.type) {
    case "queue_status":
      setQueueStatus({ queue: true });
      console.log("Request is queued. Waiting for processing to start...");
      if (response.data.session_id) {
        reconnectToProcessing(response.data.session_id);
      }
      break;

    case "metadata":
      setQueueStatus({ queue: false });
      setAnalyzing(true);
      setIsExtracting(false);
      setIsPreanalyzing(false);
      setResponse((prev) => ({
        ...prev,
        name: response.data.name,
        degree: response.data.degree,
        topic: response.data.topic,
      }));
      break;

    case "criterion_start":
      const criterion = response.data.criterion;
      const rubricEntry = showRubric[criterion];
      setResponse((prev) => ({
        ...prev,
        criteria_evaluations: {
          ...prev.criteria_evaluations,
          [criterion]: {
            feedback: "",
            score: 0,
            criteria_explanation: rubricEntry?.criteria_explanation || "",
            criteria_output: rubricEntry?.criteria_output || "",
            score_explanation: rubricEntry?.score_explanation || "",
          },
        },
      }));
      break;

    case "analysis_chunk":
      setQueueStatus({ queue: false });
      setResponse((prev) => {
        const criterion = response.data.criterion;
        const newFeedback =
          prev.criteria_evaluations[criterion].feedback + response.data.chunk;
        return {
          ...prev,
          criteria_evaluations: {
            ...prev.criteria_evaluations,
            [criterion]: {
              ...prev.criteria_evaluations[criterion],
              feedback: newFeedback,
            },
          },
        };
      });
      break;

    case "criterion_complete":
      setResponse((prev) => {
        const criterion = response.data.criterion;
        const updatedEvaluation = {
          ...prev.criteria_evaluations[criterion],
          score: response.data.score,
        };

        const updatedEvaluations = {
          ...prev.criteria_evaluations,
          [criterion]: updatedEvaluation,
        };

        const newTotalScore = Object.values(updatedEvaluations).reduce(
          (acc, evaluation) => acc + (evaluation.score || 0),
          0
        );

        return {
          ...prev,
          criteria_evaluations: updatedEvaluations,
          total_score: newTotalScore,
        };
      });
      break;

    case "complete":
      setResponse((prev) => ({
        ...prev,
        evaluation_complete: true,
      }));
      setAnalyzing(false);
      break;

    case "error":
      alert(`Error: ${response.data.message}`);
      setAnalyzing(false);
      setQueueStatus({ queue: false });
      break;

    default:
      console.warn("Unknown response type:", response.type);
  }
};



const  handleEvaluate = async () => {
  setResponse("");
  if (!file) {
    alert("No file selected. Please upload a file first.");
    return;
  }
  setResponseloading(true);
  setAnalyzing(true);

  const websocketUrl = `${apiUrl.replace("http", "ws")}/api/ws/dissertation_analysis`; // Convert to WebSocket URL
  const reconnectUrlBase = `${apiUrl.replace("http", "ws")}/api/ws/dissertation_analysis_reconnect?session_id=`;

  try {
    console.log("Starting extraction...");
    const extractedData = await extractTextAndImages(file);
    console.log("Extraction complete:", extractedData);

    if (!extractedData) {
      throw new Error("Failed to extract data from PDF");
    }

    console.log("Starting pre-analysis...");
    const analysisData = await preAnalyzeText(extractedData);
    console.log("Pre-analysis complete:", analysisData);

    if (!analysisData) {
      throw new Error("Failed to pre-analyze text");
    }

    setPreAnalysisData(analysisData);
 
    // Establish WebSocket connection
    const websocket = new WebSocket(websocketUrl);

    websocket.onopen = () => {
      console.log("WebSocket connection established");
      // Send initial payload to backend
      websocket.send(
        JSON.stringify({
          pre_analysis: analysisData,
          rubric: rubricpayload,
          feedback: "Please provide constructive feedback based on evaluation.",
        })
      );
    };

    websocket.onmessage = (event) => {
      const response = JSON.parse(event.data);

      // Handle WebSocket messages
      switch (response.type) {
        case "queue_status":
          // Request is queued; store session ID and wait for notification
          setQueueStatus({ queue: true });
          console.log("Request is queued. Waiting for processing to start...");
          if (response.data.session_id) {
            reconnectToProcessing(response.data.session_id);
          }
          break;

        case "metadata":
          // Processing has started; update states
          setQueueStatus({ queue: false });
          setAnalyzing(true);
          setIsExtracting(false);      // Extraction is complete
          setIsPreanalyzing(false);    // Pre-analysis is complete
          setResponse((prev) => ({
            ...prev,
            name: response.data.name,
            degree: response.data.degree,
            topic: response.data.topic,
          }));
          break;

        case "criterion_start":
          // Criterion evaluation has started
          const criterion = response.data.criterion;
          const rubricEntry = showRubric[criterion];
          setResponse((prev) => ({
            ...prev,
            criteria_evaluations: {
              ...prev.criteria_evaluations,
              [criterion]: {
                feedback: "",
                score: 0,
                criteria_explanation: rubricEntry?.criteria_explanation || "",
                criteria_output: rubricEntry?.criteria_output || "",
                score_explanation: rubricEntry?.score_explanation || "",
              },
            },
          }));
          break;

        case "analysis_chunk":
          // Receive streaming chunks
          setQueueStatus({ queue: false });
          setResponse((prev) => {
            const criterion = response.data.criterion;
            const newFeedback =
              prev.criteria_evaluations[criterion].feedback + response.data.chunk;
            return {
              ...prev,
              criteria_evaluations: {
                ...prev.criteria_evaluations,
                [criterion]: {
                  ...prev.criteria_evaluations[criterion],
                  feedback: newFeedback,
                },
              },
            };
          });
          break;

        case "criterion_complete":
          // Criterion evaluation is complete
          setResponse((prev) => {
            const criterion = response.data.criterion;
            const updatedEvaluation = {
              ...prev.criteria_evaluations[criterion],
              score: response.data.score,
            };

            const updatedEvaluations = {
              ...prev.criteria_evaluations,
              [criterion]: updatedEvaluation,
            };

            const newTotalScore = Object.values(updatedEvaluations).reduce(
              (acc, evaluation) => acc + (evaluation.score || 0),
              0
            );

            return {
              ...prev,
              criteria_evaluations: updatedEvaluations,
              total_score: newTotalScore,
            };
          });
          break;

          case "complete":
            extractAndPostData({
              ...response.data,
              total_score: response.data.total_score,
            });
            setResponse((prev) => ({
              ...prev,
              evaluation_complete: true,
            }));
            break;

        case "error":
          // Handle errors
          alert(`Error: ${response.data.message}`);
          setAnalyzing(false);
          setQueueStatus({ queue: false });
        
          break;

        default:
          console.warn("Unknown response type:", response.type);
      }
    };

    websocket.onclose = () => {
      console.log("WebSocket connection closed");
      // Only reset the button if the evaluation process is complete
      if (!queueStatus?.queue) {
        setResponseloading(false);
        setAnalyzing(false);
        setStreamingActive(false);
     
      }
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      alert("There was an error with the WebSocket connection.");
      setResponseloading(false);
      setAnalyzing(false);
      setStreamingActive(false);
     
    };
  } catch (error) {
    console.error("Error during evaluation:", error);
    alert(
      "Error parsing the file or initiating the evaluation. Please try again."
    );
    setResponseloading(false);
    setAnalyzing(false);
    setStreamingActive(false);
   
  }
};


const reconnectToProcessing = (sessionId) => {
    if (!sessionId) {
      console.error("Cannot reconnect. sessionId is missing.");
      return;
    }
  
    console.log(`Reconnecting for session: ${sessionId}`);
    const reconnectUrl = `${apiUrl.replace("http", "ws")}/api/ws/dissertation_analysis_reconnect?session_id=${sessionId}`;
    const websocket = new WebSocket(reconnectUrl);
  
    websocket.onopen = () => {
      console.log(`Reconnected WebSocket for session: ${sessionId}`);
      setQueueStatus({ queue: false });
      setAnalyzing(true);
    };
  
    websocket.onmessage = (event) => {
      const response = JSON.parse(event.data);
      handleWebSocketMessage(response);
    };
  
    websocket.onclose = () => {
      console.log(`WebSocket closed for session: ${sessionId}`);
      if (!analyzing) {
        setResponseloading(false);
      }
    };
  
    websocket.onerror = (error) => {
      console.error(`Error with WebSocket for session: ${sessionId}`, error);
    };
  };
  

  return (
    <div className="main-container">
   <div className="nav">
   <button id="open-btn" className="open-btn" onClick={toggleSidebar}>☰</button>
      <h1 className="nav-heading">Dissertation Analysis</h1>
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
    width: "150px", // Wider dropdown
    background: "linear-gradient(to bottom, #e0e0e0, #c0c0c0)", // Grey gradient
    fontWeight: "bold", // Bold text
    border: "1px solid #a0a0a0", // Optional subtle border
    color: "#000", // Black text
  }}
  onChange={handleSelectChange}
  defaultValue="option1"
>
  <option value="option1">Generic</option>
  <option value="option2">M.B.A</option>
</select>


  <h2 style={{ flexGrow: 1, textAlign: "center", margin: 0 }}>AI Grading Rubric</h2>
</div>


    <div className="rubric-scroll-container">
        <div className="rubric-cards">
            {Object.entries(showRubric).map(([section, content], index) => {
                const handleClick = () => openrubricModal(section, content);

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
                        <h3>{section}</h3>
                        <p>
                            {typeof content.criteria_explanation === 'string'
                                ? content.criteria_explanation.slice(0, 150)
                                : "Description not available"}...
                        </p>
                    </div>
                );
            })}
        </div>
    </div>

    {isModalOpen && (
    <div className="modal_rubric-overlay" onClick={closerubricModal}>
        <div className="modal_rubric-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal_rubric-close-btn" onClick={closerubricModal}>
                &times;
            </button>
            <h2 classname="heading2">{selectedRubric.section}</h2>
            
            <h3 className="heading3">Criteria Explanation</h3>
            <p style={{backgroundColor:'#eee' ,padding:'15px', borderRadius:'10px', color:'#000'}}>{selectedRubric.content.criteria_explanation}</p>

            <h3 className="heading3">Criteria Output</h3>
            <p style={{backgroundColor:'#eee' ,padding:'15px', borderRadius:'10px', color:'#000'}}>
                {Object.entries(selectedRubric.content.criteria_output)
                    .map(([key, value]) => (
                        <span key={key}>
                            <strong>{key}:</strong> {value}<br />
                        </span>
                    ))}
            </p>

            <h3 className="heading3">Score Explanation</h3>
            <p style={{backgroundColor:'#eee',padding:'15px', borderRadius:'10px', color:'#000'}}>
                {Object.entries(selectedRubric.content.score_explanation)
                    .map(([score, details]) => (
                        <span key={score}>
                            <strong>{score}:</strong> {details.Description} <br />
                            <em>Examples:</em> {details.Examples} <br />
                            <em>Explanation:</em> {details.Explanation}<br />
                        </span>
                    ))}
            </p>
        </div>
    </div>
)}

</div>

 <div className="response-container">
 <div className="upload-container" style={{ display: 'flex', flexDirection: 'column', height: '85vh' }}>
  <div style={{ flex: 1 }}> {/* This will take the remaining space */}
    {files.length === 0 ? (
      <div
        {...getRootProps({ className: 'dropzone' })}
        style={{ textAlign: 'center', padding: '40px', borderRadius: '8px' }}
      >
        <input {...getInputProps()} />
        <FontAwesomeIcon icon={faUpload} style={{ fontSize: '3rem', color: '#eee' }} />
        <p style={{ color: '#fff', fontWeight: '600' }}>Drag & drop files here, or click to select files</p>
      </div>
    ) : (
      <ul className="file-list" style={{ padding: 0, margin: 0 }}>
        {files.map((file) => (
          <li
            key={file.id}
            className="file-item"
            style={{ marginBottom: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
          >
            {file.file.type === 'application/pdf' && fileUrls[file.id] && (
              <object
                data={fileUrls[file.id]}
                type="application/pdf"
                width="100%"
                height="400px"
                style={{
                  display: 'block',
                  marginTop: '10px',
                  border: '2px solid #ccc',
                  borderRadius: '8px',
                }}
              >
                <p>Your browser does not support viewing PDF files. Please download the PDF to view it:</p>
                <a href={fileUrls[file.id]} download>
                  Download PDF
                </a>
              </object>
            )}

            <Box display="flex" alignItems="center" style={{ marginTop: '10px' }}>
              <CircularProgress
                variant="determinate"
                value={progress[file.id] || 0}
                size={46}
                style={{ color: 'yellow' }} // Set the circular progress color to yellow
              />
              <Typography variant="body1" style={{ marginLeft: '15px' }}>
                {file.file.name.length > 15 ? `${file.file.name.slice(0, 15)}...` : file.file.name} -{' '}
                {formatFileSize(file.file.size)}
              </Typography>
              <IconButton onClick={() => removeFile(file.id)} style={{ color: '#eee' }}> {/* Set the delete icon color to #eee */}
                <DeleteIcon />
              </IconButton>
            </Box>
          </li>
        ))}
      </ul>
    )}
  </div>

  {files.length > 0 && (
  <div className="evaluate-button-container" style={{ marginTop: 'auto' }}> 
    <Button onClick={handleEvaluate} disabled={responseloading}>
      {responseloading ? (
          <div className="loader"></div> // Add this class for the loader styling
       
      ) : (
        'Evaluate'
      )}
    </Button>


  </div>
)}

</div>


      <div style={{ width: '70%' }}>
        <div className="response-header">
          <h2>Response Box:</h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={downloadPDF} className="download-button">Download PDF</button>
            <button onClick={() => setShowModal(true)} disabled={!selectedText} className="feedback-button">
              Send Feedback
            </button>
          </div>
        </div>

        <div
  className={`response-content ${queueStatus?.queue ? "queued" : ""} ${analyzing ? "processing" : ""}`}
  contentEditable={!queueStatus?.queue && !isExtracting && !isPreanalyzing && analyzing}  
  suppressContentEditableWarning={true}
  onMouseUp={handleTextSelection}
>
  {queueStatus?.queue ? (
    // Display queued state
    <p className="queue-status">
      Your request is queued. Please wait...
      <span className="loading-dots">
        <span className="dot">.</span>
        <span className="dot">.</span>
        <span className="dot">.</span>
      </span>
    </p>
  ) : isExtracting ? (
    // Display extraction state
    <p className="analyzing-text">
      Pre-Analyzing Images and Extracting text
      <span className="loading-dots">
        <span className="dot">.</span>
        <span className="dot">.</span>
        <span className="dot">.</span>
      </span>
    </p>
  ) : isPreanalyzing ? (
    // Display pre-analysis state
    <p className="analyzing-text">
      Processing data
      <span className="loading-dots">
        <span className="dot">.</span>
        <span className="dot">.</span>
        <span className="dot">.</span>
      </span>
    </p>
  ) : analyzing ? (
    // Display real-time processing state
    <p className="analyzing-text">
      Processing your request
      <span className="loading-dots">
        <span className="dot">.</span>
        <span className="dot">.</span>
        <span className="dot">.</span>
      </span>
    </p>
  ) : response ? (
    <>
      {/* Display final response with total score */}
      <div className="total-score-box">
        <h3>
          Total Score: {response.total_score !== undefined && numberOfDimensions > 0
            ? `${(response.total_score / numberOfDimensions).toFixed(2)}/5`
            : '-'}
        </h3>
      </div>
      <div className="criteria-container">
        {response.criteria_evaluations && Object.keys(response.criteria_evaluations).length > 0 ? (
          Object.keys(response.criteria_evaluations).map((criterion, index) => {
            const evaluation = response.criteria_evaluations[criterion];
            return (
              <div key={index} className="criteria-box">
                <h3>{criterion}</h3>
                <p style={{ color: '#eee' }}>
                  <strong>Justification:</strong>{' '}
                  <span 
                    dangerouslySetInnerHTML={{
                      __html: marked(evaluation?.feedback || 'No justification provided.'),
                    }}
                  />
                </p>
                <p style={{ color: '#eee' }}>
                  <strong>Score:</strong>{' '}
                  {evaluation?.score !== undefined ? `${evaluation.score}/5` : 'No score available.'}
                </p>
              </div>
            );
          })
        ) : (
          <p>No criteria evaluations available.</p>
        )}
      </div>
    </>
  ) : (
    // Default state when no response is available
    <p className="default-message">To begin the evaluation, kindly submit your thesis file for review!</p>
  )}
</div>

      </div>
    </div>

      <Modal 
        show={showModal} 
        onClose={closeModal} 
        selectedText={selectedText} 
        handleInputChange={handleInputChange} 
        feedback={feedback}
        loading={loading}
        setLoading={setLoading} 
        setShowModal={setShowModal}
        preAnalysisData={preAnalysisData}
      />
       
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

  );
};


const formatFileSize = bytes => {
  if (bytes >= 1000000) return (bytes / 1000000).toFixed(2) + ' MB';
  return (bytes / 1000).toFixed(2) + ' KB';
};


export default Dissertation;
