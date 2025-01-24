from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.services.assistant_service import generate_response_text

# Initialize logger and router
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/assistant",
    tags=["Assistant Responses"],
    responses={404: {"description": "Not found"}},
)

# Define request & response models
class GenerateRequest(BaseModel):
    user_input: str

class GenerateTextResponse(BaseModel):
    success: bool
    response: str

@router.post(
    "/generate-text-response",
    summary="Generate Text Response",
    response_model=GenerateTextResponse
)
async def generate_text_response(request_data: GenerateRequest):
    """
    Generate the assistant's text response based on user input (and system prompts).

    :param request_data: JSON containing user input text.
    :return: JSON response containing success status and the assistant's generated response.
    """
    try:
        response_text = await generate_response_text(request_data.user_input)
        logger.info("Successfully generated assistant response.")
        return {"success": True, "response": response_text}
    except HTTPException as http_exc:
        logger.error(f"HTTP error while generating response: {http_exc.detail}")
        raise http_exc
    except ValueError as val_err:
        logger.error(f"Value error while generating response: {val_err}")
        raise HTTPException(status_code=400, detail="Invalid input data.")
    except Exception as e:
        logger.exception(f"Unexpected error while generating response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
