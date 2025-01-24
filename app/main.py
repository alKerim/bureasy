import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import assistant
from app.routers import document

from app.models.database import init_db

# Initialize logger
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bureasy API",
    description="Bureasy API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Include routers
app.include_router(assistant.router)
app.include_router(document.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bureasy API!"}

@app.on_event("startup")
async def startup_event():
    init_db()
    
if __name__ == "__main__":
    uvicorn.run(app, host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, debug=settings.FASTAPI_DEBUG)
