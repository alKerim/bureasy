from fastapi import UploadFile, HTTPException
from typing import List
import logging
import json
from app.utils.chromadb_client import get_chroma_collection, embed_text

# Initialize logging
logger = logging.getLogger(__name__)

def ingest_json_to_chromadb(json_data):
    """Ingest JSON data into ChromaDB."""
    # Get the shared ChromaDB collection
    collection = get_chroma_collection()

    # Extract source URL
    source_url = json_data.get("url", "")

    # Extract main fields
    text = json_data.get("text", "")
    summary = json_data.get("summary", "")
    pdf_links = json_data.get("pdf_links", [])
    all_links = json_data.get("all_links", [])
    phone_numbers = json_data.get("phone_numbers", [])

    # Convert list metadata to JSON strings
    pdf_links_str = json.dumps(pdf_links) if pdf_links else ""
    all_links_str = json.dumps(all_links) if all_links else ""

    # Ingest phone numbers
    for idx, phone in enumerate(phone_numbers):
        number = phone.get("number", "")
        left_context = phone.get("left_context", "")
        right_context = phone.get("right_context", "")
        phone_text = f"{left_context} {number} {right_context}"

        phone_metadata = {
            "type": "phone_number",
            "number": number,
            "left_context": left_context,
            "right_context": right_context,
            "source_url": source_url,
        }

        # Add phone number data to the collection
        collection.add(
            documents=[phone_text],
            embeddings=[embed_text(phone_text)],
            metadatas=[phone_metadata],
            ids=[f"phone_number_{idx}"]
        )

    # Ingest main text and summary
    combined_text = f"{text} {summary}"
    main_metadata = {
        "type": "content",
        "summary": summary,
        "pdf_links": pdf_links_str,  # JSON string
        "all_links": all_links_str,  # JSON string
        "source_url": source_url,
    }

    # Add main text and summary to the collection
    collection.add(
        documents=[combined_text],
        embeddings=[embed_text(combined_text)],
        metadatas=[main_metadata],
        ids=["content_summary"]
    )

    # Ingest PDF links
    for idx, pdf_link in enumerate(pdf_links):
        pdf_metadata = {
            "type": "pdf",
            "pdf_link": pdf_link,
            "source_url": source_url,
        }
        collection.add(
            documents=[f"PDF Link: {pdf_link}"],
            embeddings=[embed_text(pdf_link)],
            metadatas=[pdf_metadata],
            ids=[f"pdf_link_{idx}"]
        )

    # Ingest all other links
    for idx, url in enumerate(all_links):
        url_metadata = {
            "type": "url",
            "url": url,
            "source_url": source_url,
        }
        collection.add(
            documents=[f"URL: {url}"],
            embeddings=[embed_text(url)],
            metadatas=[url_metadata],
            ids=[f"url_{idx}"]
        )

def ingest_json_data_from_files(files: List[UploadFile]):
    """Process uploaded files and ingest their data."""
    for file in files:
        try:
            # Read and parse the JSON file
            content = file.file.read()
            json_data = json.loads(content)

            # Ingest the JSON data into ChromaDB
            ingest_json_to_chromadb(json_data)
        except json.JSONDecodeError:
            logger.error(f"File {file.filename} is not a valid JSON file.")
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a valid JSON file.")
        except Exception as e:
            logger.exception(f"Error processing file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing file {file.filename}: {str(e)}")
    return "Files successfully ingested."
