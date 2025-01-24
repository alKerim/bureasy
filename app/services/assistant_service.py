import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message
from app.prompts.conversation_flows import CONVERSATION_FLOWS
from app.prompts.system_prompt_templates import prompt

# LLM integration
from app.utils.client_manager import client_manager
from app.config import settings

logger = logging.getLogger(__name__)

def start_new_conversation(db: Session, flow_type: str):
    """
    Create a new Conversation row with the specified flow type,
    store no messages yet, set state_index to 0 (start of flow).
    Returns (conversation_id, first_question).
    """
    if flow_type not in CONVERSATION_FLOWS:
        raise HTTPException(status_code=400, detail=f"Unknown flow type: {flow_type}")

    # Create conversation
    conversation = Conversation(flow_type=flow_type, state_index=0)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # Return the first question from the flow
    first_question = CONVERSATION_FLOWS[flow_type][0]
    return conversation.id, first_question

def process_user_message(db: Session, conversation_id: int, user_input: str):
    """
    1) Store the user's message.
    2) Determine the next question or if flow is finished.
    3) Store the assistant's response (the next question or final summary).
    4) Return (assistant_response, finished).
    """
    # Retrieve conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    flow_type = conversation.flow_type
    if flow_type not in CONVERSATION_FLOWS:
        raise HTTPException(status_code=400, detail="Invalid flow type in conversation.")

    flow = CONVERSATION_FLOWS[flow_type]

    # 1) Store user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_input
    )
    db.add(user_message)

    # Move the conversation state forward
    current_index = conversation.state_index
    next_index = current_index + 1

    # Check if we've reached the end of the flow
    if next_index < len(flow):
        # There is a next question
        next_question = flow[next_index]

        # Store assistant's next question
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=next_question
        )
        db.add(assistant_message)

        # Update conversation state
        conversation.state_index = next_index
        db.commit()

        return next_question, False
    else:
        # Flow is finished - provide a final LLM-based summary
        final_summary = generate_conversation_summary(db, conversation_id)

        # Store the summary as an assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=final_summary
        )
        db.add(assistant_message)

        # We do NOT increment state_index because we've finished
        db.commit()

        return final_summary, True

def generate_conversation_summary(db: Session, conversation_id: int) -> str:
    """
    Use LLM to create a final summary of all user messages from this conversation.
    """
    # Fetch only user messages
    user_messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.role == "user"
    ).all()

    if not user_messages:
        return "No user messages to summarize."

    # Prepare the conversation text for the LLM
    # You could create a prompt that includes all user messages
    user_input_text = "\n".join([f"User said: {msg.content}" for msg in user_messages])

    # Example: a system prompt instructing the LLM to summarize all user inputs
    system_prompt = (
        "You are a helpful assistant that creates a concise summary "
        "of the information the user provided during the conversation."
        "Focus on key details relevant to the user's visa extension request.\n\n"
    )

    full_prompt = system_prompt + user_input_text

    # Call the LLM (Groq example)
    try:
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[
                {"role": "system", "content": full_prompt}
            ],
            stream=True,
            max_tokens=300,
            temperature=0.2,
        )

        summary_text = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    summary_text += token

        return summary_text.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        # Fallback: basic bullet-point summary if LLM fails
        fallback_summary = "\n".join(
            [f"{i+1}. {msg.content}" for i, msg in enumerate(user_messages)]
        )
        return f"LLM summary failed. Here is a fallback summary:\n{fallback_summary}"

def get_conversation_summary(db: Session, conversation_id: int) -> str:
    """
    Return the final assistant message if the flow is finished,
    or dynamically generate if needed.
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    flow = CONVERSATION_FLOWS.get(conversation.flow_type, [])
    if conversation.state_index < len(flow):
        # Not done with the flow, so no final summary yet
        return "Flow is not yet complete. Please finish answering all questions."

    # The final assistant message should be the last message from the assistant
    last_message = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role == "assistant")
        .order_by(Message.id.desc())
        .first()
    )
    if last_message:
        return last_message.content
    else:
        return "No summary available."
