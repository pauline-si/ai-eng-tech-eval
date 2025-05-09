"""
Pydantic models for chat
"""

from pydantic import BaseModel
from typing import List, Optional, Dict


class ChatRequest(BaseModel):
    message: str
    todo_list: Optional[List[Dict]]


class ChatResponse(BaseModel):
    response: str
    updated_todo_list: List[Dict]


class TTSRequest(BaseModel):
    text: str


class STTResponse(BaseModel):
    text: str
