"""
Agent管理相关API
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.deps import get_current_active_user
from app.models.user import User
from app.ai.agents.orchestrator import agent_orchestrator
from typing import List, Dict, Optional

router = APIRouter()


class IntentRequest(BaseModel):
    """意图识别请求"""
    message: str
    context: Optional[Dict] = None


@router.get("/list")
async def list_agents(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取可用的Agent列表
    """
    agents = agent_orchestrator.get_available_agents()
    
    return {
        "total": len(agents),
        "agents": agents
    }


@router.post("/intent")
async def identify_intent(
    request: IntentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    测试意图识别
    
    用于调试和测试意图识别功能
    
    请求体示例:
    ```json
    {
        "message": "什么是RAG？",
        "context": {}
    }
    ```
    """
    intent_result = await agent_orchestrator.identify_intent(request.message)
    
    return intent_result
