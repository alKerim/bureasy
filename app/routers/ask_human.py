from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ask_human_service import ask_human_phone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["Ask Human"],
    responses={404: {"description": "Not found"}},
)

class AskHumanRequest(BaseModel):
    query: str

class AskHumanResponse(BaseModel):
    phone: str

@router.post("/ask-human", response_model=AskHumanResponse)
def ask_human_route(request: AskHumanRequest):
    """
    Returns a phone number as a JSON object or 'NoPhoneAvailable'
    if no number is available.
    """
    try:
        # Get the result from the `ask_human_phone` function
        result = ask_human_phone(request.query)

        # Ensure the response is wrapped in the expected format
        if result == "NoPhoneAvailable":
            return AskHumanResponse(phone="NoPhoneAvailable")

        return AskHumanResponse(phone=result)
    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception(f"Error getting phone number: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
