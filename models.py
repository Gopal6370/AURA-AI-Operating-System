from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from .db import Base

def now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(512), nullable=False)
    name = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=now)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200), default="New conversation")
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)
    agent = Column(String(50), default="general")
    created_at = Column(DateTime, default=now)

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    due_date = Column(String(50), default="")
    priority = Column(String(30), default="medium")
    status = Column(String(30), default="todo")
    created_at = Column(DateTime, default=now)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    filename = Column(String(255), nullable=False)
    page = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)
