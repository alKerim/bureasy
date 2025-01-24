from app.utils.client_manager import client_manager
from app.config import settings

def get_clients():
    """
    Dependency to get initialized clients.
    """
    client_manager.setup_clients()
    return client_manager
