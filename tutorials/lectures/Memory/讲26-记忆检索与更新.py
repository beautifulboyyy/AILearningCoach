"""
讲26｜记忆检索与更新 - 实战案例：智能知识库

场景: 企业知识库,支持智能检索和自动更新

功能:
1. 添加文档时自动提取关键信息
2. 智能检索(混合检索+重要性排序)
3. 自动去重和合并
4. 检测知识更新并提示
5. 知识图谱关联

配置说明:
- LLM: DeepSeek-chat (通过OpenAI API兼容接口)
- 嵌入模型: 阿里云百炼 text-embedding-v3 (1024维)
- 向量存储: 内存存储(可选Qdrant)

环境变量要求 (.env文件):
- DEEPSEEK_API_KEY: DeepSeek API密钥
- OPENAI_BASE_URL: https://api.deepseek.com
- DASHSCOPE_API_KEY: 阿里云百炼API密钥

运行方式:
    python 讲26-记忆检索与更新.py

依赖安装:
    pip install openai mem0ai python-dotenv

注意事项:
- 如果使用Qdrant，需要先启动Qdrant服务: docker run -p 6333:6333 qdrant/qdrant
- 默认使用内存存储，适合演示和测试
- 生产环境建议使用Qdrant等持久化向量数据库
"""

from openai import OpenAI
from mem0 import Memory
import json
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ImportanceScorer:
    """重要性评分器 - 使用DeepSeek"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    
    def score(self, memory_text: str, user_context: Optional[str] = None) -> float:
        """
        使用LLM评估记忆重要性
        
        Args:
            memory_text: 记忆内容
            user_context: 用户背景信息（可选）
        
        Returns:
            重要性分数 (0-1)
        """
        context_info = f"\n用户背景: {user_context}" if user_context else ""
        
        prompt = f"""请评估以下记忆信息的重要性(0-10分)。

记忆内容: {memory_text}{context_info}

评分标准:
9-10分: 关键信息(身份、安全、核心偏好)
7-8分: 重要信息(工作、主要兴趣)
5-6分: 有用信息(一般偏好、事实)
3-4分: 次要信息(普通对话)
1-2分: 无关紧要(闲聊)

请直接返回分数(0-10的整数),无需解释。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            score_text = response.choices[0].message.content.strip()
            # 提取数字
            score_num = int(''.join(filter(str.isdigit, score_text)))
            score = min(max(score_num, 0), 10) / 10  # 归一化到0-1
            
            return score
        except Exception as e:
            print(f"评分出错: {e}")
            return 0.5  # 默认中等重要性


class ConflictDetector:
    """冲突检测器 - 使用DeepSeek"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    
    def detect_conflict(self, existing_memory: str, new_info: str) -> Dict:
        """
        检测两条信息是否冲突
        
        Args:
            existing_memory: 已有记忆
            new_info: 新信息
        
        Returns:
            冲突检测结果字典
        """
        prompt = f"""请分析两条信息是否冲突:

已有记忆: {existing_memory}
新信息: {new_info}

请判断:
1. 是否存在冲突?
2. 如果冲突,属于哪种类型?
   - correction: 纠正错误(如电话号码更换)
   - evolution: 偏好演化(如喜好改变)
   - refinement: 细化信息(如"工程师"→"Python工程师")
   - contradiction: 矛盾(如既喜欢又讨厌)
   - no_conflict: 无冲突

返回JSON格式:
{{
    "has_conflict": true/false,
    "conflict_type": "correction/evolution/refinement/contradiction/no_conflict",
    "explanation": "简短解释",
    "recommended_action": "update/merge/keep_both/ask_user"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"冲突检测出错: {e}")
            return {
                "has_conflict": False,
                "conflict_type": "no_conflict",
                "explanation": "检测失败",
                "recommended_action": "keep_both"
            }


class IntelligentKnowledgeBase:
    """智能知识库 - 使用DeepSeek + 阿里云嵌入模型"""
    
    def __init__(self, use_qdrant: bool = False):
        """
        初始化知识库系统
        
        Args:
            use_qdrant: 是否使用Qdrant向量数据库（False则使用内存存储）
        """
        # 配置OpenAI客户端使用DeepSeek
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        
        # 配置mem0使用阿里云百炼的嵌入模型
        config = {
            "embedder": {
                "provider": "openai",  # 使用openai兼容接口
                "config": {
                    "model": "text-embedding-v3",
                    "embedding_dims": 1024,
                    "api_key": os.getenv("DASHSCOPE_API_KEY"),
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "deepseek-chat",
                    "api_key": os.getenv("DEEPSEEK_API_KEY"),
                    "base_url": os.getenv("OPENAI_BASE_URL")
                }
            }
        }
        
        # 根据参数选择向量存储方式
        if use_qdrant:
            config["vector_store"] = {
                "provider": "qdrant",
                "config": {
                    "collection_name": "knowledge_base",
                    "host": "localhost",
                    "port": 6333,
                }
            }
            print("🗄️  使用Qdrant向量数据库")
        else:
            # 使用内存向量存储（适合演示和测试）
            print("💾 使用内存向量存储（适合演示）")
        
        try:
            self.memory = Memory.from_config(config)
            print("✅ mem0初始化成功")
            print(f"   - 嵌入模型: text-embedding-v3 (1024维)")
            print(f"   - LLM模型: deepseek-chat")
        except Exception as e:
            print(f"⚠️  mem0初始化失败: {e}")
            print("   使用默认配置...")
            self.memory = Memory()
        
        self.scorer = ImportanceScorer()
        self.conflict_detector = ConflictDetector()
    
    def add_document(self, document_text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        添加文档到知识库
        
        Args:
            document_text: 文档内容
            metadata: 元数据（如来源、作者等）
        
        Returns:
            添加结果统计
        """
        print(f"\n📄 正在处理文档...")
        
        # 1. 提取关键信息
        key_points = self._extract_key_points(document_text)
        print(f"✅ 提取了 {len(key_points)} 个关键要点")
        
        # 2. 为每个要点评分
        scored_points = []
        for point in key_points:
            importance = self.scorer.score(point)
            scored_points.append({
                "content": point,
                "importance": importance
            })
            print(f"   - {point[:50]}... (重要性: {importance:.2f})")
        
        # 3. 检查重复和冲突
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for point in scored_points:
            # 检索相似记忆
            try:
                existing = self.memory.search(
                    query=point["content"],
                    user_id="knowledge_base",
                    limit=3
                )
                
                if existing.get("results"):
                    # 检测冲突
                    conflict = self.conflict_detector.detect_conflict(
                        existing["results"][0]["memory"],
                        point["content"]
                    )
                    
                    if conflict["has_conflict"]:
                        # 处理冲突
                        self._handle_conflict(
                            conflict,
                            existing["results"][0]["id"],
                            point["content"],
                            point["importance"]
                        )
                        updated_count += 1
                        print(f"   🔄 更新: {point['content'][:50]}...")
                    else:
                        # 可能是重复,跳过
                        skipped_count += 1
                        print(f"   ⏭️  跳过: {point['content'][:50]}... (重复)")
                else:
                    # 新知识,添加
                    self._add_knowledge(point, metadata)
                    added_count += 1
                    print(f"   ✨ 添加: {point['content'][:50]}...")
            
            except Exception as e:
                print(f"   ⚠️  处理出错: {e}")
                # 出错时仍尝试添加
                try:
                    self._add_knowledge(point, metadata)
                    added_count += 1
                except:
                    skipped_count += 1
        
        result = {
            "total_points": len(key_points),
            "added": added_count,
            "updated": updated_count,
            "skipped": skipped_count
        }
        
        print(f"\n📊 处理完成: 总计{result['total_points']}个要点, 添加{result['added']}个, 更新{result['updated']}个, 跳过{result['skipped']}个")
        
        return result
    
    def _add_knowledge(self, point: Dict, metadata: Optional[Dict] = None):
        """添加单个知识点"""
        self.memory.add(
            messages=[{
                "role": "system",
                "content": point["content"]
            }],
            user_id="knowledge_base",
            metadata={
                "importance": point["importance"],
                "source": metadata.get("source") if metadata else None,
                "added_at": datetime.now().isoformat()
            }
        )
    
    def search_knowledge(self, query: str, top_k: int = 5, min_importance: float = 0.3) -> List[Dict]:
        """
        智能检索知识
        
        Args:
            query: 查询语句
            top_k: 返回结果数量
            min_importance: 最低重要性阈值
        
        Returns:
            检索结果列表
        """
        print(f"\n🔍 检索: {query}")
        
        try:
            # 1. 基础检索
            results = self.memory.search(
                query=query,
                user_id="knowledge_base",
                limit=top_k * 2  # 检索更多,然后过滤
            )
            
            if not results.get("results"):
                print("   ❌ 未找到相关知识")
                return []
            
            # 2. 过滤低重要性
            filtered = [
                r for r in results.get("results", [])
                if r.get("metadata", {}).get("importance", 0) >= min_importance
            ]
            
            # 3. 重新排序(考虑重要性)
            for result in filtered:
                semantic_score = result.get("score", 0.5)
                importance = result.get("metadata", {}).get("importance", 0.5)
                
                # 综合分数: 60%语义相似度 + 40%重要性
                result["final_score"] = 0.6 * semantic_score + 0.4 * importance
            
            filtered.sort(key=lambda r: r.get("final_score", 0), reverse=True)
            
            top_results = filtered[:top_k]
            
            print(f"   ✅ 找到 {len(top_results)} 条相关知识")
            
            return top_results
        
        except Exception as e:
            print(f"   ⚠️  检索出错: {e}")
            return []
    
    def _extract_key_points(self, document_text: str) -> List[str]:
        """
        从文档中提取关键要点
        
        Args:
            document_text: 文档内容
        
        Returns:
            关键要点列表
        """
        prompt = f"""请从以下文档中提取关键知识点:

{document_text}

要求:
1. 提取5-10个关键要点
2. 每个要点独立完整,可单独理解
3. 去除冗余信息
4. 保留重要细节(数据、日期、名称等)

返回JSON格式:
{{
    "key_points": ["要点1", "要点2", ...]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("key_points", [])
        
        except Exception as e:
            print(f"提取要点出错: {e}")
            return []
    
    def _handle_conflict(self, conflict: Dict, existing_id: str, new_content: str, importance: float):
        """
        处理冲突
        
        Args:
            conflict: 冲突信息
            existing_id: 已有记忆ID
            new_content: 新内容
            importance: 重要性分数
        """
        action = conflict.get("recommended_action")
        
        try:
            if action == "update":
                # 更新
                self.memory.update(
                    memory_id=existing_id,
                    data=new_content
                )
            elif action == "merge":
                # 合并 (简化版,直接更新)
                self.memory.update(
                    memory_id=existing_id,
                    data=new_content
                )
            # keep_both 或其他: 不做处理,让调用方添加新记忆
        except Exception as e:
            print(f"处理冲突出错: {e}")
    
    def get_statistics(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            all_memories = self.memory.get_all(user_id="knowledge_base")
            memories = all_memories.get("results", [])
            
            if not memories:
                return {
                    "total": 0,
                    "high_importance": 0,
                    "medium_importance": 0,
                    "low_importance": 0
                }
            
            # 按重要性分组
            high_importance = sum(
                1 for m in memories 
                if m.get("metadata", {}).get("importance", 0) >= 0.7
            )
            medium_importance = sum(
                1 for m in memories 
                if 0.4 <= m.get("metadata", {}).get("importance", 0) < 0.7
            )
            low_importance = sum(
                1 for m in memories 
                if m.get("metadata", {}).get("importance", 0) < 0.4
            )
            
            return {
                "total": len(memories),
                "high_importance": high_importance,
                "medium_importance": medium_importance,
                "low_importance": low_importance
            }
        
        except Exception as e:
            print(f"获取统计信息出错: {e}")
            return {
                "total": 0,
                "high_importance": 0,
                "medium_importance": 0,
                "low_importance": 0
            }
    
    def update_knowledge(self, knowledge_id: str, new_content: str):
        """更新知识"""
        try:
            self.memory.update(
                memory_id=knowledge_id,
                data=new_content
            )
            print(f"✅ 知识更新成功: {knowledge_id}")
        except Exception as e:
            print(f"❌ 更新失败: {e}")
    
    def delete_knowledge(self, knowledge_id: str):
        """删除知识"""
        try:
            self.memory.delete(memory_id=knowledge_id)
            print(f"✅ 知识删除成功: {knowledge_id}")
        except Exception as e:
            print(f"❌ 删除失败: {e}")


def demo_intelligent_knowledge_base():
    """演示智能知识库系统"""
    
    print("=" * 70)
    print("🎓 智能知识库系统演示")
    print("=" * 70)
    
    # 显示配置信息
    print("\n⚙️  系统配置:")
    print(f"   - LLM: DeepSeek-chat")
    print(f"   - 嵌入模型: 阿里云百炼 text-embedding-v3")
    print(f"   - 向量维度: 1024")
    print(f"   - API Base: {os.getenv('OPENAI_BASE_URL')}")
    print()
    
    # 初始化知识库（使用内存存储，适合演示）
    kb = IntelligentKnowledgeBase(use_qdrant=False)
    
    # 1. 添加第一份文档
    print("\n" + "=" * 70)
    print("📝 添加文档1: Python最佳实践")
    print("=" * 70)
    
    doc1 = """
    Python编程最佳实践:
    
    1. 使用虚拟环境管理依赖(venv或conda)
    2. 遵循PEP 8代码规范
    3. 使用类型提示(Type Hints)提高代码可读性
    4. 编写单元测试,测试覆盖率至少80%
    5. 使用日志记录而非print调试
    """
    
    result1 = kb.add_document(doc1, metadata={"source": "Python Guide"})
    
    # 2. 添加第二份文档(有部分重复)
    print("\n" + "=" * 70)
    print("📝 添加文档2: Python开发指南")
    print("=" * 70)
    
    doc2 = """
    Python开发建议:
    
    1. 始终使用虚拟环境
    2. 代码格式化使用Black工具
    3. 使用mypy进行类型检查
    4. 测试框架推荐pytest
    5. 异步编程使用asyncio
    """
    
    result2 = kb.add_document(doc2, metadata={"source": "Dev Guide"})
    
    # 3. 检索知识
    print("\n" + "=" * 70)
    print("🔍 知识检索测试")
    print("=" * 70)
    
    queries = [
        "如何管理Python依赖?",
        "Python测试的最佳实践是什么?",
        "如何提高代码质量?"
    ]
    
    for query in queries:
        results = kb.search_knowledge(query, top_k=3)
        
        if results:
            print(f"\n📋 查询结果 (Top {len(results)}):")
            for i, result in enumerate(results, 1):
                memory = result.get('memory', 'N/A')
                final_score = result.get('final_score', 0)
                importance = result.get('metadata', {}).get('importance', 0)
                
                print(f"\n   {i}. {memory}")
                print(f"      综合分数: {final_score:.2f} | 重要性: {importance:.2f}")
    
    # 4. 统计信息
    print("\n" + "=" * 70)
    print("📊 知识库统计")
    print("=" * 70)
    
    stats = kb.get_statistics()
    print(f"\n📈 知识库概况:")
    print(f"   总知识点: {stats['total']}")
    print(f"   高重要性 (≥0.7): {stats['high_importance']}")
    print(f"   中重要性 (0.4-0.7): {stats['medium_importance']}")
    print(f"   低重要性 (<0.4): {stats['low_importance']}")
    
    print("\n" + "=" * 70)
    print("✅ 演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    # 运行演示
    demo_intelligent_knowledge_base()
