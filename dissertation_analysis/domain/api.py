from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from dissertation_analysis.domain import business_logic, data_preprocessing, analysis_algorithms
from dissertation_analysis.common.types import (
    DocumentText,
    ChunkSummarizationProcessingRequest,
    ScoringRequest,
    BatchImageProcessingRequest,
    FirstNWordsRequest,
    FirstNWordsResponse,
    ChunkResponse,
    TextChunkRequest,
    QueryRequestThesisAndRubric
)
from fastapi.responses import JSONResponse
from fastapi import File, UploadFile
import logging
import uvicorn


app = FastAPI()

####################################################################################
###########################analysis_algorithms.py endpoints start###################
####################################################################################
@app.websocket("/api/ws/dissertation_analysis")
async def websocket_dissertation(websocket: WebSocket):
    dissertation_analyzer = analysis_algorithms.DissertationAnalyzer()
    
    try:
        await websocket.accept()
        
        # Set up disconnect handler
        websocket.on_disconnect = dissertation_analyzer.handle_disconnect
        
        # Receive and process the initial data
        data = await websocket.receive_json()
        request = QueryRequestThesisAndRubric(**data)
        
        # Process the dissertation analysis
        await dissertation_analyzer.process_dissertation(websocket, request)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected during main processing")
        dissertation_analyzer.mark_connection_closed()
    except Exception as e:
        print(f"Error in main processing: {str(e)}")
        if not dissertation_analyzer.is_connection_closed:
            await dissertation_analyzer.safe_send(websocket, {
                "type": "error",
                "data": {"message": str(e)}
            })
    finally:
        if not dissertation_analyzer.is_connection_closed:
            await websocket.close()

####################################################################################
###########################analysis_algorithms.py endpoints end#####################
####################################################################################





####################################################################################
###########################data_preprocessing.py endpoints start####################
####################################################################################
# Endpoint to chunk text into semantic pieces
# -----------------------------------------
# Description:
# This endpoint splits input text into semantic chunks using LangChain's
# RecursiveCharacterTextSplitter while preserving context.
#
# Request Body:
# {
#     "text": "Your long text here...",
#     "chunk_size": 1000  // optional, defaults to 1000
# }
#
# Response:
# {
#     "chunks": [
#         ["chunk text here...", 995],
#         ["next chunk text...", 1002],
#         ...
#     ]
# }
@app.post("/api/chunk-text", response_model=ChunkResponse)
async def chunk_text_endpoint(request: TextChunkRequest):
    try:
        chunks = data_preprocessing.chunk_text(
            text=request.text,
            chunk_size=request.chunk_size
        )
        return {"chunks": chunks}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error chunking text: {str(e)}"
        )

# Endpoint to get first N words from text
# -------------------------------------
# Description:
# This endpoint extracts the first N words from the input text.
#
# Request Body:
# {
#     "text": "Your text here...",
#     "n": 500
# }
#
# Response:
# {
#     "text": "First N words...",
#     "word_count": 500
# }
@app.post("/api/get-first-n-words", response_model=FirstNWordsResponse)
async def get_first_n_words_endpoint(request: FirstNWordsRequest):
    try:
        result = data_preprocessing.get_first_n_words(
            text=request.text,
            n=request.n
        )
        return {
            "text": result,
            "word_count": len(result.split())
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting first N words: {str(e)}"
        )
####################################################################################
###########################inference_client.py endpoints end########################
####################################################################################






####################################################################################
###########################nlp_utils.py endpoints start#############################
####################################################################################

####################################################################################
###########################nlp_utils.py endpoints end###############################
####################################################################################





####################################################################################
###########################business_logic.py endpoints start########################
####################################################################################


# Endpoint to process PDF files
# ----------------------------
# Description:
# This endpoint processes PDF files, extracting both text and images.
# Images are analyzed starting from page 7, and the output preserves
# the original sequence of text and images.
#
# Request:
# Multipart form data with a PDF file
#
# Response:
# {
#     "text_and_image_analysis": "Combined text and image analysis..."
# }
@app.post("/api/process-pdf")
async def process_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to process")
):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF files are accepted."
            )

        result = await business_logic.process_pdf(file)
        return JSONResponse(content=result)
    
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF file: {str(e)}"
        )
    finally:
        await file.close()

# Endpoint to process DOCX files
# -----------------------------
# Description:
# This endpoint processes DOCX files, extracting both text and images.
# Images are processed in batches for efficient analysis.
#
# Request:
# Multipart form data with a DOCX file
#
# Response:
# {
#     "text": "Extracted text content...",
#     "image_analyses": {
#         "1": "First image analysis",
#         "2": "Second image analysis",
#         ...
#     }
# }
@app.post("/api/process-docx")
async def process_docx_endpoint(
    file: UploadFile = File(..., description="DOCX file to process")
):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.docx'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only DOCX files are accepted."
            )

        result = await business_logic.process_docx(file)
        return JSONResponse(content=result)
    
    except Exception as e:
        logging.error(f"Error processing DOCX: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing DOCX file: {str(e)}"
        )
    finally:
        await file.close()

# Endpoint to process multiple images in batches
# ---------------------------------------------
# Description:
# This endpoint processes multiple images concurrently in batches, applying resizing
# and analysis to each image. It maintains the order of images using page/image numbers.
#
# Request Body:
# {
#     "images_data": [(page_number, image_bytes), ...],
#     "batch_size": 5  # optional, defaults to 5
# }
#
# Response:
# {
#     "results": {
#         "1": "Analysis result for image 1",
#         "2": "Analysis result for image 2",
#         ...
#     }
# }
@app.post("/api/process-images-batch")
async def process_images_batch_endpoint(request: BatchImageProcessingRequest):
    try:
        results = await business_logic.process_images_in_batch(
            images_data=request.images_data,
            batch_size=request.batch_size
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to analyze an image
# ----------------------------
# Description:
# This endpoint processes an image and analyzes its content using either VLLM or Ollama, 
# depending on the available configuration. VLLM is used by default if both services are set up.
#
# Request:
# The request body should contain raw image data in bytes format.
#
# Example Request:
# Content-Type: application/octet-stream
# <binary image data>
#
# Response:
# {
#     "response": "<Analysis result>"
# }
@app.post("/api/analyze-image")
async def analyze_image_endpoint(image_data: bytes = Body(..., media_type="application/octet-stream")):
    try:
        result = await business_logic.analyze_image(image_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to extract the topic from the first few pages of a document
# Request Body: DocumentText containing the text of the document
# Response: JSON containing the extracted topic
@app.post("/api/extract-topic-from-first-few-pages-of-a-document")
async def extract_topic(data: DocumentText):
    try:
        topic = await business_logic.extract_topic_agent(data.document_text)
        return {"topic": topic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to extract the degree information from the first few pages of a document
# Request Body: DocumentText containing the text of the document
# Response: JSON containing the extracted degree information
@app.post("/api/extract-degree-from-first-few-pages-of-a-document")
async def extract_degree(data: DocumentText):
    try:
        degree = await business_logic.extract_degree_agent(data.document_text)
        return {"degree": degree}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to extract the author's name from the first few pages of a document
# Request Body: DocumentText containing the text of the document
# Response: JSON containing the extracted name
@app.post("/api/extract-name-from-first-few-pages-of-a-document")
async def extract_name(data: DocumentText):
    try:
        name = await business_logic.extract_name_agent(data.document_text)
        return {"name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to summarize and analyze large documents
# Request Body: DocumentText containing the text of the thesis
# Response: JSON containing the summarized and analyzed content
@app.post("/api/summarize-and-analyze-large-documents")
async def summarize_and_analyze(request: DocumentText):
    try:
        summary = await business_logic.summarize_and_analyze_agent(
            thesis=request.document_text
        )
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to process and summarize document chunks in batches
# Request Body: ChunkSummarizationProcessingRequest containing chunks, system prompt, and batch size
# Response: JSON containing summarized chunks
@app.post("/api/process-chunks")
async def process_chunks(request: ChunkSummarizationProcessingRequest):
    try:
        summarized_chunks = await business_logic.process_chunks_in_batch(
            chunks=request.chunks,
            system_prompt=request.system_prompt,
            batch_size=request.batch_size
        )
        return {"summarized_chunks": summarized_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to score a criterion based on analysis
# ------------------------------------------------
# Description:
# This endpoint evaluates a specific dissertation criterion using a scoring agent.
# It processes the provided analysis, scoring guidelines, and expert feedback to generate a score.
#
# Request Body (ScoringRequest):
# {
#     "analysis": "The thesis lacks coherence in its argument structure.",
#     "criteria": "Clarity of Argument",
#     "score_guidelines": "0 - Poor, 5 - Excellent",
#     "criteria_guidelines": "A clear and logically structured argument is required.",
#     "feedback": "Consider improving the logical flow of arguments."
# }
#
# Response:
# {
#     "spanda_score": "spanda_score: 3"
# }
@app.post("/api/score-criteria")
async def score_criteria(request: ScoringRequest):
    try:
        score = await business_logic.scoring_agent(
            request.analysis,
            request.criteria,
            request.score_guidelines,
            request.criteria_guidelines,
            request.feedback
        )
        return {"spanda_score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to process initial agents (extract topic, degree, and name)
# --------------------------------------------------------------------
# Description:
# This endpoint concurrently extracts the research topic, degree information, and author's name 
# from the first few pages of the document
async def process_initial_agents(request: DocumentText):
    try:
        results = await business_logic.process_initial_agents(request.document_text)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


####################################################################################
###########################business_logic.py endpoints end##########################
####################################################################################

# Main function to start the FastAPI server
def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)


if __name__ == "__main__":
    main()
