import os
import logging
import tempfile
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat, DocumentStream
from io import BytesIO

logger = logging.getLogger(__name__)

class DoclingExtractor:
    """
    Extract text from documents using Docling
    """
    def __init__(self):
        self.converter = DocumentConverter()
        logger.info("Initialized Docling document converter")
        
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a file using Docling
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text from the document
        """
        try:
            logger.info(f"Extracting text with Docling: {file_path}")
            
            # Convert the document
            result = self.converter.convert(file_path)
            
            # Check if conversion was successful
            if result.status.is_error():
                logger.error(f"Docling conversion error: {result.status.message}")
                return ""
                
            # Export to text
            extracted_text = result.document.export_to_markdown()
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text with Docling: {str(e)}")
            return ""
            
    def extract_text_from_bytes(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from file bytes using Docling
        
        Args:
            file_content: Binary content of the file
            filename: Name of the file (with extension)
            
        Returns:
            Extracted text from the document
        """
        try:
            logger.info(f"Extracting text with Docling from bytes: {filename}")
            
            # Create BytesIO object from file content
            buf = BytesIO(file_content)
            
            # Create DocumentStream
            source = DocumentStream(name=filename, stream=buf)
            
            # Convert the document
            result = self.converter.convert(source)
            
            # Check if conversion was successful
            if result.status.is_error():
                logger.error(f"Docling conversion error: {result.status.message}")
                return ""
                
            # Export to text
            extracted_text = result.document.export_to_markdown()
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text with Docling from bytes: {str(e)}")
            return ""