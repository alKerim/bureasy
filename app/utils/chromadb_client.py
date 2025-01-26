import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Configure persistent storage for ChromaDB
PERSIST_DIRECTORY = "./chroma_db"

# Initialize ChromaDB client
client = chromadb.Client(
    Settings(
        persist_directory=PERSIST_DIRECTORY,
        is_persistent=True
    )
)

# Get or create the shared collection
def get_chroma_collection(collection_name: str = "knowledge_base"):
    """Retrieve or create the shared ChromaDB collection."""
    return client.get_or_create_collection(collection_name)

# Initialize embedding model
embedding_model = SentenceTransformer("all-MPNet-base-v2")

def embed_text(text: str):
    """Generate embeddings for a given text."""
    return embedding_model.encode(text).tolist()
