import logging
from typing import List, Dict
from fastapi import HTTPException, UploadFile
import json
import os

import torch
from transformers import AutoTokenizer, AutoModel

import chromadb
from chromadb.utils import embedding_functions

from app.prompts.system_prompt_templates import checklist_system_prompt
from app.utils.client_manager import client_manager
from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------
# 1) Setup the E5 model for embeddings
# ---------------------------
MODEL_NAME = "intfloat/e5-base"  # e.g. "intfloat/e5-large", "GTE-base", etc.

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()

# Helper to get embeddings from the E5 model
def embed_text(text: str) -> List[float]:
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

# Get or create the collection with persistence
try:
    doc_collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )
except Exception:
    doc_collection = chroma_client.get_collection(collection_name)

# ---------------------------
# 3) Ingestion function
# ---------------------------
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
                doc_id = item.get("id", "auto-id")
                text = item.get("content") or item.get("text") or ""
                meta = {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "phone": item.get("phone"),
                    "pdf_links": ", ".join(item.get("pdf_links", [])) if item.get("pdf_links") else None,
                    "all_links": ", ".join(item.get("all_links", [])) if item.get("all_links") else None,
                }
                # Remove keys with None values
                meta = {k: v for k, v in meta.items() if v is not None}

                ids.append(doc_id)
                docs.append(text)
                metas.append(meta)

        # Add data to the persistent collection
        doc_collection.add(
            documents=docs,
            metadatas=metas,
            ids=ids
        )

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
        # Query the persistent Chroma collection
        results = doc_collection.query(
            query_texts=[query],
            n_results=3
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
