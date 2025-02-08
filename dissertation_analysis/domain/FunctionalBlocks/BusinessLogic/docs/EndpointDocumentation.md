# Dissertation Analysis API Documentation

## Overview
The Dissertation Analysis API provides multiple endpoints for processing and analyzing dissertation documents. This API includes functionalities such as summarization, chunk processing, name extraction, topic extraction, degree extraction, and scoring based on predefined criteria.

## Base URL
```
http://localhost:9002
```

## Endpoints

### 1. Process Chunks
**Endpoint:**
```
POST /process-chunks
```
**Description:**
Processes text chunks in batches for summarization.

**Request Body:**
```json
{
    "chunks": ["chunk1", "chunk2"],
    "system_prompt": "Summarize this content",
    "batch_size": 5
}
```

**Response:**
```json
["summary1", "summary2"]
```

---

### 2. Summarize and Analyze
**Endpoint:**
```
POST /summarize-analyze
```
**Description:**
Summarizes and analyzes a dissertation document.

**Request Body:**
```json
{
    "text": "Complete dissertation text here."
}
```

**Response:**
```json
{
    "summary": "Summarized content here."
}
```

---

### 3. Extract Name
**Endpoint:**
```
POST /extract-name
```
**Description:**
Extracts the author's name from a dissertation.

**Request Body:**
```json
{
    "text": "Complete dissertation text here."
}
```

**Response:**
```json
{
    "name": "Author Name"
}
```

---

### 4. Extract Topic
**Endpoint:**
```
POST /extract-topic
```
**Description:**
Extracts the topic of a dissertation.

**Request Body:**
```json
{
    "text": "Complete dissertation text here."
}
```

**Response:**
```json
{
    "topic": "Dissertation Topic"
}
```

---

### 5. Extract Degree
**Endpoint:**
```
POST /extract-degree
```
**Description:**
Extracts the degree associated with the dissertation.

**Request Body:**
```json
{
    "text": "Complete dissertation text here."
}
```

**Response:**
```json
{
    "degree": "Degree Information"
}
```

---

### 6. Scoring
**Endpoint:**
```
POST /scoring
```
**Description:**
Scores a dissertation based on predefined criteria.

**Request Body:**
```json
{
    "analysis": "Analysis of dissertation",
    "criteria": "Evaluation criteria",
    "score_guidelines": "Scoring guidelines",
    "criteria_guidelines": "Guidelines for criteria",
    "feedback": "Feedback provided"
}
```

**Response:**
```json
{
    "score": "Final score"
}
```

---

### 7. Process Initial Analysis
**Endpoint:**
```
POST /process-initial
```
**Description:**
Processes the initial analysis of a dissertation, extracting the name, topic, and degree.

**Request Body:**
```json
{
    "text": "Complete dissertation text here."
}
```

**Response:**
```json
{
    "degree": "Degree Information",
    "name": "Author Name",
    "topic": "Dissertation Topic"
}
```

## Notes
- Ensure the API is running on `http://localhost:9002` before testing.
- Each endpoint expects a valid JSON request body.
- Response times may vary depending on the complexity of the input text.

---

**Author:** Spanda.AI Team  
**Version:** 1.0.0  
**Date:** February 2025

