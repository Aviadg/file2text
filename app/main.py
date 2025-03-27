import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import mimetypes
from extractors.pdf_extractor import extract_text_from_pdf
from extractors.doc_extractor import extract_text_from_doc
from extractors.image_extractor import extract_text_from_image
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
    description="API for extracting text from various document formats",
    version="1.0.0",
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

# Define models for base64 data
class Base64FileData(BaseModel):
    filename: str
    content_type: str
    base64_data: str

class BatchBase64Data(BaseModel):
    files: List[Base64FileData]

@app.post("/extract-text-base64/", response_class=JSONResponse)
async def extract_text_base64(
    file_data: Base64FileData,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Extract text from base64-encoded file data
    """
    logger.info(f"Received base64 data for file: {file_data.filename}")
    
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
            "file_type": file_type
        }
        
    except Exception as e:
        logger.error(f"Error processing base64 data for file {file_data.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

def get_file_type(filename: str) -> str:
    """Determine file type based on extension"""
    extension = os.path.splitext(filename)[1].lower()
    
    if extension in ['.pdf']:
        return 'pdf'
    elif extension in ['.doc', '.docx']:
        return 'doc'
    elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']:
        return 'image'
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
    
    return file_path

@app.post("/extract-text/", response_class=JSONResponse)
async def extract_text(
    file: UploadFile = File(...),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Extract text from the uploaded file
    """
    logger.info(f"Received file: {file.filename}")
    
    try:
        # Save the uploaded file
        file_path = await save_upload_file(file)
        file_type = get_file_type(file.filename)
        
        # Extract text based on file type
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
            "file_type": file_type
        }
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/batch-extract/", response_class=JSONResponse)
async def batch_extract_text(
    files: List[UploadFile] = File(...),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Extract text from multiple uploaded files
    """
    results = []
    
    for file in files:
        try:
            # Save the uploaded file
            file_path = await save_upload_file(file)
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
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "error"
            })
    
    return {"results": results}

@app.get("/")
async def read_root(api_key: APIKey = Depends(get_api_key)):
    return {"message": "Text Extraction API is running. Use /extract-text/, /extract-text-base64/ or /batch-extract/ endpoints."}