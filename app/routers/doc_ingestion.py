import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List

from app.services.doc_ingestion_service import (
    ingest_json_data_from_files,
    generate_checklist,
    ask_human_phone
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant Responses"],
    responses={404: {"description": "Not found"}},
)

@router.post("/ingest-data")
def ingest_data(files: List[UploadFile] = File(...)):
    """
    Ingest JSON data from uploaded files into Chroma DB with E5 embeddings.
    """
    try:
        result = ingest_json_data_from_files(files)
        return {"message": result}
    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception(f"Error ingesting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ChecklistRequest(BaseModel):
    query: str

@router.post("/generate-checklist")
def generate_checklist_route(request: ChecklistRequest):
    """
    Query the vector store + LLM to produce a JSON-based checklist.
    """
    try:
        checklist_json = generate_checklist(request.query)
        return {"checklist": checklist_json}
    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception(f"Error generating checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class AskHumanRequest(BaseModel):
    query: str

@router.post("/ask-human")
def ask_human_route(request: AskHumanRequest):
    """
    Returns a plain phone number as a string or 'NoPhoneAvailable'
    if no number is available.
    """
    try:
        # Get the result from the `ask_human_phone` function
        result = ask_human_phone(request.query)

        # Ensure the response is cleaned and formatted properly
        if result == "NoPhoneAvailable":
            return "NoPhoneAvailable"

        return result
    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception(f"Error getting phone number: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
