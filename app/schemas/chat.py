"""
对话Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色：user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID（可选，用于继续对话）")
    stream: bool = Field(False, description="是否使用流式输出")
    top_k: int = Field(3, ge=1, le=10, description="检索结果数量")
    temperature: float = Field(0.7, ge=0, le=2, description="生成温度")


class Source(BaseModel):
    """知识来源"""
    document_name: str = Field(..., description="文档名")
    file_type: str = Field(..., description="文件类型")
    page: Optional[int] = Field(None, description="页码")
    source_path: str = Field(..., description="来源路径")
    assets: List[Dict[str, Any]] = Field(default_factory=list, description="关联资产列表")
    text: str = Field(..., description="来源文本描述")


class ChatResponse(BaseModel):
    """对话响应"""
    message: str = Field(..., description="助手回复")
    session_id: str = Field(..., description="会话ID")
    sources: List[Source] = Field(default_factory=list, description="知识来源")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    message_id: int = Field(..., description="消息ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class ChatHistory(BaseModel):
    """对话历史"""
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    message_count: int


class StreamChatChunk(BaseModel):
    """流式对话片段"""
    type: str = Field(..., description="类型：metadata/answer")
    content: Optional[str] = Field(None, description="内容片段")
    done: Optional[bool] = Field(None, description="是否完成")
    sources: Optional[List[Source]] = Field(None, description="知识来源")
    confidence: Optional[float] = Field(None, description="置信度")
