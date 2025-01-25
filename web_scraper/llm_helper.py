from http.client import HTTPException

from config import settings
from models.conversation import Conversation

from client_manager_scraper import client_manager


def summarize_website(site_text: str) -> str:
    """
    Summarize the site_text, which is scraped from a website, and generate an overview of everything
    that is available on the site. This function should return a string that summarizes the site_text.
    """


    system_prompt = (
        "Below is the raw text from the website:\n"
        f"{site_text}\n\n"
        "Please reply with a summary of every available information on the site."
        "Don't leave out important information, but keep it concise. "
        "Don't add any comments from you, just reply directly with and only with the summary. don't say things like 'Here is a summary of the available information on the site:'. Just start directly."
        "Don't summarize detailed what is there, just list as many different things the user can find on the site."

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
        fallback = "Failed to generate request. Please summarize the site text manually."
        return (
                "LLM request generation failed. Fallback request based on partial conversation:\n"
                + fallback
        )
