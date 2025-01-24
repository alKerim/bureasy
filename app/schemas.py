# app/schemas.py

from pydantic import BaseModel
from typing import Dict, Any

class SaveRequest(BaseModel):
    session_name: str
    transcriptions: Dict[str, Any]  # e.g. { "fasterwhisper": { "transcription": "...", "time": 1.23 }, ... }
    comparisons: Dict[str, Any]     # e.g. { "fasterwhisper": { "wer": 0.1, "cer": 0.05, "bleu": 0.8, "similarity": 0.9 }, ... }
