import os
import logging
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import tempfile

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF files, including scanned PDFs using OCR
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    # First try to extract text directly from PDF
    extracted_text = ""
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text.strip():
                    extracted_text += page_text + "\n\n"
    
    except Exception as e:
        logger.error(f"Error extracting text with PyPDF2: {str(e)}")
    
    # If little or no text was extracted, it might be a scanned PDF
    # Try OCR in that case
    if len(extracted_text.strip()) < 100:
        logger.info("Limited text extracted, trying OCR for possibly scanned PDF")
        ocr_text = extract_text_with_ocr(file_path)
        
        # If OCR extracted more text, use that instead
        if len(ocr_text.strip()) > len(extracted_text.strip()):
            extracted_text = ocr_text
    
    return extracted_text.strip()

def extract_text_with_ocr(file_path: str) -> str:
    """
    Extract text from PDF using OCR
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        OCR extracted text
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Converting PDF to images for OCR")
            # Convert PDF to images
            images = convert_from_path(file_path, output_folder=temp_dir)
            
            # Extract text from each image
            text = ""
            for i, image in enumerate(images):
                logger.info(f"Running OCR on page {i+1}")
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n\n"
            
            return text
    
    except Exception as e:
        logger.error(f"Error during OCR text extraction: {str(e)}")
        return ""