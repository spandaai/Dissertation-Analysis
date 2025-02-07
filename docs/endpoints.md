# EdTech Domain API Documentation

## Base URL
`http://localhost:8006`

## WebSocket Endpoints

### document Analysis WebSocket
```
WebSocket: /api/ws/document_analysis
```
Establishes a WebSocket connection for real-time document analysis.

**Request Body:**
```json
{
    "rubric": {
        "criteria_name": {
            "criteria_explanation": "string",
            "score_explanation": "string",
            "criteria_output": "string"
        }
    },
    "pre_analysis": {
        "degree": "string",
        "name": "string",
        "topic": "string",
        "pre_analyzed_summary": "string"
    },
    "feedback": "string"  // optional
}
```

## Text Processing Endpoints

### Chunk Text
```
POST /api/chunk-text
```
Splits input text into semantic chunks using LangChain's RecursiveCharacterTextSplitter.

**Request Body:**
```json
{
    "text": "string",
    "chunk_size": 1000  // optional, default is 1000
}
```

**Response:**
```json
{
    "chunks": [
        ["chunk text here", 995],
        ["next chunk text", 1002]
    ]
}
```

### Get First N Words
```
POST /api/get-first-n-words
```
Extracts the first N words from the input text.

**Request Body:**
```json
{
    "text": "string",
    "n": 500  // must be greater than 0
}
```

**Response:**
```json
{
    "text": "string",
    "word_count": 500
}
```

## Document Processing Endpoints

### Process PDF
```
POST /api/process-pdf
```
Processes PDF files, extracting both text and images. Images are analyzed starting from page 7.

**Request:**
- Multipart form data with PDF file

**Response:**
```json
{
    "text_and_image_analysis": "string"
}
```

### Process DOCX
```
POST /api/process-docx
```
Processes DOCX files, extracting both text and images.

**Request:**
- Multipart form data with DOCX file

**Response:**
```json
{
    "text": "string",
    "image_analyses": {
        "1": "string",
        "2": "string"
    }
}
```

## Image Processing Endpoints

### Analyze Image
```
POST /api/analyze-image
```
Analyzes image content using VLLM or Ollama.

**Request:**
- Binary image data (application/octet-stream)

**Response:**
```json
{
    "response": "string"
}
```

## Document Analysis Endpoints

### Extract Topic
```
POST /api/extract-topic-from-first-few-pages-of-a-document
```
Extracts the research topic from the document's first pages.

**Request Body:**
```json
{
    "document_text": "string"
}
```

**Response:**
```json
{
    "topic": "string"
}
```

### Extract Degree
```
POST /api/extract-degree-from-first-few-pages-of-a-document
```
Extracts degree information from the document's first pages.

**Request Body:**
```json
{
    "document_text": "string"
}
```

**Response:**
```json
{
    "degree": "string"
}
```

### Extract Name
```
POST /api/extract-name-from-first-few-pages-of-a-document
```
Extracts author's name from the document's first pages.

**Request Body:**
```json
{
    "document_text": "string"
}
```

**Response:**
```json
{
    "name": "string"
}
```

### Summarize and Analyze
```
POST /api/summarize-and-analyze-large-documents
```
Provides comprehensive summary and analysis of large documents.

**Request Body:**
```json
{
    "document_text": "string"
}
```

**Response:**
```json
{
    "summary": "string"
}
```

### Process Chunks
```
POST /api/process-chunks
```
Processes and summarizes document chunks in batches.

**Request Body:**
```json
{
    "chunks": ["string"],
    "system_prompt": "string",
    "batch_size": 5  // optional, defaults to 5
}
```

**Response:**
```json
{
    "summarized_chunks": ["string"]
}
```

### Score Criteria
```
POST /api/score-criteria
```
Evaluates specific document criteria using a scoring agent.

**Request Body:**
```json
{
    "analysis": "string",
    "criteria": "string",
    "score_guidelines": "string",
    "criteria_guidelines": "string",
    "feedback": "string"
}
```

**Response:**
```json
{
    "spanda_score": "string"
}
```
