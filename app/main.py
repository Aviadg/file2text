import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Security, Depends, Query
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.responses import JSONResponse
from typing import List, Optional, Literal
import logging
import mimetypes
from extractors.pdf_extractor import extract_text_from_pdf
from extractors.doc_extractor import extract_text_from_doc
from extractors.image_extractor import extract_text_from_image
from extractors.docling_extractor import DoclingExtractor
from pydantic import BaseModel
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Text Extraction API",
    description="API for extracting text from various document formats using Docling",
    version="2.0.0",
)

# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Get API key from environment variable
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403,
        detail="Invalid API Key"
    )

# Ensure upload directory exists
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize DoclingExtractor
docling_extractor = DoclingExtractor()

# Define models for base64 data
class Base64FileData(BaseModel):
    filename: str
    content_type: str
    base64_data: str

class BatchBase64Data(BaseModel):
    files: List[Base64FileData]

def get_file_type(filename: str) -> str:
    """Determine file type based on extension"""
    extension = os.path.splitext(filename)[1].lower()
    
    if extension in ['.pdf']:
        return 'pdf'
    elif extension in ['.doc', '.docx']:
        return 'doc'
    elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']:
        return 'image'
    elif extension in ['.xlsx', '.xls']:
        return 'excel'
    elif extension in ['.pptx', '.ppt']:
        return 'powerpoint'
    elif extension in ['.html', '.htm']:
        return 'html'
    elif extension in ['.txt', '.md']:
        return 'text'
    else:
        return 'unknown'

async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to disk and return the file path"""
    file_id = uuid.uuid4().hex
    file_extension = os.path.splitext(upload_file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
    
    # Write the file to disk
    with open(file_path, "wb") as f:
        content = await upload_file.read()
        f.write(content)
    
    return file_path, content

@app.post("/extract-text/", response_class=JSONResponse)
async def extract_text(
    file: UploadFile = File(...),
    api_key: APIKey = Depends(get_api_key),
    backend: Optional[Literal["docling", "legacy"]] = Query("docling", description="Extraction backend to use")
):
    """
    Extract text from the uploaded file
    """
    logger.info(f"Received file: {file.filename}, using backend: {backend}")
    
    try:
        # Save the uploaded file
        file_path, file_content = await save_upload_file(file)
        file_type = get_file_type(file.filename)
        
        # Extract text based on backend choice
        if backend == "docling":
            # Use Docling for extraction
            text = docling_extractor.extract_text(file_path)
        else:
            # Use legacy backend
            if file_type == 'pdf':
                text = extract_text_from_pdf(file_path)
            elif file_type == 'doc':
                text = extract_text_from_doc(file_path)
            elif file_type == 'image':
                text = extract_text_from_image(file_path)
            else:
                raise HTTPException(status_code=400, detail=f"Legacy backend doesn't support file type: {file.filename}")
        
        # Clean up - remove the temporary file
        os.remove(file_path)
        
        return {
            "filename": file.filename,
            "text": text,
            "file_type": file_type,
            "backend": backend
        }
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/extract-text-legacy/", response_class=JSONResponse)
async def extract_text_legacy(
    file: UploadFile = File(...),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Extract text from the uploaded file using legacy extractors
    """
    logger.info(f"Received file for legacy extraction: {file.filename}")
    
    try:
        # Save the uploaded file
        file_path, _ = await save_upload_file(file)
        file_type = get_file_type(file.filename)
        
        # Extract text based on file type using legacy extractors
        if file_type == 'pdf':
            text = extract_text_from_pdf(file_path)
        elif file_type == 'doc':
            text = extract_text_from_doc(file_path)
        elif file_type == 'image':
            text = extract_text_from_image(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
        
        # Clean up - remove the temporary file
        os.remove(file_path)
        
        return {
            "filename": file.filename,
            "text": text,
            "file_type": file_type,
            "backend": "legacy"
        }
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/extract-text-base64/", response_class=JSONResponse)
async def extract_text_base64(
    file_data: Base64FileData,
    api_key: APIKey = Depends(get_api_key),
    backend: Optional[Literal["docling", "legacy"]] = Query("docling", description="Extraction backend to use")
):
    """
    Extract text from base64-encoded file data
    """
    logger.info(f"Received base64 data for file: {file_data.filename}, using backend: {backend}")
    
    try:
        # Decode base64 data
        file_content = base64.b64decode(file_data.base64_data)
        
        # Save to temporary file
        file_id = uuid.uuid4().hex
        file_extension = os.path.splitext(file_data.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Determine file type
        file_type = get_file_type(file_data.filename)
        
        # Extract text based on backend choice
        if backend == "docling":
            # Use Docling for extraction
            text = docling_extractor.extract_text_from_bytes(file_content, file_data.filename)
        else:
            # Use legacy backend
            if file_type == 'pdf':
                text = extract_text_from_pdf(file_path)
            elif file_type == 'doc':
                text = extract_text_from_doc(file_path)
            elif file_type == 'image':
                text = extract_text_from_image(file_path)
            else:
                raise HTTPException(status_code=400, detail=f"Legacy backend doesn't support file type: {file_data.filename}")
        
        # Clean up temporary file
        os.remove(file_path)
        
        return {
            "filename": file_data.filename,
            "text": text,
            "file_type": file_type,
            "backend": backend
        }
        
    except Exception as e:
        logger.error(f"Error processing base64 data for file {file_data.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/extract-text-base64-legacy/", response_class=JSONResponse)
async def extract_text_base64_legacy(
    file_data: Base64FileData,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Extract text from base64-encoded file data using legacy extractors
    """
    logger.info(f"Received base64 data for legacy extraction: {file_data.filename}")
    
    try:
        # Decode base64 data
        file_content = base64.b64decode(file_data.base64_data)
        
        # Save to temporary file
        file_id = uuid.uuid4().hex
        file_extension = os.path.splitext(file_data.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Determine file type and extract text
        file_type = get_file_type(file_data.filename)
        
        if file_type == 'pdf':
            text = extract_text_from_pdf(file_path)
        elif file_type == 'doc':
            text = extract_text_from_doc(file_path)
        elif file_type == 'image':
            text = extract_text_from_image(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_data.filename}")
        
        # Clean up temporary file
        os.remove(file_path)
        
        return {
            "filename": file_data.filename,
            "text": text,
            "file_type": file_type,
            "backend": "legacy"
        }
        
    except Exception as e:
        logger.error(f"Error processing base64 data for file {file_data.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/batch-extract/", response_class=JSONResponse)
async def batch_extract_text(
    files: List[UploadFile] = File(...),
    api_key: APIKey = Depends(get_api_key),
    backend: Optional[Literal["docling", "legacy"]] = Query("docling", description="Extraction backend to use")
):
    """
    Extract text from multiple uploaded files
    """
    results = []
    
    for file in files:
        try:
            # Save the uploaded file
            file_path, file_content = await save_upload_file(file)
            file_type = get_file_type(file.filename)
            
            # Extract text based on backend choice
            if backend == "docling":
                # Use Docling for extraction
                text = docling_extractor.extract_text(file_path)
            else:
                # Use legacy backend
                if file_type == 'pdf':
                    text = extract_text_from_pdf(file_path)
                elif file_type == 'doc':
                    text = extract_text_from_doc(file_path)
                elif file_type == 'image':
                    text = extract_text_from_image(file_path)
                else:
                    text = f"Legacy backend doesn't support file type: {file.filename}"
            
            # Clean up - remove the temporary file
            os.remove(file_path)
            
            results.append({
                "filename": file.filename,
                "text": text,
                "file_type": file_type,
                "status": "success",
                "backend": backend
            })
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "error",
                "backend": backend
            })
    
    return {"results": results}

@app.post("/batch-extract-legacy/", response_class=JSONResponse)
async def batch_extract_text_legacy(
    files: List[UploadFile] = File(...),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Extract text from multiple uploaded files using legacy extractors
    """
    results = []
    
    for file in files:
        try:
            # Save the uploaded file
            file_path, _ = await save_upload_file(file)
            file_type = get_file_type(file.filename)
            
            # Extract text based on file type
            if file_type == 'pdf':
                text = extract_text_from_pdf(file_path)
            elif file_type == 'doc':
                text = extract_text_from_doc(file_path)
            elif file_type == 'image':
                text = extract_text_from_image(file_path)
            else:
                text = f"Unsupported file type: {file.filename}"
            
            # Clean up - remove the temporary file
            os.remove(file_path)
            
            results.append({
                "filename": file.filename,
                "text": text,
                "file_type": file_type,
                "status": "success",
                "backend": "legacy"
            })
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "error",
                "backend": "legacy"
            })
    
    return {"results": results}

@app.get("/")
async def read_root(api_key: APIKey = Depends(get_api_key)):
    return {
        "message": "Text Extraction API is running with Docling backend. Use /extract-text/, /extract-text-base64/ or /batch-extract/ endpoints. Legacy endpoints are available with -legacy suffix."
    }