import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
from itertools import chain
from app.utils.chromadb_client import get_chroma_collection, embed_text
from app.utils.client_manager import client_manager
from app.config import settings
from app.prompts.system_prompt_templates import checklist_generation_template

# Initialize logger
logger = logging.getLogger(__name__)

def generate_checklist(query: str) -> dict:
    """
    Query ChromaDB and generate a checklist based on user input.
    """
    try:
        # Get the shared ChromaDB collection
        collection = get_chroma_collection()

        # Generate the query embedding
        query_embedding = embed_text(query)

        # Perform semantic search on the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10  # Retrieve more results for a broader checklist
        )

        # Flatten the metadata list
        all_metadatas = list(chain.from_iterable(results.get("metadatas", [])))

        # Prepare the checklist
        checklist = {
            "query": query,
            "steps": []
        }

        # Extract steps, PDFs, and sources
        for metadata in all_metadatas:
            step = metadata.get("summary", "").strip() or metadata.get("text", "").strip()
            pdf_links = metadata.get("pdf_links", [])
            source_url = metadata.get("source_url", "Unknown Source")

            if step:
                checklist["steps"].append({
                    "step": step,
                    "details": [step],
                    "pdf_links": pdf_links,
                    "source": source_url
                })

        # Validate checklist steps
        if not checklist["steps"]:
            raise ValueError("No valid steps found for the query.")

        return checklist

    except Exception as e:
        logger.exception(f"Error generating checklist: {e}")
        raise Exception("Internal server error while generating the checklist.")

def send_checklist_to_ai_model(query: str, checklist: dict) -> str:
    """
    Format the checklist and send it to the AI model for further processing.
    
    Args:
        query (str): The user's query.
        checklist (dict): The checklist generated based on the query.
    
    Returns:
        str: The formatted response from the AI model.
    """
    try:
        # Ensure formatted_steps is correctly built
        formatted_steps = ""
        for idx, step in enumerate(checklist.get("steps", []), start=1):
            step_details = "\n".join(f"- {detail}" for detail in step.get("details", []))
            pdf_links = step.get("pdf_links", [])
            formatted_pdf_links = (
                f"PDF Links:\n{chr(10).join(pdf_links)}\n" if pdf_links else ""
            )
            source = step.get("source", "Unknown Source")

            formatted_steps += (
                f"Step {idx}:\n{step['step']}\n{step_details}\n{formatted_pdf_links}Source: {source}\n\n"
            )

        # Validate formatted_steps
        if not formatted_steps.strip():
            logger.error("Formatted steps are empty. Ensure checklist steps are provided.")
            raise ValueError("Formatted steps are empty.")

        # Format the system prompt
        system_prompt = checklist_generation_template.format(
            query=query,
            formatted_steps=formatted_steps  # Pass formatted_steps here
        ).strip()

    except KeyError as e:
        logger.error(f"Error formatting checklist prompt: Missing key: {e}")
        raise Exception("Failed to format the system prompt.")
    except Exception as e:
        logger.error(f"Error formatting checklist prompt: {e}")
        raise Exception("Failed to format the system prompt.")

    try:
        # Set up the client
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        # Send the system prompt to the AI model
        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[{"role": "system", "content": system_prompt}],
            stream=True,
            max_tokens=600,
            temperature=0.4,
        )

        # Collect the streamed response
        raw_output = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    raw_output += token

        return raw_output.strip()

    except Exception as e:
        logger.error(f"Error querying AI model: {e}")
        raise Exception("Failed to retrieve response from the AI model.")
