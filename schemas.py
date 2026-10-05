from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=120)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ChatIn(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: Optional[int] = None
    agent: str = "general"

class MemoryIn(BaseModel):
    content: str = Field(min_length=1)

class TaskIn(BaseModel):
    title: str
    description: str = ""
    due_date: str = ""
    priority: str = "medium"

class TaskUpdate(BaseModel):
    status: str

class DocumentQuery(BaseModel):
    query: str
    top_k: int = 5
