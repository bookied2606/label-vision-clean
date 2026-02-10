import os
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from typing import Union

load_dotenv()

class SimpleOCRClient:
    def __init__(self):
        # Tell pytesseract exactly where Tesseract is installed
        self.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        # Tesseract config for product labels
        # PSM 3 = Fully automatic page segmentation
        # OEM 3 = Legacy + LSTM mode
        self.config = r'--psm 3 --oem 3'
        
        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
            print("✅ Tesseract OCR is available")
        except Exception as e:
            print(f"⚠️ Tesseract not found at {self.tesseract_cmd}: {e}")

    def preprocess_image(self, image_input: Union[bytes, np.ndarray]) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy:
        - Convert to grayscale (best for OCR)
        - Enhance contrast using CLAHE
        - Resize if needed
        """
        if isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input))
        else:
            image = Image.fromarray(image_input)

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert PIL to numpy for preprocessing
        img_array = np.array(image)
        
        # Convert to grayscale (better for OCR than binary)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Resize if image is very large (improves speed without losing quality)
        height, width = enhanced.shape[:2]
        max_width = 2000
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"📏 Resized large image to {new_width}x{new_height}")
        
        # Convert back to PIL Image
        result = Image.fromarray(enhanced)
        return result

    def extract_text(self, image_bytes: bytes) -> str:
        """Extract text from image bytes with multiple fallbacks."""
        try:
            print("📸 Starting OCR extraction...")
            image = self.preprocess_image(image_bytes)
            
            # Try PSM 6 first (Assume single block of text) - better for labels
            print("🔍 Trying PSM 6 (block of text)...")
            config_6 = r'--psm 6 --oem 3'
            text = pytesseract.image_to_string(image, config=config_6)
            text = text.strip()
            
            if text and len(text) > 10:
                print(f"✅ OCR extracted {len(text)} chars with PSM 6")
                return text
            
            # Fallback to PSM 3 if PSM 6 didn't work well
            print("🔍 Fallback to PSM 3 (automatic segmentation)...")
            config_3 = r'--psm 3 --oem 3'
            text = pytesseract.image_to_string(image, config=config_3)
            text = text.strip()
            
            if text and len(text) > 10:
                print(f"✅ OCR extracted {len(text)} chars with PSM 3")
                return text
            
            # Last resort: try PSM 11 (sparse text)
            if not text or len(text) < 10:
                print("🔍 Last resort PSM 11 (sparse text)...")
                config_11 = r'--psm 11 --oem 3'
                text = pytesseract.image_to_string(image, config=config_11)
                text = text.strip()
            
            if text:
                print(f"✅ OCR extracted {len(text)} chars")
                return text
            else:
                print("⚠️ No text extracted from image")
                return ""
                    
        except Exception as e:
            print(f"❌ OCR extraction failed: {e}")
            raise RuntimeError(f"OCR extraction failed: {e}")

    def extract_text_from_array(self, image_array: np.ndarray) -> str:
        """Extract text from numpy array."""
        try:
            image = self.preprocess_image(image_array)
            text = pytesseract.image_to_string(image, config=self.config)
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {e}")
