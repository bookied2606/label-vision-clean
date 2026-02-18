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

    def is_valid_text(self, text: str) -> bool:
        """
        STRICT English validation.
        Rejects anything that looks remotely like gibberish.
        """
        if not text or len(text.strip()) < 8:
            return False
        
        text_clean = text.strip()
        
        # Count character types
        letters = sum(c.isalpha() for c in text_clean)
        digits = sum(c.isdigit() for c in text_clean)
        spaces = sum(c.isspace() for c in text_clean)
        special = sum(not c.isalnum() and not c.isspace() for c in text_clean)
        total = len(text_clean)
        
        letter_ratio = letters / total
        special_ratio = special / total
        
        # STRICT requirements:
        # 1. Must be 70%+ letters/numbers/spaces (not special chars)
        # 2. Must be 55%+ actual letters (not numbers)
        # 3. Max 20% special characters
        
        if letter_ratio < 0.55:
            print(f"❌ Only {letter_ratio:.0%} letters - TOO MUCH GIBBERISH")
            return False
        
        if special_ratio > 0.20:
            print(f"❌ Too many special chars ({special_ratio:.0%}) - GIBBERISH")
            return False
        
        # Check for common gibberish patterns (too many repeated chars, no spaces in long text)
        if len(text_clean) > 40 and spaces < 2:
            print(f"❌ Long text with no spaces - GIBBERISH")
            return False
        
        # Count consecutive non-ASCII or weird characters
        weird_chars = sum(1 for c in text_clean if ord(c) > 127 or c in '¢øå')
        if weird_chars > total * 0.05:
            print(f"❌ Has weird/special symbols - GIBBERISH")
            return False
        
        print(f"✅ VALID English ({letter_ratio:.0%} letters, {special_ratio:.0%} special)")
        return True

    def preprocess_image(self, image_input: Union[bytes, np.ndarray]) -> Image.Image:
        """
        Simple preprocessing for better OCR.
        Not too aggressive - preserve clear text.
        """
        if isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input))
        else:
            image = Image.fromarray(image_input)

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to numpy for processing
        img_array = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Light denoising (don't be too aggressive)
        denoised = cv2.bilateralFilter(gray, 5, 50, 50)
        
        # Moderate contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Auto scale if too small
        height, width = enhanced.shape[:2]
        if width < 300:
            scale = 300 / width if width > 0 else 1
            new_w = int(width * scale)
            new_h = int(height * scale)
            enhanced = cv2.resize(enhanced, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            print(f"📏 Upscaled to {new_w}x{new_h}")
        
        return Image.fromarray(enhanced)

    def extract_text(self, image_bytes: bytes) -> str:
        """Extract English text only. Simple and strict."""
        try:
            print("📸 Starting OCR (English only)...")
            image = self.preprocess_image(image_bytes)
            
            # Try PSM 6 first (block of text) with ENGLISH ONLY
            print("🔍 Trying PSM 6 (English block)...")
            text = pytesseract.image_to_string(image, config=r'--psm 6 --oem 3 -l eng')
            text = text.strip()
            
            if text and len(text) > 5 and self.is_valid_text(text):
                print(f"✅ Success! Extracted {len(text)} chars")
                return text
            
            # Try PSM 13 (sparse English text)
            print("🔍 Trying PSM 13 (sparse English)...")
            text = pytesseract.image_to_string(image, config=r'--psm 13 --oem 3 -l eng')
            text = text.strip()
            
            if text and len(text) > 5 and self.is_valid_text(text):
                print(f"✅ Success! Extracted {len(text)} chars")
                return text
            
            # Try PSM 3 (auto segment, English)
            print("🔍 Trying PSM 3 (auto segment English)...")
            text = pytesseract.image_to_string(image, config=r'--psm 3 --oem 3 -l eng')
            text = text.strip()
            
            if text and len(text) > 5 and self.is_valid_text(text):
                print(f"✅ Success! Extracted {len(text)} chars")
                return text
            
            print("❌ Could not extract valid English text")
            return ""
                    
        except Exception as e:
            print(f"❌ OCR failed: {e}")
            raise RuntimeError(f"OCR extraction failed: {e}")

    def extract_text_from_array(self, image_array: np.ndarray) -> str:
        """Extract text from numpy array."""
        try:
            image = self.preprocess_image(image_array)
            text = pytesseract.image_to_string(image, config=self.config)
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {e}")
