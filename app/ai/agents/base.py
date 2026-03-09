"""
Agent基类
"""
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.utils.logger import app_logger


@dataclass
class AgentTool:
    """Agent工具定义"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str, description: str):
        """
        初始化Agent

        Args:
            name: Agent名称
            description: Agent描述
        """
        self.name = name
        self.description = description
        self.tools: List[AgentTool] = []
    
    def register_tool(self, tool: AgentTool):
        """
        注册工具
        
        Args:
            tool: 工具对象
        """
        self.tools.append(tool)
        app_logger.info(f"Agent {self.name} 注册工具: {tool.name}")
    
    def get_tools_description(self) -> str:
        """
        获取工具描述（用于Prompt）
        
        Returns:
            工具描述文本
        """
        if not self.tools:
            return "此Agent没有可用工具。"
        
        descriptions = []
        for tool in self.tools:
            descriptions.append(
                f"- {tool.name}: {tool.description}"
            )
        
        return "\n".join(descriptions)
    
    @abstractmethod
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理用户输入

        Args:
            user_input: 用户输入
            context: 上下文信息（包含user_id、session_id、user_profile等）

        Returns:
            处理结果
        """
        pass

    async def process_stream(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理用户输入（默认实现：调用非流式方法并分块返回）

        Args:
            user_input: 用户输入
            context: 上下文信息

        Yields:
            处理结果片段
        """
        # 默认实现：调用非流式 process 方法
        result = await self.process(user_input, context)

        # 流式返回答案
        answer = result.get("answer", "")
        chunk_size = 10

        # 先发送元数据
        yield {
            "type": "metadata",
            "agent": self.name,
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0)
        }

        # 分块发送答案
        for i in range(0, len(answer), chunk_size):
            yield {
                "type": "answer",
                "content": answer[i:i + chunk_size],
                "done": False
            }

        # 发送完成信号
        yield {
            "type": "answer",
            "content": "",
            "done": True
        }
    
    async def call_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
        
        Returns:
            工具返回结果
        """
        tool = next((t for t in self.tools if t.name == tool_name), None)
        
        if not tool:
            raise ValueError(f"工具不存在: {tool_name}")
        
        try:
            result = await tool.function(**kwargs)
            app_logger.info(f"Agent {self.name} 调用工具 {tool_name} 成功")
            return result
        except Exception as e:
            app_logger.error(f"Agent {self.name} 调用工具 {tool_name} 失败: {e}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取Agent信息
        
        Returns:
            Agent信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "tools": [t.name for t in self.tools],
            "tools_count": len(self.tools)
        }
