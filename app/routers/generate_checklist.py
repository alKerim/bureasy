from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.services.checklist_generation_service import generate_checklist, send_checklist_to_ai_model

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["Checklist Generation"],
    responses={404: {"description": "Not found"}},
)

class ChecklistRequest(BaseModel):
    query: str

class ChecklistResponse(BaseModel):
    checklist: dict
    ai_response: str

@router.post("/generate-checklist", response_model=ChecklistResponse)
def generate_checklist_route(request: ChecklistRequest):
    """
    Query the vector store + LLM to produce a JSON-based checklist, then send it to an AI model for processing.
    """
    try:
        # Generate the checklist
        checklist_json = generate_checklist(request.query)
        print(checklist_json)
        # Send the checklist to the AI model for further formatting
        ai_response = send_checklist_to_ai_model(request.query, checklist_json)
        print(ai_response)
        return ChecklistResponse(checklist=checklist_json, ai_response=ai_response)

    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception(f"Error generating checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
