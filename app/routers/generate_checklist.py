from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.services.checklist_generation_service import generate_checklist, send_checklist_to_ai_model
import json

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
    ai_response: dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.services.checklist_generation_service import generate_checklist, send_checklist_to_ai_model
import json

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
    ai_response: dict

@router.post("/generate-checklist", response_model=ChecklistResponse)
def generate_checklist_route(request: ChecklistRequest):
    """
    Query the vector store + LLM to produce a JSON-based checklist, then send it to an AI model for processing.
    """
    try:
        # Generate the checklist
        checklist_json = generate_checklist(request.query)
        logger.info(f"Generated checklist: {checklist_json}")

        # Send the checklist to the AI model for further formatting
        ai_response = send_checklist_to_ai_model(request.query, checklist_json)
        logger.info(f"AI response (raw): {ai_response}")

        # Process and clean up the AI response
        if isinstance(ai_response, str):
            # Remove potential formatting markers (like ```json and ``` around the response)
            ai_response = ai_response.strip()
            if ai_response.startswith("```json"):
                ai_response = ai_response[7:]
            if ai_response.endswith("```"):
                ai_response = ai_response[:-3]

            logger.info(f"AI response (cleaned): {ai_response}")

            # Attempt to parse the cleaned response as JSON
            try:
                ai_response = json.loads(ai_response)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing AI response as JSON: {e}")
                raise HTTPException(status_code=500, detail="Failed to parse AI response as valid JSON.")

        # Ensure the parsed response is a dictionary
        if not isinstance(ai_response, dict):
            logger.error(f"AI response is not a valid dictionary: {ai_response}")
            raise HTTPException(status_code=500, detail="AI response format is invalid.")

        # Return the successfully parsed and validated AI response
        return ChecklistResponse(ai_response=ai_response)

    except HTTPException as exc:
        logger.error(f"HTTPException occurred: {exc.detail}")
        raise exc
    except Exception as e:
        logger.exception(f"Unexpected error generating checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate the checklist or query the AI model.")
