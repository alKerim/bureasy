from openai import OpenAI
from groq import Groq
from app.config import settings

class ClientManager:
    """Manages shared instances of external clients."""
    def __init__(self):
        self.groq_client = None
        self.openai_client = None

    def setup_clients(self):
        """Initialize clients if not already initialized."""
        if not self.groq_client:
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not set in the environment.")
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)

        if not self.openai_client:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in the environment.")
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def get_groq_client(self):
        if not self.groq_client:
            raise RuntimeError("Groq client is not initialized. Call setup_clients first.")
        return self.groq_client

    def get_openai_client(self):
        if not self.openai_client:
            raise RuntimeError("OpenAI client is not initialized. Call setup_clients first.")
        return self.openai_client

# Singleton instance of the client manager
client_manager = ClientManager()
