# Multi-Image Scanning Feature - Changes Summary

## Branch: feature/multi-image-scanning

### Overview
Added support for capturing **front and back sides** of product labels to extract complete information like expiry dates, ingredients, and warnings from both sides.

---

## Backend Changes

### 1. **Database Model** (`backend/models.py`)
**Changes:** +3 lines
- Added `image_paths` (JSON) - stores list of saved image paths `["front.jpg", "back.jpg"]`
- Added `raw_text_front` (Text) - OCR text extracted from front side
- Added `raw_text_back` (Text) - OCR text extracted from back side

**Migration needed:** Run `alembic upgrade head` or restart backend to auto-create columns

---

### 2. **API Endpoint** (`backend/main.py`)
**Changes:** +148 lines, -100 lines

#### New Endpoint Signature:
```python
@app.post("/scan")
async def scan(
    front: UploadFile = File(..., description="Front side of label"),
    back: Optional[UploadFile] = File(None, description="Back side (optional)"),
    db: Session = Depends(get_db),
)
```

#### New Helper Functions:
- **`save_image()`** - Saves images to `uploads/{scan_id}_{side}.jpg`
- **`merge_ocr_results()`** - Intelligently combines front + back OCR results:
  - **Product name/brand** → prioritize front
  - **Expiry date/mfg date** → prioritize back
  - **Ingredients/warnings** → prioritize back
  - **Confidence** → average of both sides

#### Response Changes:
```json
{
  "id": "abc123",
  "sides": 2,
  "product_name": "...",
  "expiry_date": "...",  // from back
  "ingredients": [...],  // from back
  "raw_ocr_front": "...",
  "raw_ocr_back": "..."
}
```

---

### 3. **OCR Service** (`backend/services/ocr.py`)
**Changes:** +22 lines removed (code cleanup)
- Minor imports/formatting updates

---

### 4. **Environment Config** (`backend/.env.example`)
**Changes:** +3 lines
- Documentation updates for new features

---

## Mobile App Changes

### 1. **Scanning Screen UI** (`create-anything/_/apps/mobile/src/app/(tabs)/home/scanning.jsx`)
**Changes:** +155 lines, -155 lines (complete refactor)

#### New State Management:
- `frontImageUri` - stores captured front image
- `backImageUri` - stores captured back image
- `currentSide` - tracks which side being captured ("front" or "back")

#### Capture Flow:
1. **Stage 1**: Capture front side
   - Auto-captures after 2s
   - Shows thumbnail with green border
   - Voice feedback: "Front side captured, now scan the back side"

2. **Stage 2**: Capture back side
   - Auto-captures after 2s
   - Shows both thumbnails
   - Sends both images to backend

3. **Reset Option**: Reset button to restart if needed

#### UI Components:
- Thumbnail previews of captured images (green bordered)
- Dynamic prompt text: "Point at FRONT" → "Point at BACK"
- Reset button (appears after front is captured)
- Status messages for each stage

---

### 2. **API Client** (`create-anything/_/apps/mobile/src/utils/api.js`)
**Changes:** +64 lines

#### New Function: `scanImages(frontImageUri, backImageUri)`
- Sends both images to backend `/scan` endpoint
- Form fields: `front` and `back`
- Timeout: 60 seconds (longer for dual images)
- Upload progress tracking

#### Legacy Support:
- `scanImage()` still works for single images
- Backward compatible with old backend

---

## File Statistics

```
 backend/.env.example                               |   3 +-
 backend/main.py                                    | 148 ++++++++
 backend/models.py                                  |   3 +
 backend/services/ocr.py                            |  22 +--
 create-anything/_/apps/mobile/package-lock.json    |  55 +++++---
 .../home/scanning.jsx                              | 155 ++++++++
 create-anything/_/apps/mobile/src/utils/api.js     |  64 ++++++-

 7 files changed, 350 insertions(+), 100 deletions(-)
```

---

## Testing Checklist

- [ ] Backend can handle single image (backward compat)
- [ ] Backend can handle front + back images
- [ ] OCR results are merged correctly
- [ ] Expiry date extracted from back side
- [ ] Product name extracted from front side
- [ ] Images saved to `uploads/` folder
- [ ] Database stores both `raw_text_front` and `raw_text_back`
- [ ] Mobile shows front capture → back capture flow
- [ ] Thumbnails display correctly
- [ ] Reset button works after front capture
- [ ] Voice feedback plays at each stage

---

## Deployment Steps

1. **Merge to main** when tested:
   ```bash
   git checkout main
   git merge feature/multi-image-scanning
   ```

2. **Backend**:
   - Run migrations if needed
   - Restart uvicorn server

3. **Mobile**:
   - Rebuild/restart Expo app
   - Test with both front and back images

---

## API Examples

### Single Image (Legacy):
```bash
curl -X POST "http://localhost:8000/scan" \
  -F "front=@/path/to/front.jpg"
```

### Front + Back (New):
```bash
curl -X POST "http://localhost:8000/scan" \
  -F "front=@/path/to/front.jpg" \
  -F "back=@/path/to/back.jpg"
```

---

## Notes

- Images are stored locally in `uploads/` folder (not the best for production - consider S3/cloud storage)
- Database is auto-migrated when models change (SQLAlchemy)
- Mobile app auto-captures with 2s delay - can be configured in UI
- Voice feedback requires `settings.voiceEnabled` flag
