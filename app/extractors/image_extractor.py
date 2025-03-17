import os
import logging
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

def enhance_image(image):
    """
    Enhance image for better OCR results
    
    Args:
        image: PIL Image object
        
    Returns:
        Enhanced PIL Image object
    """
    # Convert to grayscale
    image = image.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Apply slight blur to reduce noise
    image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Apply threshold to make text more distinct
    threshold = 150
    image = image.point(lambda p: 255 if p > threshold else 0)
    
    return image

def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from image files using OCR
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Extracted text from the image
    """
    try:
        logger.info(f"Extracting text from image: {file_path}")
        
        # Open the image
        with Image.open(file_path) as img:
            # Enhance image for better OCR results
            enhanced_img = enhance_image(img)
            
            # Run OCR on the image
            text = pytesseract.image_to_string(enhanced_img)
            
            # Alternative OCR with different settings if little text was found
            if len(text.strip()) < 50:
                logger.info("Limited text found, trying different OCR settings")
                
                # Try different configurations
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(enhanced_img, config=custom_config)
                
                # If still little text, try with original image
                if len(text.strip()) < 50:
                    logger.info("Still limited text, trying original image")
                    text = pytesseract.image_to_string(img)
            
            return text.strip()
    
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return ""