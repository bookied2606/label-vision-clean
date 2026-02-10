#!/usr/bin/env python
"""Test OCR on actual captured images"""
import pytesseract
from PIL import Image
import cv2
import numpy as np
import os

# Set Tesseract path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Test with newest image
image_path = r"c:\Users\User\Downloads\label-vision-clean\backend\uploads\d5b8b6d7_front.jpg"

if os.path.exists(image_path):
    print(f"Testing OCR on: {image_path}")
    print(f"File size: {os.path.getsize(image_path)} bytes")
    
    # Load image
    img = Image.open(image_path)
    print(f"Image size: {img.size}")
    print(f"Image mode: {img.mode}")
    
    # Convert to numpy for analysis
    img_array = np.array(img)
    print(f"Array shape: {img_array.shape}")
    
    # Try OCR without preprocessing
    print("\n1. Testing raw OCR...")
    text1 = pytesseract.image_to_string(img)
    print(f"   Result length: {len(text1)} chars")
    if text1.strip():
        print(f"   Text: {text1[:200]}")
    else:
        print("   ❌ No text extracted")
    
    # Convert to grayscale
    print("\n2. Testing with grayscale conversion...")
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray_img = Image.fromarray(gray)
    text2 = pytesseract.image_to_string(gray_img)
    print(f"   Result length: {len(text2)} chars")
    if text2.strip():
        print(f"   Text: {text2[:200]}")
    else:
        print("   ❌ No text extracted")
    
    # Try with contrast enhancement
    print("\n3. Testing with contrast enhancement...")
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    enhanced_img = Image.fromarray(enhanced)
    text3 = pytesseract.image_to_string(enhanced_img)
    print(f"   Result length: {len(text3)} chars")
    if text3.strip():
        print(f"   Text: {text3[:200]}")
    else:
        print("   ❌ No text extracted")
    
    # Try with binary threshold
    print("\n4. Testing with binary threshold...")
    _, binary = cv2.threshold(enhanced, 150, 255, cv2.THRESH_BINARY)
    binary_img = Image.fromarray(binary)
    text4 = pytesseract.image_to_string(binary_img)
    print(f"   Result length: {len(text4)} chars")
    if text4.strip():
        print(f"   Text: {text4[:200]}")
    else:
        print("   ❌ No text extracted")
    
    # Try different PSM modes
    print("\n5. Testing different PSM modes...")
    for psm in [3, 6, 11]:
        config = f'--psm {psm} --oem 3'
        text = pytesseract.image_to_string(img, config=config)
        print(f"   PSM {psm}: {len(text)} chars")
        if text.strip():
            print(f"      Text: {text[:100]}")
    
else:
    print(f"Image not found: {image_path}")
