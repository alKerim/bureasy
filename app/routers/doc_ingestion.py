import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List

from app.services.doc_ingestion_service import ingest_json_data_from_files

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Document Ingestion"],
    responses={404: {"description": "Not found"}},
)

@router.post("/ingest-data")
def ingest_data(files: List[UploadFile] = File(...)):
    """API endpoint to ingest uploaded JSON files."""
    try:
        result = ingest_json_data_from_files(files)
        return {"message": result}
    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception(f"Error ingesting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))