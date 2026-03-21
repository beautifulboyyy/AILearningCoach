"""
RAG答案生成器模块
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.ai.rag.retriever import rag_retriever
from app.ai.rag.llm import llm
from app.ai.prompts.system_prompts import RAG_QA_SYSTEM_PROMPT
from app.utils.logger import app_logger


class RAGGenerator:
    """RAG答案生成器"""
    
    def __init__(self):
        self.retriever = rag_retriever
        self.llm = llm
    
    async def generate(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_messages: Optional[List[Dict[str, str]]] = None,
        extra_context: Optional[str] = None,
        top_k: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_hybrid: bool = True
    ) -> Dict[str, Any]:
        """
        生成答案（非流式）
        
        Args:
            query: 用户问题
            user_profile: 用户画像
            conversation_messages: 最近对话历史
            extra_context: 会话级补充上下文（短期记忆、摘要等）
            top_k: 检索结果数量
            temperature: 生成温度
            max_tokens: 最大token数
            use_hybrid: 是否使用混合检索（向量+关键词+Reranking）
        
        Returns:
            包含答案和来源的字典
        """
        # 1. 检索相关知识（使用混合检索优化）
        if use_hybrid:
            retrieval_results = await self.retriever.hybrid_retrieve(
                query=query,
                top_k=top_k,
                vector_weight=0.7,
                keyword_weight=0.3,
                use_rerank=True
            )
        else:
            retrieval_results = await self.retriever.retrieve(query, top_k=top_k)
        
        if not retrieval_results:
            app_logger.warning(f"未找到相关知识: {query}")
            return {
                "answer": "抱歉，我在课程知识库中没有找到相关内容。请尝试换个方式提问，或者检查问题是否在课程范围内。",
                "sources": [],
                "confidence": 0.0
            }
        
        # 2. 格式化上下文
        context = self.retriever.format_context(retrieval_results)
        
        # 3. 组装messages
        messages = self._build_messages(
            query=query,
            knowledge_context=context,
            user_profile=user_profile,
            conversation_messages=conversation_messages,
            extra_context=extra_context
        )

        # 4. 生成答案
        answer = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 5. 提取来源信息
        sources = self._extract_sources(retrieval_results)
        
        # 6. 计算置信度（基于检索结果的平均相似度）
        confidence = sum(r["distance"] for r in retrieval_results) / len(retrieval_results)
        
        app_logger.info(f"成功生成答案，置信度: {confidence:.2f}")
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": float(confidence)
        }
    
    async def generate_stream(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_messages: Optional[List[Dict[str, str]]] = None,
        extra_context: Optional[str] = None,
        top_k: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_hybrid: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成答案（流式）

        Args:
            query: 用户问题
            user_profile: 用户画像
            conversation_messages: 最近对话历史
            extra_context: 会话级补充上下文（短期记忆、摘要等）
            top_k: 检索结果数量
            temperature: 生成温度
            max_tokens: 最大token数
            use_hybrid: 是否使用混合检索

        Yields:
            答案片段和元数据
        """
        import asyncio

        # 1. 发送检索状态
        yield {
            "type": "status",
            "status": "retrieving",
            "message": "正在检索相关知识..."
        }
        await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

        # 2. 检索相关知识（使用混合检索）
        if use_hybrid:
            retrieval_results = await self.retriever.hybrid_retrieve(
                query=query,
                top_k=top_k,
                vector_weight=0.7,
                keyword_weight=0.3,
                use_rerank=True
            )
        else:
            retrieval_results = await self.retriever.retrieve(query, top_k=top_k)

        if not retrieval_results:
            # 知识库无结果时，使用 LLM 直接回答（流式）
            yield {
                "type": "metadata",
                "sources": [],
                "confidence": 0.0,
                "note": "知识库未找到相关内容，使用通用知识回答"
            }
            await asyncio.sleep(0)

            fallback_messages = self._build_messages(
                query=query,
                knowledge_context="",
                user_profile=user_profile,
                conversation_messages=conversation_messages,
                extra_context=(extra_context or "").strip()
            )

            async for chunk in self.llm.generate_stream(
                messages=fallback_messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield {
                    "type": "answer",
                    "content": chunk,
                    "done": False
                }

            yield {
                "type": "answer",
                "content": "",
                "done": True
            }
            app_logger.info("知识库无结果，使用通用知识流式回答完成")
            return

        # 3. 先发送来源信息
        sources = self._extract_sources(retrieval_results)
        confidence = sum(r["distance"] for r in retrieval_results) / len(retrieval_results)

        yield {
            "type": "metadata",
            "sources": sources,
            "confidence": float(confidence)
        }
        await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

        # 4. 发送生成状态
        yield {
            "type": "status",
            "status": "generating",
            "message": "正在生成回答..."
        }
        await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

        # 5. 格式化上下文
        context = self.retriever.format_context(retrieval_results)

        # 6. 组装messages
        messages = self._build_messages(
            query=query,
            knowledge_context=context,
            user_profile=user_profile,
            conversation_messages=conversation_messages,
            extra_context=extra_context
        )

        # 7. 流式生成答案
        async for chunk in self.llm.generate_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield {
                "type": "answer",
                "content": chunk,
                "done": False
            }
            # 不需要在每个chunk后sleep，LLM流式本身就是逐步返回的

        # 8. 发送完成信号
        yield {
            "type": "answer",
            "content": "",
            "done": True
        }

        app_logger.info("完成流式答案生成")
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取来源信息
        
        Args:
            results: 检索结果
        
        Returns:
            来源列表
        """
        sources = []
        for result in results:
            source = dict(result.get("source", {}))
            document_name = source.get("document_name", "未知文档")
            page = source.get("page")
            source["text"] = f"{document_name} (p.{page})" if page is not None else document_name
            source.setdefault("file_type", "unknown")
            source.setdefault("source_path", "")
            source.setdefault("assets", [])
            sources.append(source)
        
        return sources

    def _build_messages(
        self,
        query: str,
        knowledge_context: str,
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_messages: Optional[List[Dict[str, str]]] = None,
        extra_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        构建结构化messages：system + history + current user。
        """
        system_parts = [RAG_QA_SYSTEM_PROMPT]

        if user_profile:
            system_parts.append(
                "## 学习者信息\n"
                f"- 背景：{user_profile.get('occupation', '未知')}\n"
                f"- 技术水平：{user_profile.get('current_level', {})}\n"
                f"- 学习目标：{user_profile.get('learning_goal', '未知')}\n"
            )

        if extra_context:
            system_parts.append(f"## 会话补充上下文\n{extra_context}")

        if knowledge_context:
            system_parts.append(f"## 课程知识内容\n{knowledge_context}")

        system_parts.append("回答时请优先依据课程知识内容，必要时补充通用知识。")
        system_content = "\n\n".join(system_parts)

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
        if conversation_messages:
            for message in conversation_messages:
                role = message.get("role")
                content = message.get("content")
                if role in {"user", "assistant", "system"} and isinstance(content, str) and content.strip():
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": query})
        return messages


# 全局生成器实例
rag_generator = RAGGenerator()
