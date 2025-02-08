# WebSocket Endpoint Documentation: `/api/ws/dissertation_analysis`

## Overview
This WebSocket endpoint enables real-time dissertation analysis. Clients can send dissertation-related data and receive step-by-step analysis feedback.

## Workflow
1. Accepts an incoming WebSocket connection.
2. Receives JSON data containing:
   - A rubric for evaluation.
   - Pre-analysis data about the dissertation.
   - Optional feedback from the user.
3. Initializes the dissertation analysis process asynchronously.
4. Streams results back to the client in real-time.
5. Handles disconnections and errors gracefully.

## Request Structure (JSON Payload)
```json
{
    "rubric": {
        "criterion_1": {
            "criteria_explanation": "Clarity of argument",
            "score_explanation": "Scores range from 1 to 5 based on coherence",
            "criteria_output": "Well-structured argument with supporting evidence"
        },
        "criterion_2": {
            "criteria_explanation": "Use of references",
            "score_explanation": "Scores based on appropriate citation usage",
            "criteria_output": "Citations follow APA style"
        }
    },
    "pre_analysis": {
        "degree": "PhD",
        "name": "John Doe",
        "topic": "Machine Learning for Healthcare",
        "pre_analyzed_summary": "The dissertation explores ML models for medical diagnosis."
    },
    "feedback": "Please focus on methodological accuracy"
}
```

## Response Format (WebSocket Messages)
Messages are sent as JSON objects with a `type` field:

### Progress Updates(WIP)
```json
{
    "type": "progress",
    "data": {
        "step": "Processing Introduction",
        "progress": "20%"
    }
}
```

### Analysis Results
```json
{
    "type": "result",
    "data": {
        "criterion": "Clarity of argument",
        "score": 4,
        "feedback": "The argument is clear but could use more supporting evidence."
    }
}
```

### Completion Message
```json
{
    "type": "completed",
    "data": {
        "message": "Dissertation analysis finished successfully."
    }
}
```

### Error Handling
```json
{
    "type": "error",
    "data": {
        "message": "Invalid rubric format."
    }
}
```

## Usage Example
1. Clients establish a WebSocket connection to `ws://<host>:9000/api/ws/dissertation_analysis`.
2. Send a properly formatted JSON payload.
3. Receive real-time dissertation analysis updates in the formats above.

## Error Handling
- If an exception occurs during processing, an error message is sent.
- If the WebSocket disconnects, processing is halted safely.

## Returns
- None (Communication occurs via WebSocket messages).

