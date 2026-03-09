"""
大语言模型（LLM）模块 - 使用DeepSeek
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.logger import app_logger


class DeepSeekLLM:
    """DeepSeek LLM 封装"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = settings.DEEPSEEK_MODEL
        self.api_url = f"{self.api_base}/v1/chat/completions"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        生成文本（非流式）
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数（0-2）
            max_tokens: 最大生成token数
        
        Returns:
            生成的文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                content = result["choices"][0]["message"]["content"]
                app_logger.info(f"成功生成回复，长度: {len(content)} 字符")
                
                return content
                
        except httpx.HTTPError as e:
            app_logger.error(f"调用DeepSeek API失败: {e}")
            raise
        except KeyError as e:
            app_logger.error(f"解析DeepSeek响应失败: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        生成文本（流式）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
        
        Yields:
            生成的文本片段
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self.api_url,
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # 移除 "data: " 前缀
                            
                            if data == "[DONE]":
                                break
                            
                            try:
                                import json
                                chunk = json.loads(data)
                                delta = chunk["choices"][0]["delta"]
                                
                                if "content" in delta:
                                    yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                            except (KeyError, IndexError):
                                continue
                
                app_logger.info("完成流式生成")
                
        except httpx.HTTPError as e:
            app_logger.error(f"调用DeepSeek流式API失败: {e}")
            raise
    
    async def chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        对话接口
        
        Args:
            user_message: 用户消息
            system_message: 系统消息（可选）
            history: 历史对话（可选）
            temperature: 温度参数
            max_tokens: 最大生成token数
        
        Returns:
            助手回复
        """
        messages = []
        
        # 添加系统消息
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # 添加历史对话
        if history:
            messages.extend(history)
        
        # 添加用户消息
        messages.append({"role": "user", "content": user_message})
        
        return await self.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )


# 全局LLM实例
llm = DeepSeekLLM()
