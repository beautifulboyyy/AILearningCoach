"""
记忆管理器模块
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.memory import Memory, MemoryType
from app.ai.rag.embeddings import embedding_model
from app.ai.rag.milvus_client import milvus_client
from app.utils.cache import cache_set, cache_get, cache_set_hash, cache_get_hash, cache_get_all_hash
from app.utils.logger import app_logger
import json


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self):
        self.embedding = embedding_model
        self.milvus = milvus_client
    
    async def save_short_term_memory(
        self,
        user_id: int,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        保存短期记忆到Redis
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            content: 记忆内容
            metadata: 元数据
        
        Returns:
            是否成功
        """
        try:
            # 使用Hash存储会话记忆
            cache_key = f"session:{session_id}:memory"
            timestamp = datetime.utcnow().isoformat()
            
            memory_data = {
                "content": content,
                "metadata": metadata or {},
                "timestamp": timestamp
            }
            
            # 添加到会话记忆列表
            await cache_set_hash(cache_key, timestamp, json.dumps(memory_data, ensure_ascii=False))
            
            # 设置2小时过期
            from app.utils.cache import get_redis
            redis = await get_redis()
            await redis.expire(cache_key, 7200)
            
            app_logger.info(f"保存短期记忆: user_id={user_id}, session_id={session_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"保存短期记忆失败: {e}")
            return False
    
    async def get_short_term_memory(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取短期记忆（当前会话）
        
        Args:
            session_id: 会话ID
        
        Returns:
            记忆列表
        """
        try:
            cache_key = f"session:{session_id}:memory"
            memory_hash = await cache_get_all_hash(cache_key)
            
            if not memory_hash:
                return []
            
            # 解析并排序
            memories = []
            for timestamp, data in memory_hash.items():
                try:
                    memory_data = json.loads(data)
                    memory_data["timestamp"] = timestamp
                    memories.append(memory_data)
                except json.JSONDecodeError:
                    continue
            
            # 按时间排序
            memories.sort(key=lambda x: x["timestamp"])
            
            app_logger.info(f"获取短期记忆: session_id={session_id}, 数量={len(memories)}")
            return memories
            
        except Exception as e:
            app_logger.error(f"获取短期记忆失败: {e}")
            return []
    
    async def save_working_memory(
        self,
        user_id: int,
        content: str,
        db: AsyncSession
    ) -> Memory:
        """
        保存工作记忆（7天）
        
        Args:
            user_id: 用户ID
            content: 记忆内容
            db: 数据库会话
        
        Returns:
            记忆对象
        """
        try:
            # 设置7天后过期
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            memory = Memory(
                user_id=user_id,
                memory_type=MemoryType.WORKING,
                content=content,
                importance_score=0.5,
                expires_at=expires_at
            )
            
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            app_logger.info(f"保存工作记忆: user_id={user_id}, memory_id={memory.id}")
            return memory
            
        except Exception as e:
            app_logger.error(f"保存工作记忆失败: {e}")
            raise
    
    async def get_working_memory(
        self,
        user_id: int,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Memory]:
        """
        获取工作记忆（最近7天）
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            limit: 最大返回数量
        
        Returns:
            记忆列表
        """
        try:
            # 查询未过期的工作记忆
            result = await db.execute(
                select(Memory).filter(
                    and_(
                        Memory.user_id == user_id,
                        Memory.memory_type == MemoryType.WORKING,
                        Memory.expires_at > datetime.utcnow()
                    )
                ).order_by(Memory.created_at.desc()).limit(limit)
            )
            
            memories = result.scalars().all()
            app_logger.info(f"获取工作记忆: user_id={user_id}, 数量={len(memories)}")
            
            return list(memories)
            
        except Exception as e:
            app_logger.error(f"获取工作记忆失败: {e}")
            return []
    
    async def save_long_term_memory(
        self,
        user_id: int,
        content: str,
        importance_score: float,
        db: AsyncSession
    ) -> Memory:
        """
        保存长期记忆
        
        Args:
            user_id: 用户ID
            content: 记忆内容
            importance_score: 重要性评分
            db: 数据库会话
        
        Returns:
            记忆对象
        """
        try:
            # 向量化内容
            embedding = await self.embedding.embed_text(content)
            
            # 生成向量ID
            vector_id = f"memory_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            # 保存到Milvus（使用知识库集合，加上user_id区分）
            try:
                self.milvus.connect()
                collection = self.milvus.get_collection()
                
                # 插入向量数据
                self.milvus.insert([{
                    "vector_id": vector_id,
                    "content": content[:8000],  # Milvus字段限制
                    "embedding": embedding,
                    "metadata": {
                        "type": "memory",
                        "user_id": user_id,
                        "importance_score": importance_score,
                        "created_at": datetime.utcnow().isoformat()
                    }
                }])
                
                app_logger.info(f"记忆向量已存储到Milvus: vector_id={vector_id}")
                
            except Exception as e:
                app_logger.warning(f"向量存储到Milvus失败，降级为仅PostgreSQL: {e}")
                # 如果Milvus失败，继续保存到PostgreSQL
            
            # 保存元数据到PostgreSQL
            memory = Memory(
                user_id=user_id,
                memory_type=MemoryType.LONG_TERM,
                content=content,
                vector_id=vector_id,
                importance_score=importance_score,
                expires_at=None  # 长期记忆不过期
            )
            
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            app_logger.info(f"保存长期记忆: user_id={user_id}, memory_id={memory.id}")
            return memory
            
        except Exception as e:
            app_logger.error(f"保存长期记忆失败: {e}")
            raise
    
    async def search_long_term_memory(
        self,
        user_id: int,
        query: str,
        db: AsyncSession,
        top_k: int = 5
    ) -> List[Memory]:
        """
        搜索长期记忆（使用向量语义检索 + 时间衰减）
        
        Args:
            user_id: 用户ID
            query: 查询文本
            db: 数据库会话
            top_k: 返回数量
        
        Returns:
            相关记忆列表
        """
        try:
            # 1. 向量化查询
            query_embedding = await self.embedding.embed_query(query)
            
            # 2. 从Milvus检索（过滤用户的记忆）
            try:
                self.milvus.connect()
                
                # 构建过滤表达式（只检索该用户的记忆）
                filter_expr = f"metadata['type'] == 'memory' and metadata['user_id'] == {user_id}"
                
                search_results = self.milvus.search(
                    query_embedding=query_embedding,
                    top_k=top_k * 2,  # 多检索一些用于时间衰减过滤
                    filter_expr=filter_expr
                )
                
                # 3. 从PostgreSQL获取记忆详情
                vector_ids = [r["vector_id"] for r in search_results]
                
                if not vector_ids:
                    app_logger.warning(f"向量检索未找到记忆: user_id={user_id}")
                    return []
                
                result = await db.execute(
                    select(Memory).filter(
                        and_(
                            Memory.user_id == user_id,
                            Memory.vector_id.in_(vector_ids)
                        )
                    )
                )
                memories_dict = {m.vector_id: m for m in result.scalars().all()}
                
                # 4. 应用时间衰减和排序
                scored_memories = []
                for search_result in search_results:
                    vector_id = search_result["vector_id"]
                    if vector_id not in memories_dict:
                        continue
                    
                    memory = memories_dict[vector_id]
                    
                    # 计算时间衰减分数
                    age_days = (datetime.utcnow() - memory.created_at).days
                    time_decay = 1.0 / (1.0 + age_days / 30.0)  # 30天衰减50%
                    
                    # 综合分数 = 向量相似度 * 时间衰减 * 重要性
                    combined_score = (
                        search_result["distance"] * 
                        time_decay * 
                        memory.importance_score
                    )
                    
                    scored_memories.append((memory, combined_score))
                
                # 按综合分数排序
                scored_memories.sort(key=lambda x: x[1], reverse=True)
                result_memories = [m for m, _ in scored_memories[:top_k]]
                
                # 更新访问时间
                for memory in result_memories:
                    memory.last_accessed = datetime.utcnow()
                await db.commit()
                
                app_logger.info(f"搜索长期记忆（向量+时间衰减）: user_id={user_id}, 找到={len(result_memories)}条")
                return result_memories
                
            except Exception as e:
                app_logger.warning(f"向量检索失败，降级为数据库查询: {e}")
                
                # 降级方案：直接从数据库查询
                result = await db.execute(
                    select(Memory).filter(
                        and_(
                            Memory.user_id == user_id,
                            Memory.memory_type == MemoryType.LONG_TERM
                        )
                    ).order_by(Memory.last_accessed.desc()).limit(top_k)
                )
                
                memories = result.scalars().all()
                
                # 更新访问时间
                for memory in memories:
                    memory.last_accessed = datetime.utcnow()
                await db.commit()
                
                app_logger.info(f"搜索长期记忆（降级模式）: user_id={user_id}, 找到={len(memories)}条")
                return list(memories)
            
        except Exception as e:
            app_logger.error(f"搜索长期记忆失败: {e}")
            return []
    
    async def cleanup_expired_memories(self, db: AsyncSession):
        """
        清理过期记忆
        
        Args:
            db: 数据库会话
        """
        try:
            result = await db.execute(
                select(Memory).filter(
                    and_(
                        Memory.expires_at.isnot(None),
                        Memory.expires_at < datetime.utcnow()
                    )
                )
            )
            
            expired_memories = result.scalars().all()
            
            for memory in expired_memories:
                await db.delete(memory)
            
            await db.commit()
            
            app_logger.info(f"清理过期记忆: 数量={len(expired_memories)}")
            
        except Exception as e:
            app_logger.error(f"清理过期记忆失败: {e}")


# 全局记忆管理器实例
memory_manager = MemoryManager()
