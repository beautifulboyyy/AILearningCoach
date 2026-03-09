from pydantic import BaseModel
from typing import List, Optional, Dict

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = []
    user_context: Optional[Dict] = {}
