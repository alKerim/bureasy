# app/routers/assistant.py

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.assistant_service import (
    process_incoming_message,
    generate_user_request
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
class ChatRequest(BaseModel):
    user_input: str
    conversation_id: int | None = None  # If null => detect or start new flow

class ChatResponse(BaseModel):
    conversation_id: int | None
    response: str
    finished: bool

@router.post("/message", response_model=ChatResponse)
def handle_message(request_data: ChatRequest, db: Session = Depends(get_db)):
    """
    Single endpoint to handle user messages.
    1) If conversation_id not provided/invalid => LLM tries to detect flow.
    2) If recognized => next question or final summary.
    3) If unsupported => politely say so.
    """
    try:
        conversation_id, response_text, finished = process_incoming_message(
            db=db,
            user_input=request_data.user_input,
            conversation_id=request_data.conversation_id
        )
        return {
            "conversation_id": conversation_id,
            "response": response_text,
            "finished": finished
        }
    except HTTPException as http_exc:
        logger.error(f"Error processing message: {http_exc.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.get("/{conversation_id}/generate-request")
def skip_and_generate_request(conversation_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to skip the remaining questions and generate a partial user request from
    any data collected so far.
    """
    try:
        user_request = generate_user_request(db, conversation_id)
        return {
            "conversation_id": conversation_id,
            "user_request": user_request
        }
    except HTTPException as http_exc:
        logger.error(f"Error generating user request: {http_exc.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
