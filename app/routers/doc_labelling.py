import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.services.document_labelling_service import process_pdf_document

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Document Processing"],
    responses={404: {"description": "Not found"}},
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload and process a PDF, returning doc type and tags.
    """
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext != ".pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    temp_file_name = f"{uuid.uuid4()}{ext}"
    temp_path = os.path.join("/tmp", temp_file_name)

    try:
        # Save locally
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        result = process_pdf_document(temp_path)

        return {
            "filename": filename,
            "document_type": result.get("document_type", "unknown"),
            "tags": result.get("tags", [])
        }

    except Exception as e:
        logger.exception(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to process PDF.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
