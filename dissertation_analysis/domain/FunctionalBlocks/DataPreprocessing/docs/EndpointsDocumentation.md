# **Data Preprocessing API Documentation**

## **Overview**  
This API provides endpoints for text chunking, extracting first words, resizing images, batch image processing, and document analysis (PDF & DOCX).  

**Base URL:** `http://<host>:9001/api/`  

---

## **Endpoints**  

### **1. Chunk Text**  
**Endpoint:** `POST /api/chunk-text`  
**Description:** Splits text into semantic chunks.  

#### **Request Body (JSON)**  
```json
{
  "text": "Your long text here...",
  "chunk_size": 1000  # Optional (default: 1000)
}
```

#### **Response (JSON)**  
```json
{
  "chunks": [
    ["Chunk 1 text...", 200],
    ["Chunk 2 text...", 180]
  ]
}
```

---

### **2. Extract First N Words**  
**Endpoint:** `POST /api/first-n-words`  
**Description:** Retrieves the first N words from the given text.  

#### **Request Body (JSON)**  
```json
{
  "text": "Your long text here...",
  "n_words": 50
}
```

#### **Response (JSON)**  
```json
{
  "text": "Extracted first 50 words..."
}
```

---

### **3. Resize Image**  
**Endpoint:** `POST /api/resize-image`  
**Description:** Resizes an uploaded image while maintaining aspect ratio.  

#### **Request Parameters**  
- `file`: Uploaded image file (Required)  
- `max_size`: Maximum allowed dimension (Optional, default: 800)  
- `min_size`: Minimum allowed dimension (Optional, default: 70)  

#### **Response**  
- Returns resized image bytes with appropriate media type.  

---

### **4. Process Images in Batch**  
**Endpoint:** `POST /api/process-images-batch`  
**Description:** Processes multiple images in batches for analysis.  

#### **Request Parameters**  
- `files`: List of image files (Required)  
- `batch_size`: Number of images per batch (Optional, default: 5)  

#### **Response (JSON)**  
```json
{
  "analysis_results": {
    "0": "Analysis result for image 1",
    "1": "Analysis result for image 2"
  }
}
```

---

### **5. Process PDF File**  
**Endpoint:** `POST /api/process-pdf`  
**Description:** Extracts text and analyzes images from an uploaded PDF.  

#### **Request Parameters**  
- `file`: Uploaded PDF file (Required)  

#### **Response (JSON)**  
```json
{
  "text_and_image_analysis": "Extracted text and image analysis result"
}
```

---

### **6. Process DOCX File**  
**Endpoint:** `POST /api/process-docx`  
**Description:** Extracts text and analyzes images from an uploaded DOCX document.  

#### **Request Parameters**  
- `file`: Uploaded DOCX file (Required)  

#### **Response (JSON)**  
```json
{
  "text_and_image_analysis": "Extracted text and image analysis result"
}
```

---

### **7. Health Check**  
**Endpoint:** `GET /api/health`  
**Description:** Simple health check endpoint to verify API status.  

#### **Response (JSON)**  
```json
{
  "status": "healthy"
}
```

---

