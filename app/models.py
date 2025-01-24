# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class TranscriptionResult(Base):
    __tablename__ = "transcription_results"

    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String, index=True)  # The "name" user typed in the pop-up
    method = Column(String, index=True)        # "fasterwhisper", "whisper", etc.
    time_s = Column(Float)                     # In seconds
    transcription = Column(String)             # The transcribed text
    wer = Column(Float)
    cer = Column(Float)
    bleu = Column(Float)
    similarity = Column(Float)

    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
