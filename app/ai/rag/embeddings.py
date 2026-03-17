"""
向量化（Embedding）模块 - 使用通义千问
"""
from typing import List, Union
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.logger import app_logger


class DashScopeEmbedding:
    """通义千问 Embedding 封装"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = settings.EMBEDDING_MODEL
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        self.max_batch_size = 10
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def embed_text(self, text: str) -> List[float]:
        """
        向量化单个文本
        
        Args:
            text: 输入文本
        
        Returns:
            向量表示
        """
        return (await self.embed_texts([text]))[0]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        向量化单批文本（单次请求）
        
        Args:
            texts: 单批输入文本列表（长度不超过max_batch_size）
        
        Returns:
            向量表示列表
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "input": {
                "texts": texts
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                # 提取向量
                embeddings = []
                for item in result["output"]["embeddings"]:
                    embeddings.append(item["embedding"])
                
                app_logger.info(f"成功向量化 {len(texts)} 个文本")
                return embeddings
                
        except httpx.HTTPError as e:
            response_text = ""
            if isinstance(e, httpx.HTTPStatusError):
                response_text = e.response.text
            app_logger.error(f"调用通义千问Embedding API失败: {e}; 响应: {response_text[:300]}")
            raise
        except KeyError as e:
            app_logger.error(f"解析Embedding响应失败: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        向量化多个文本（自动分批）
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_embeddings = await self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
        return all_embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """
        向量化查询（与embed_text相同，但语义上更清晰）
        
        Args:
            query: 查询文本
        
        Returns:
            向量表示
        """
        return await self.embed_text(query)


# 全局Embedding实例
embedding_model = DashScopeEmbedding()
