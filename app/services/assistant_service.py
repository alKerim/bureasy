import asyncio
import logging
from fastapi import HTTPException

from app.config import settings
from app.prompts.system_prompt_templates import prompt
from app.utils.client_manager import client_manager

logger = logging.getLogger(__name__)

async def generate_response_text(user_input: str) -> str:
    try:
        # Prepare the system and user messages
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input},
        ]

        # Initialize clients and fetch response
        client_manager.setup_clients()
        client = settings.CLIENT_NAME
        response_stream = None

        if client == "openai":
            openai_client = client_manager.get_openai_client()
            response_stream = openai_client.chat.completions.create(
                model=settings.MODEL_NAME_CONVERSATIONAL_OPENAI,
                messages=messages,
                stream=True,
                max_tokens=100,
                temperature=0.2,
            )
        elif client == "groq":
            groq_client = client_manager.get_groq_client()
            response_stream = groq_client.chat.completions.create(
                model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
                messages=messages,
                stream=True,
                max_tokens=100,
                temperature=0.2,
            )
        else:
            raise ValueError("Invalid client specified in settings.")

        if response_stream is None:
            raise ValueError("Response stream could not be initialized.")

        # Process response stream into text
        response_text = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    response_text += token
        response_text = response_text.strip()

        # Make sure to RETURN the response_text
        return response_text

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response.")
