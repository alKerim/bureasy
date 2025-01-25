import os

# Set the TOKENIZERS_PARALLELISM environment variable before any other imports
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
from typing import List, Dict
from fastapi import HTTPException, UploadFile
import json
import re

import torch
from transformers import AutoTokenizer, AutoModel

import chromadb
from chromadb.utils import embedding_functions

from app.prompts.system_prompt_templates import (
    checklist_system_prompt,
    ask_human_system_prompt
)
from app.utils.client_manager import client_manager
from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------
# 1) Setup the E5 model for embeddings (Lazy Initialization)
# ---------------------------
MODEL_NAME = "intfloat/e5-base"  # e.g. "intfloat/e5-large", "GTE-base", etc.

tokenizer = None
model = None

def initialize_model():
    global tokenizer, model
    if tokenizer is None or model is None:
        logger.info("Initializing tokenizer and model...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME)
        model.eval()
        logger.info("Tokenizer and model initialized.")

# Helper to get embeddings from the E5 model
def embed_text(text: str) -> List[float]:
    initialize_model()
    text = "passage: " + text
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state[:, 0, :]
    return embeddings.squeeze().tolist()

# Custom Chroma embedding function
class E5EmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __call__(self, texts: List[str]) -> List[List[float]]:
        return [embed_text(t) for t in texts]

# ---------------------------
# 2) Initialize Chroma with persistent storage
# ---------------------------
# Directory to persist Chroma data
persist_directory = './chroma_data'
os.makedirs(persist_directory, exist_ok=True)

# Initialize Chroma PersistentClient
chroma_client = chromadb.PersistentClient(path=persist_directory)

embedding_fn = E5EmbeddingFunction()
collection_name = "munich_docs"

# Check if the collection already exists and load it
existing_collections = chroma_client.list_collections()

if collection_name in existing_collections:
    logger.info(f"Collection '{collection_name}' already exists. Loading it...")
    doc_collection = chroma_client.get_collection(
        name=collection_name,
        embedding_function=embedding_fn  # Ensure the embedding function is used
    )
else:
    logger.info(f"Collection '{collection_name}' does not exist. Creating a new one...")
    doc_collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

# ---------------------------
# 3) Ingestion function with phone context extraction
# ---------------------------
PHONE_REGEX = r'\+?\d[\d\-()\s]{5,}\d'

def extract_phone_numbers_with_context(text: str) -> List[Dict[str, str]]:
    """Extract phone numbers and their context (left/right) from text."""
    sentences = text.split('.')  # Split text into sentences
    results = []

    for i, sentence in enumerate(sentences):
        matches = re.findall(PHONE_REGEX, sentence)
        for match in matches:
            left_context = sentences[i-1].strip() if i > 0 else ""
            right_context = sentences[i+1].strip() if i < len(sentences) - 1 else ""

            results.append({
                "number": match,
                "left_context": left_context,
                "right_context": right_context
            })

    return results

def ingest_json_data_from_files(files: List[UploadFile]) -> str:
    try:
        ids = []
        docs = []
        metas = []

        for file in files:
            # Read and parse the JSON content
            content = file.file.read().decode("utf-8")
            data = json.loads(content)  # Safely parse JSON

            # Ensure `data` is a list of dictionaries
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                raise ValueError("Invalid JSON format. Expected a list or a dictionary.")

            for item in data:
                doc_id = item.get("id", f"auto-id-{len(ids)+1}")
                text = item.get("content") or item.get("text") or ""
                url = item.get("url", "")
                summary = item.get("summary", "")  # Extract the summary field

                # Extract phone numbers with context
                phone_metadata = extract_phone_numbers_with_context(text)
                phone_metadata_str = json.dumps(phone_metadata)
                
                # Convert all_links to a JSON string or a comma-separated string
                all_links = item.get("all_links", [])
                all_links_str = json.dumps(all_links) if isinstance(all_links, list) else ""
                
                meta = {
                    "title": item.get("title"),
                    "url": url,
                    "phone_numbers": phone_metadata_str,
                    "all_links": all_links_str,
                    "summary": summary,  # Add summary to metadata
                }
                # Remove keys with None values
                meta = {k: v for k, v in meta.items() if v}

                ids.append(doc_id)
                docs.append(text)
                metas.append(meta)

        if not ids:
            raise ValueError("No valid documents found in the uploaded files.")

        # Add data to the persistent collection
        doc_collection.add(
            documents=docs,
            metadatas=metas,
            ids=ids
        )

        logger.info(f"Ingested {len(ids)} documents into the collection.")
        return "Data ingestion complete."

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format in uploaded file.")
    except Exception as e:
        logger.error(f"Error ingesting data into Chroma: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest JSON data into Chroma.")

# ---------------------------
# 4) Generate checklist from retrieved docs
# ---------------------------
def generate_checklist(query: str) -> str:
    try:
        total_docs = doc_collection.count()
        logger.info(f"Total documents in collection: {total_docs}")

        if total_docs == 0:
            raise HTTPException(
                status_code=404,
                detail="No documents available in the vector store."
            )

        n_results = min(3, total_docs)
        results = doc_collection.query(
            query_texts=[query],
            n_results=n_results
        )
    except Exception as e:
        logger.error(f"Error querying Chroma: {e}")
        raise HTTPException(status_code=500, detail="Failed to query vector store.")

    if not results.get("documents"):
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found for the query."
        )

    relevant_snippets = [doc for docs in results["documents"] for doc in docs]
    snippets_str = "\n".join(relevant_snippets)

    if not snippets_str.strip():
        snippets_str = "No relevant context found in the vector store."

    try:
        system_prompt = checklist_system_prompt.format(
            snippets_placeholder=snippets_str,
            user_request_placeholder=query
        )
    except KeyError as e:
        logger.error(f"Error formatting checklist prompt: {e}")
        raise HTTPException(status_code=500, detail="Failed to format system prompt.")

    try:
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[{"role": "system", "content": system_prompt}],
            stream=True,
            max_tokens=600,
            temperature=0.4,
        )

        raw_output = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    raw_output += token

        return raw_output.strip()

    except Exception as e:
        logger.error(f"Error generating checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate checklist.")

def ask_human_phone(query: str) -> str:
    try:
        # Check if documents exist in the collection
        total_docs = doc_collection.count()
        if total_docs == 0:
            raise HTTPException(
                status_code=404,
                detail="No documents in the vector store to find a phone number."
            )

        # Query the vector store
        n_results = min(3, total_docs)
        results = doc_collection.query(
            query_texts=[query],
            n_results=n_results
        )
    except Exception as e:
        logger.error(f"Error querying Chroma for ask-human: {e}")
        raise HTTPException(status_code=500, detail="Failed to query vector store.")

    phone_candidates = []
    for meta_batch in results.get("metadatas", []):
        for meta in meta_batch:
            phone_data_str = meta.get("phone_numbers", "[]")  # Get the JSON string
            try:
                # Decode the JSON string into a Python list of dictionaries
                phone_data = json.loads(phone_data_str)
                for phone in phone_data:
                    phone_candidates.append(phone["number"])
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.error(f"Error decoding phone data: {e}")

    if not phone_candidates:
        phone_candidates.append("NoPhoneAvailable")

    phones_text = "\n".join(phone_candidates)

    # Build the prompt
    prompt = ask_human_system_prompt.format(phones=phones_text)

    try:
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        # Call the conversational model
        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[{"role": "system", "content": f"{prompt}\n\nPhones:\n{phones_text}"}],
            stream=True,
            max_tokens=100,
            temperature=0.2,
        )

        raw_output = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    raw_output += token

        return raw_output.strip()

    except Exception as e:
        logger.error(f"Error generating phone number for ask-human: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate phone contact.")