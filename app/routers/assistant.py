import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.assistant_service import (
    start_new_conversation,
    process_user_message,
    get_conversation_summary
)
from app.models.database import SessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/assistant",
    tags=["Assistant Responses"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request & Response Models
class StartConversationRequest(BaseModel):
    flow_type: str  # e.g., "visa_extension"

class StartConversationResponse(BaseModel):
    conversation_id: int
    first_question: str

class NextMessageRequest(BaseModel):
    conversation_id: int
    user_input: str

class NextMessageResponse(BaseModel):
    conversation_id: int
    response: str
    finished: bool  # Indicates if the flow is finished or not

@router.post("/start-conversation", response_model=StartConversationResponse)
def start_conversation(request_data: StartConversationRequest, db: Session = Depends(get_db)):
    try:
        conversation_id, first_question = start_new_conversation(db, request_data.flow_type)
        return {
            "conversation_id": conversation_id,
            "first_question": first_question
        }
    except HTTPException as http_exc:
        logger.error(f"Error starting conversation: {http_exc.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.post("/next-message", response_model=NextMessageResponse)
def handle_next_message(request_data: NextMessageRequest, db: Session = Depends(get_db)):
    try:
        conversation_id = request_data.conversation_id
        user_input = request_data.user_input
        response, finished = process_user_message(db, conversation_id, user_input)
        return {
            "conversation_id": conversation_id,
            "response": response,
            "finished": finished
        }
    except HTTPException as http_exc:
        logger.error(f"Error processing message: {http_exc.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.get("/{conversation_id}/summary")
def get_summary(conversation_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a final summary of all user data in the conversation.
    """
    try:
        summary_text = get_conversation_summary(db, conversation_id)
        return {"conversation_id": conversation_id, "summary": summary_text}
    except HTTPException as http_exc:
        logger.error(f"Error getting summary: {http_exc.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
