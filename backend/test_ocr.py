#!/usr/bin/env python
"""Debug OCR to see what's failing"""
import pytesseract
from PIL import Image
import cv2
import numpy as np

# Test Tesseract installation
print("Testing Tesseract OCR...")

# Set Tesseract path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract found: {version}")
except Exception as e:
    print(f"❌ Tesseract error: {e}")
    exit(1)

# Test with a simple image
print("\nCreating test image...")
test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255  # White background
cv2.putText(test_img, "HELLO WORLD TEST", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

# Test OCR
print("Running OCR on test image...")
text = pytesseract.image_to_string(test_img)
print(f"OCR Result: '{text}'")

if text.strip():
    print("✅ OCR is working!")
else:
    print("❌ OCR returned empty text")
    
# Test with preprocessing
print("\nTesting with preprocessing...")
gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
text2 = pytesseract.image_to_string(binary)
print(f"OCR Result (preprocessed): '{text2}'")

if text2.strip():
    print("✅ Preprocessing helps!")
else:
    print("❌ Still empty even with preprocessing")
