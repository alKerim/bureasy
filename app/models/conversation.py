from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    flow_type = Column(String, index=True)  # e.g., "visa_extension"
    state_index = Column(Integer, default=0)  # Tracks which question index we are on in the flow

    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # e.g., "user" or "assistant"
    content = Column(String)

    conversation = relationship("Conversation", back_populates="messages")
