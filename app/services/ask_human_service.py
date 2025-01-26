import logging
from itertools import chain
from app.utils.chromadb_client import get_chroma_collection, embed_text

# Initialize logger
logger = logging.getLogger(__name__)

def ask_human_phone(query: str) -> str:
    """Query ChromaDB for the most relevant phone number based on its context."""
    try:
        # Get the shared ChromaDB collection
        collection = get_chroma_collection()

        # Generate the query embedding
        query_embedding = embed_text(query)

        # Perform semantic search on the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5  # Number of results to retrieve
        )

        # Flatten the metadatas list (handles potential list of lists)
        all_metadatas = list(chain.from_iterable(results.get("metadatas", [])))

        # Parse and prioritize results for phone numbers with context
        for metadata in all_metadatas:
            if metadata.get('type') == "phone_number":
                number = metadata.get("number", "No number available")
                
                # Return the phone number directly
                return number

        # If no phone number matches, return "NoPhoneAvailable"
        logger.info("No phone number found matching the query.")
        return "NoPhoneAvailable"

    except Exception as e:
        logger.exception(f"Error querying for phone number: {e}")
        raise Exception("Internal server error while querying ChromaDB.")
