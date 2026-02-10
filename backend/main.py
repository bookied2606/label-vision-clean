import os
import uuid
import logging
import io
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import httpx
from PIL import Image
import numpy as np
import json

from database import get_db, engine, Base
from models import ScanHistory
from services.ocr import SimpleOCRClient
from services.extract import extract_from_pipeline

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="LabelVision Backend",
    description="Direct OCR for product labels (Simple)",
    version="3.0.0",
)

# CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# OCR client (singleton)
ocr_client = SimpleOCRClient()

# Helper: generate short UUID
def short_id() -> str:
    return str(uuid.uuid4())[:8]

# Helper: save uploaded image to disk
def save_image(file_bytes: bytes, scan_id: str, side: str) -> str:
    """Save image to disk, return relative path. side: 'front' or 'back'"""
    os.makedirs("uploads", exist_ok=True)
    filename = f"{scan_id}_{side}.jpg"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return filepath

# Helper: merge OCR results from front and back
def merge_ocr_results(front_text: str, back_text: str, front_extraction: dict, back_extraction: dict) -> dict:
    """
    Intelligently merge extraction results from front and back sides.
    Front: typically has product name, brand
    Back: typically has ingredients, warnings, expiry date
    """
    merged = {}
    
    # Priority: front for name/brand, back for expiry/ingredients
    merged["product_name"] = front_extraction.get("product_name") or back_extraction.get("product_name")
    merged["brand"] = front_extraction.get("brand") or back_extraction.get("brand")
    
    # Expiry and mfg date more likely on back
    merged["expiry_date"] = back_extraction.get("expiry_date") or front_extraction.get("expiry_date")
    merged["mfg_date"] = back_extraction.get("mfg_date") or front_extraction.get("mfg_date")
    
    # Ingredients and warnings from back (more likely), fallback to front
    merged["ingredients"] = back_extraction.get("ingredients") or front_extraction.get("ingredients", [])
    merged["warnings"] = back_extraction.get("warnings") or front_extraction.get("warnings", [])
    
    # Confidence: average of both
    front_conf = front_extraction.get("confidence", 0.5)
    back_conf = back_extraction.get("confidence", 0.5)
    merged["confidence"] = (front_conf + back_conf) / 2
    
    return merged

# Health check
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}

# Scan endpoint - supports front + back images for complete label data
@app.post("/scan")
async def scan(
    front: UploadFile = File(..., description="Front side of label"),
    back: Optional[UploadFile] = File(None, description="Back side of label (optional)"),
    db: Session = Depends(get_db),
):
    logger.info(f"📥 Received front: {front.filename}, back: {back.filename if back else 'None'}")
    
    if not front.content_type or not front.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Front file must be an image")
    if back and (not back.content_type or not back.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="Back file must be an image")
    
    try:
        scan_id = short_id()
        
        # Read front image
        front_bytes = await front.read()
        logger.info(f"📦 Front image size: {len(front_bytes)} bytes")
        front_path = save_image(front_bytes, scan_id, "front")
        
        # Run OCR on front
        logger.info("🔍 Running OCR on front side...")
        front_text = ocr_client.extract_text(front_bytes)
        logger.info(f"✅ Front OCR extracted {len(front_text)} chars")
        
        # Extract structured data from front
        front_extraction = extract_from_pipeline(front_text, front_text, front_text) if front_text.strip() else {}
        
        back_path = None
        back_text = ""
        back_extraction = {}
        
        # Process back image if provided
        if back:
            back_bytes = await back.read()
            logger.info(f"📦 Back image size: {len(back_bytes)} bytes")
            back_path = save_image(back_bytes, scan_id, "back")
            
            logger.info("🔍 Running OCR on back side...")
            back_text = ocr_client.extract_text(back_bytes)
            logger.info(f"✅ Back OCR extracted {len(back_text)} chars")
            
            # Extract structured data from back
            back_extraction = extract_from_pipeline(back_text, back_text, back_text) if back_text.strip() else {}
        
        # Merge or use front-only results
        if back and (front_text.strip() or back_text.strip()):
            result = merge_ocr_results(front_text, back_text, front_extraction, back_extraction)
        else:
            result = front_extraction
        
        # Add metadata
        result["id"] = scan_id
        result["sides"] = 2 if back else 1
        result["raw_ocr_front"] = front_text[:300] if front_text else ""
        if back:
            result["raw_ocr_back"] = back_text[:300] if back_text else ""
        
        # Handle case where no text was extracted at all
        if len(front_text.strip()) == 0 and (not back or len(back_text.strip()) == 0):
            result["failure_reason"] = "No text detected in image(s). Please ensure the label is clearly visible."
            result["suggestion"] = "Try capturing in better lighting or from a closer angle."
        
        # Store in DB
        combined_text = (front_text + "\n---BACK---\n" + back_text) if back else front_text
        db_scan = ScanHistory(
            id=scan_id,
            raw_text=combined_text[:1000],
            raw_text_front=front_text[:1000],
            raw_text_back=back_text[:1000] if back else None,
            extracted_json=result,
            confidence=result.get("confidence", 0.0),
            image_paths=json.dumps([front_path, back_path] if back else [front_path]),
        )
        db.add(db_scan)
        db.commit()
        db.refresh(db_scan)
        
        logger.info(f"✅ Scan complete: {scan_id} ({result['sides']} sides)")
        return result
        
    except Exception as e:
        logger.error("❌ Scan error", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# History list (paginated)
@app.get("/history")
def history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    scans = (
        db.query(ScanHistory)
        .order_by(ScanHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "summary": s.extracted_json.get("summary"),
            "confidence": s.confidence,
            "scannedAt": s.extracted_json.get("scannedAt"),
        }
        for s in scans
    ]

# History detail
@app.get("/history/{scan_id}")
def history_detail(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    image_paths = []
    if scan.image_paths:
        try:
            image_paths = json.loads(scan.image_paths)
        except:
            image_paths = []
    
    return {
        "id": scan.id,
        "rawText": scan.raw_text,
        "rawTextFront": scan.raw_text_front,
        "rawTextBack": scan.raw_text_back,
        "extracted": scan.extracted_json,
        "confidence": scan.confidence,
        "imagePaths": image_paths,
        "scannedAt": scan.extracted_json.get("scannedAt"),
    }

# Run with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
