"""
Parser Agent: Extracts text from PDF and image files.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ParserAgent:
    """Agent responsible for parsing lab reports from PDF and image files."""
    
    def __init__(self):
        """Initialize parser agent."""
        self.supported_formats = ['.pdf', '.jpg', '.jpeg', '.png']
    
    def parse(self, file_path: str, file_extension: str) -> Optional[str]:
        """
        Parse file and extract text.
        
        Args:
            file_path: Path to the file
            file_extension: File extension (e.g., '.pdf', '.jpg')
            
        Returns:
            Extracted text as string, or None if parsing fails
        """
        try:
            ext = file_extension.lower()
            
            if ext == '.pdf':
                return self._parse_pdf(file_path)
            elif ext in ['.jpg', '.jpeg', '.png']:
                return self._parse_image(file_path)
            else:
                logger.error(f"Unsupported file format: {ext}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            return None
    
    def _parse_pdf(self, file_path: str) -> str:
        """Parse PDF file using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            doc = fitz.open(file_path)
            text_parts = []
            
            if len(doc) == 0:
                doc.close()
                raise ValueError("PDF file appears to be empty or corrupted")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():  # Only add non-empty pages
                    text_parts.append(text)
            
            doc.close()
            
            if not text_parts:
                raise ValueError("No text could be extracted from PDF. The PDF might be image-based or corrupted.")
            
            extracted_text = '\n\n'.join(text_parts)
            
            if len(extracted_text.strip()) < 10:
                raise ValueError("Extracted text is too short. PDF might be image-based - try converting to image first.")
            
            return extracted_text
            
        except ImportError:
            logger.error("PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF")
            raise
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise
    
    def _parse_image(self, file_path: str) -> str:
        """Parse image file using Tesseract OCR."""
        try:
            from PIL import Image
            import pytesseract
            
            # Open image
            image = Image.open(file_path)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image, lang='eng')
            
            return text
            
        except ImportError:
            logger.error("Tesseract or PIL not installed. Install with: pip install pytesseract pillow")
            raise
        except Exception as e:
            logger.error(f"Error parsing image: {str(e)}")
            raise
