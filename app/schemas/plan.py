from pydantic import BaseModel
from typing import Dict

class PlanCreateRequest(BaseModel):
    background: Dict
    target: str
