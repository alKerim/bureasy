# app/services/assistant_service.py

import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message
from app.prompts.conversation_flows import CONVERSATION_FLOWS
from app.prompts.system_prompt_templates import (
    detect_flow_prompt,
    next_question_prompt,
    user_request_generation_prompt,
    classification_instructions_template,
)
from app.utils.client_manager import client_manager
from app.config import settings

logger = logging.getLogger(__name__)

def process_incoming_message(db: Session, user_input: str, conversation_id: int | None):
    """
    1) If conversation_id is None or invalid => detect flow from user_input via LLM.
    2) If recognized => create/resume conversation.
    3) Store user msg => ask next question or produce final summary.
    """
    conversation = None
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        detected_flow = detect_flow_from_text(user_input)
        if not detected_flow:
            # If LLM can't match a known flow
            response_text = (
                "Thanks for your request. Unfortunately, we do not yet support this process. "
                "We may add it in a future release."
            )
            return None, response_text, True
        else:
            # Create new conversation
            conversation = Conversation(flow_type=detected_flow, state_index=0)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

    flow_type = conversation.flow_type
    flow = CONVERSATION_FLOWS.get(flow_type)
    if not flow:
        raise HTTPException(status_code=400, detail="Flow type not recognized.")

    # Store the user's message
    user_msg = Message(conversation_id=conversation.id, role="user", content=user_input)
    db.add(user_msg)
    db.commit()

    current_index = conversation.state_index
    next_index = current_index + 1

    if next_index < len(flow):
        # We still have questions => reword next question
        raw_question = flow[next_index]
        next_q = ai_generate_question(conversation, raw_question, db)

        assistant_msg = Message(
            conversation_id=conversation.id, 
            role="assistant", 
            content=next_q
        )
        db.add(assistant_msg)

        conversation.state_index = next_index
        db.commit()

        return conversation.id, next_q, False
    else:
        # All questions answered => generate user request
        user_request = generate_user_request(db, conversation.id)
        
        assistant_msg = Message(
            conversation_id=conversation.id, 
            role="assistant", 
            content=user_request
        )
        
        db.add(assistant_msg)
        db.commit()
        
        return conversation.id, user_request, True
    
def detect_flow_from_text(user_input: str) -> str | None:
    """
    LLM-based flow detection using classification_instructions_template.
    Dynamically list known flows from CONVERSATION_FLOWS. If not matched => None.
    """
    known_flows = list(CONVERSATION_FLOWS.keys())  # e.g. ["visa_extension", ...]

    flow_list_text = "\n".join(f"- {f}" for f in known_flows)

    classification_text = classification_instructions_template.format(
        detect_flow_prompt=detect_flow_prompt,
        flow_list_text=flow_list_text,
        user_input=user_input
    )

    try:
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[{"role": "system", "content": classification_text}],
            stream=True,
            max_tokens=30,
            temperature=0.0,
        )

        llm_response = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    llm_response += token

        llm_response = llm_response.strip().lower()
        logger.info(f"[Flow Detection] LLM responded: {llm_response}")

        # If LLM response is one of our known flows => use it
        if llm_response in known_flows:
            return llm_response

        return None

    except Exception as e:
        logger.error(f"Error detecting flow: {e}")
        # fallback if LLM fails
        fallback_input = user_input.lower()
        if "visa" in fallback_input or "extend" in fallback_input:
            return "visa_extension"
        return None

def ai_generate_question(conversation: Conversation, new_question: str, db: Session) -> str:
    """
    Reword new_question in a friendlier style, using recent conversation context.
    """
    recent_msgs = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.id.desc()).limit(5).all()

    user_context = "\n".join(
        f"{m.role.capitalize()}: {m.content}" for m in reversed(recent_msgs)
    )

    system_prompt = (
        f"{detect_flow_prompt}\n\n"
        f"{next_question_prompt}\n\n"
        "Conversation so far:\n"
        f"{user_context}\n\n"
        "Raw next question:\n"
        f"{new_question}\n"
        "Please reply ONLY with the reworded question, nothing else."
    )

    try:
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[{"role": "system", "content": system_prompt}],
            stream=True,
            max_tokens=120,
            temperature=0.3,
        )

        final_question = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    final_question += token

        return final_question.strip()

    except Exception as e:
        logger.error(f"Error generating next question: {e}")
        return new_question

def generate_user_request(db: Session, conversation_id: int) -> str:
    """
    Generate a user request from partial or complete conversation data.
    We include both user's answers and assistant's questions for full context.
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Fetch entire conversation so LLM sees Q&A
    all_msgs = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.id.asc()).all()

    if not all_msgs:
        return "No messages to generate a request."

    conv_context = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in all_msgs)

    system_prompt = (
        f"{user_request_generation_prompt}\n\n"
        "Below is the conversation so far, including both questions and user responses:\n"
        f"{conv_context}\n\n"
        "Please generate a concise, polite user request to the relevant authority using first-person language. "
        "If some details are missing, politely mention them. End with a polite question like 'What do I need to do next?'."
    )

    try:
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[{"role": "system", "content": system_prompt}],
            stream=True,
            max_tokens=400,
            temperature=0.4,
        )

        request_text = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    request_text += token

        return request_text.strip()

    except Exception as e:
        logger.error(f"Error generating user request: {e}")
        fallback = "\n".join([f"- {m.role.capitalize()}: {m.content}" for m in all_msgs])
        return (
            "LLM request generation failed. Fallback request based on partial conversation:\n"
            + fallback
        )
