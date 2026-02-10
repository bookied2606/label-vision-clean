#!/usr/bin/env python
"""Debug OCR to see what text is being extracted"""
import os
import pytesseract
from PIL import Image
import cv2
import numpy as np

# Set Tesseract path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Get the latest captured image
uploads_dir = r"c:\Users\User\Downloads\label-vision-clean\backend\uploads"

# Get all jpg files, sorted by date (most recent first)
jpg_files = sorted(
    [f for f in os.listdir(uploads_dir) if f.endswith('.jpg')],
    key=lambda f: os.path.getmtime(os.path.join(uploads_dir, f)),
    reverse=True
)

if not jpg_files:
    print("No captured images found!")
    exit(1)

# Get the most recent front image
front_files = [f for f in jpg_files if '_front' in f]
if not front_files:
    print("No front images found!")
    exit(1)

latest_front = front_files[0]
image_path = os.path.join(uploads_dir, latest_front)

print(f"Analyzing: {latest_front}")
print(f"Full path: {image_path}")
print(f"File size: {os.path.getsize(image_path)} bytes")
print()

# Load image
img = Image.open(image_path)
print(f"Image dimensions: {img.size} (width x height)")
print(f"Image mode: {img.mode}")
print()

# Convert to numpy
img_array = np.array(img)

# Preprocess like the backend does
print("Preprocessing image (same as backend)...")
gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(gray)

# Try PSM 6 (what backend uses first)
print("\nTrying PSM 6 (Block of text mode)...")
config_6 = r'--psm 6 --oem 3'
text_6 = pytesseract.image_to_string(Image.fromarray(enhanced), config=config_6)
text_6 = text_6.strip()

print(f"Characters extracted: {len(text_6)}")
if text_6:
    print(f"\nExtracted Text:\n---")
    print(text_6)
    print("---")
    
    # Count words
    words = [w for w in text_6.split() if w]
    print(f"\nWord count: {len(words)}")
    
    # Show first 5 words
    if words:
        print(f"First words: {', '.join(words[:10])}")
else:
    print("NO TEXT EXTRACTED - Image might be:")
    print("  - Blurry or out of focus")
    print("  - Too dark (poor lighting)")
    print("  - Label not visible in frame")
    print("  - At an angle")
    print()
    print("RECOMMENDATION: Try capturing again with:")
    print("  1. Better lighting")
    print("  2. Camera held steady")
    print("  3. Label filling the blue frame")
    print("  4. Text clearly visible to human eye")

print()
print("=" * 50)

# Also try PSM 3
print("\nTrying PSM 3 (Automatic segmentation)...")
config_3 = r'--psm 3 --oem 3'
text_3 = pytesseract.image_to_string(Image.fromarray(enhanced), config=config_3)
text_3 = text_3.strip()

print(f"Characters extracted: {len(text_3)}")
if text_3:
    print(f"\nExtracted Text:\n---")
    print(text_3[:300])  # First 300 chars
    if len(text_3) > 300:
        print(f"... ({len(text_3) - 300} more characters)")
    print("---")
