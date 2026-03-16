"""
讲24｜记忆系统架构 - 练习：构建个性化推荐系统

功能：
1. 记录用户对内容的评分（1-5星）
2. 自动提取用户的兴趣偏好
3. 基于记忆推荐新内容
4. 避免推荐已看过的内容
5. 根据用户反馈持续优化

技术栈：
- mem0：记忆管理
- 支持配置向量数据库（Qdrant/Chroma/Pinecone）
- 支持配置LLM（OpenAI/其他）
"""

from mem0 import Memory
from openai import OpenAI
from typing import List, Dict, Optional
import json
from datetime import datetime
from dotenv import load_dotenv

_ = load_dotenv()


class PersonalizedRecommendationSystem:
    """个性化推荐系统（基于mem0）"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化推荐系统
        
        Args:
            config: 配置字典，包含LLM和向量数据库配置
                {
                    "llm": {
                        "provider": "openai",  # 或 "anthropic", "ollama" 等
                        "config": {
                            "model": "gpt-4o-mini",
                            "temperature": 0,
                            "api_key": "your-api-key"  # 可选，默认从环境变量读取
                        }
                    },
                    "vector_store": {
                        "provider": "qdrant",  # 或 "chroma", "pinecone" 等
                        "config": {
                            "host": "localhost",
                            "port": 6333
                        }
                    },
                    "embedder": {
                        "provider": "openai",
                        "config": {
                            "model": "text-embedding-3-small"
                        }
                    }
                }
        """
        # 配置LLM和向量数据库
        if config:
            self.memory = Memory.from_config(config)
        else:
            # 默认配置（使用OpenAI和默认向量数据库）
            self.memory = Memory()


        # OpenAI客户端用于生成推荐
        self.openai_client = OpenAI()
        self.model = config.get("llm", {}).get("config", {}).get("model", "gpt-4o-mini") if config else "gpt-4o-mini"

        # 内容库（模拟数据）
        self.articles = [
            {"id": 1, "title": "Python编程入门", "category": "编程", "tags": ["Python", "入门", "编程"]},
            {"id": 2, "title": "机器学习基础", "category": "AI", "tags": ["机器学习", "AI", "入门"]},
            {"id": 3, "title": "深度学习与神经网络", "category": "AI", "tags": ["深度学习", "神经网络", "进阶"]},
            {"id": 4, "title": "大语言模型详解", "category": "AI", "tags": ["LLM", "Transformer", "进阶"]},
            {"id": 5, "title": "Prompt工程实战", "category": "AI", "tags": ["Prompt", "LLM", "实战"]},
            {"id": 6, "title": "旅行攻略：日本篇", "category": "旅游", "tags": ["旅游", "日本", "攻略"]},
            {"id": 7, "title": "摄影技巧入门", "category": "摄影", "tags": ["摄影", "入门", "技巧"]},
            {"id": 8, "title": "健康饮食指南", "category": "健康", "tags": ["健康", "饮食", "生活"]},
            {"id": 9, "title": "Transformer架构详解", "category": "AI", "tags": ["Transformer", "架构", "深度学习"]},
            {"id": 10, "title": "RAG系统设计", "category": "AI", "tags": ["RAG", "LLM", "应用"]},
            {"id": 11, "title": "JavaScript前端开发", "category": "编程", "tags": ["JavaScript", "前端", "Web"]},
            {"id": 12, "title": "数据结构与算法", "category": "编程", "tags": ["算法", "数据结构", "基础"]},
            {"id": 13, "title": "云计算入门", "category": "技术", "tags": ["云计算", "AWS", "入门"]},
            {"id": 14, "title": "Docker容器化实践", "category": "技术", "tags": ["Docker", "容器", "DevOps"]},
            {"id": 15, "title": "创业心得分享", "category": "创业", "tags": ["创业", "管理", "经验"]},
        ]

    def record_rating(self, user_id: str, article_id: int, rating: int, comment: str = ""):
        """
        记录用户对文章的评分
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
            rating: 评分（1-5星）
            comment: 评论（可选）
        """
        if rating < 1 or rating > 5:
            raise ValueError("评分必须在1-5之间")

        # 获取文章信息
        article = self._get_article_by_id(article_id)
        if not article:
            raise ValueError(f"文章ID {article_id} 不存在")

        # 构建记忆消息
        message = f"""用户对文章《{article['title']}》的评价：
评分：{rating}/5
类别：{article['category']}
标签：{', '.join(article['tags'])}
评论：{comment if comment else '无'}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"""

        # 添加到记忆系统
        result = self.memory.add(
            messages=[{"role": "user", "content": message}],
            user_id=user_id
        )

        print(f"✓ 评分记录: {rating}星 - 《{article['title']}》")
        return result

    def record_article_read(self, user_id: str, article_id: int):
        """
        记录用户阅读了某篇文章
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
        """
        article = self._get_article_by_id(article_id)
        if not article:
            raise ValueError(f"文章ID {article_id} 不存在")

        message = f"""用户阅读了文章：
标题：{article['title']}
类别：{article['category']}
标签：{', '.join(article['tags'])}
时间：{datetime.now().strftime('%Y-%m-%d')}"""

        result = self.memory.add(
            messages=[{"role": "user", "content": message}],
            user_id=user_id
        )

        print(f"✓ 阅读记录: 《{article['title']}》")
        return result

    def get_recommendations(self, user_id: str, count: int = 5) -> List[Dict]:
        """
        基于用户记忆推荐内容
        
        Args:
            user_id: 用户ID
            count: 推荐数量
            
        Returns:
            推荐文章列表
        """

        # 1. 获取用户的所有记忆
        all_memories = self.memory.get_all(user_id=user_id)
        memories = all_memories.get("results", [])

        if not memories:
            return self.articles[:count]

        # 2. 分析用户画像
        user_profile = self._analyze_user_profile(memories)

        # 3. 提取已读文章
        read_articles = self._extract_read_articles(memories)

        # 4. 基于记忆生成推荐
        recommendations = self._generate_recommendations(
            user_profile,
            read_articles,
            count
        )

        return recommendations

    def _analyze_user_profile(self, memories: List[Dict]) -> Dict:
        """
        分析用户画像
        
        Args:
            memories: 用户的所有记忆
            
        Returns:
            用户画像字典
        """
        memories_text = "\n".join([
            f"- {mem['memory']}" for mem in memories
        ])

        prompt = f"""基于以下用户记忆，分析用户的阅读画像：

用户记忆：
{memories_text}

请以JSON格式输出：
{{
    "interests": ["兴趣1", "兴趣2", ...],
    "categories": ["类别1", "类别2", ...],
    "preferred_difficulty": "入门|中级|进阶",
    "high_rated_topics": ["高评分主题1", "主题2", ...],
    "tags": ["标签1", "标签2", ...]
}}

只输出JSON，不要其他说明。"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )

            profile = json.loads(response.choices[0].message.content)
            return profile
        except Exception as e:
            return {"interests": [], "categories": [], "tags": []}

    def _extract_read_articles(self, memories: List[Dict]) -> List[str]:
        """
        从记忆中提取已读文章标题
        
        Args:
            memories: 用户的所有记忆
            
        Returns:
            已读文章标题列表
        """
        read_articles = []
        for mem in memories:
            text = mem['memory'].lower()
            if '阅读' in text or '读过' in text or '看过' in text:
                # 尝试从记忆中提取文章标题
                for article in self.articles:
                    if article['title'].lower() in text or article['title'] in mem['memory']:
                        read_articles.append(article['title'])

        read_articles = list(set(read_articles))  # 去重
        return read_articles

    def _generate_recommendations(
            self,
            user_profile: Dict,
            read_articles: List[str],
            count: int
    ) -> List[Dict]:
        """
        生成推荐列表
        
        Args:
            user_profile: 用户画像
            read_articles: 已读文章
            count: 推荐数量
            
        Returns:
            推荐文章列表
        """
        # 过滤已读文章
        candidate_articles = [
            article for article in self.articles
            if article['title'] not in read_articles
        ]

        if not candidate_articles:
            print("所有文章都已阅读！")
            return []

        # 计算每篇文章的匹配分数
        scored_articles = []
        user_interests = user_profile.get('interests', [])
        user_categories = user_profile.get('categories', [])
        user_tags = user_profile.get('tags', [])

        for article in candidate_articles:
            score = 0.0

            # 1. 类别匹配（权重：0.4）
            if article['category'] in user_categories:
                score += 0.4

            # 2. 标签匹配（权重：0.4）
            tag_matches = sum(1 for tag in article['tags'] if tag in user_tags or tag in user_interests)
            score += 0.4 * min(tag_matches / 3, 1.0)  # 归一化

            # 3. 关键词匹配（权重：0.2）
            title_lower = article['title'].lower()
            keyword_matches = sum(1 for interest in user_interests if interest.lower() in title_lower)
            score += 0.2 * min(keyword_matches / 2, 1.0)

            scored_articles.append((article, score))

        # 按分数排序
        scored_articles.sort(key=lambda x: x[1], reverse=True)

        # 返回前N篇
        recommendations = [article for article, score in scored_articles[:count]]

        print(f"\n推荐结果:")
        for i, article in enumerate(recommendations, 1):
            print(f"  {i}. 《{article['title']}》 - {article['category']}")

        return recommendations

    def chat(self, user_id: str, message: str) -> str:
        """
        与用户对话，支持记忆功能
        
        Args:
            user_id: 用户ID
            message: 用户消息
            
        Returns:
            AI回复
        """
        # 1. 检索相关记忆
        relevant_memories = self.memory.search(
            query=message,
            user_id=user_id,
            limit=5
        )

        memories = relevant_memories.get("results", [])
        memories_text = "\n".join([
            f"- {mem['memory']}" for mem in memories
        ]) if memories else "暂无用户记忆"

        # 2. 构建系统提示
        system_prompt = f"""你是一个个性化内容推荐助手，能够记住用户的阅读偏好和历史。

用户记忆：
{memories_text}

你的任务：
1. 根据用户的兴趣和历史推荐相关内容
2. 避免推荐用户已读过的内容
3. 记录用户的反馈并理解其偏好
4. 提供友好、个性化的建议

请简洁、友好地回复用户。"""

        # 3. 调用LLM生成回复
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=chat_messages
        )

        assistant_response = response.choices[0].message.content

        # 4. 保存对话到记忆
        conversation = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": assistant_response}
        ]
        self.memory.add(messages=conversation, user_id=user_id)

        return assistant_response

    def get_user_profile(self, user_id: str) -> Dict:
        """
        获取用户的详细画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户画像字典
        """
        # 获取所有记忆
        all_memories = self.memory.get_all(user_id=user_id)
        memories = all_memories.get("results", [])

        if not memories:
            return {
                "user_id": user_id,
                "total_memories": 0,
                "profile": "用户暂无记忆"
            }

        # 使用LLM生成画像
        memories_text = "\n".join([
            f"- {mem['memory']}" for mem in memories
        ])

        prompt = f"""基于以下用户记忆，生成用户的详细阅读画像：

{memories_text}

请以JSON格式输出：
{{
    "interests": ["兴趣领域1", "兴趣领域2", ...],
    "reading_preferences": {{
        "content_depth": "入门级|中级|高级",
        "content_types": ["类型1", "类型2", ...],
        "feedback_style": "喜好描述"
    }},
    "read_articles": ["已读文章1", "已读文章2", ...],
    "high_rated_articles": ["高评分文章1", "文章2", ...],
    "recommendation_strategy": "推荐策略描述"
}}

只输出JSON。"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            profile = json.loads(response.choices[0].message.content)
            profile["user_id"] = user_id
            profile["total_memories"] = len(memories)

            return profile
        except Exception as e:
            return {
                "user_id": user_id,
                "total_memories": len(memories),
                "error": str(e)
            }

    def show_user_memories(self, user_id: str):
        """
        展示用户的所有记忆
        
        Args:
            user_id: 用户ID
        """
        all_memories = self.memory.get_all(user_id=user_id)
        memories = all_memories.get("results", [])

        print(f"\n用户记忆 (共{len(memories)}条):")

        if memories:
            for i, mem in enumerate(memories, 1):
                print(f"  {i}. {mem['memory']}")
        else:
            print("  暂无记忆")

    def delete_memory(self, memory_id: str):
        """
        删除指定记忆
        
        Args:
            memory_id: 记忆ID
        """
        self.memory.delete(memory_id=memory_id)
        print(f"✓ 已删除")

    def reset_user_memories(self, user_id: str):
        """
        重置用户的所有记忆
        
        Args:
            user_id: 用户ID
        """
        self.memory.delete_all(user_id=user_id)
        print(f"✓ 已清空所有记忆")

    def _get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """获取文章信息"""
        for article in self.articles:
            if article['id'] == article_id:
                return article
        return None

    def list_all_articles(self):
        """列出所有可用文章"""
        print(f"\n内容库:")

        # 按类别分组
        by_category = {}
        for article in self.articles:
            category = article['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(article)

        # 显示
        for category, articles in by_category.items():
            print(f"\n【{category}】")
            for article in articles:
                print(f"  {article['id']:2d}. {article['title']}")


custom_config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0,
            "api_key": "sk-f44d19e89dd5485eb87bf6a9fb187762",
            "openai_base_url": "https://api.deepseek.com"
        }
    },
    "vector_store": {
        "provider": "milvus",  # 可改为 "chroma", "pinecone" 等
        "config": {
            "url": "http://211.65.101.204:19530",
            "collection_name": "recommendation_memories",
            "embedding_model_dims": 1024,
            "token": ""
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-v3",
            "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "sk-495baeee133449f786482a6df55058ef",
            "embedding_dims": 1024
        }
    }
}


def demo_basic_usage():
    """演示基础使用"""
    print("\n" + "=" * 50)
    print("演示1: 基础使用")
    print("=" * 50)

    system = PersonalizedRecommendationSystem(custom_config)
    user_id = "user_demo1"

    # 表达兴趣
    print("\n[1] 表达兴趣")
    response = system.chat(user_id, "我对AI和大语言模型很感兴趣")
    print(f"AI: {response}")

    # 记录阅读
    print("\n[2] 记录阅读")
    system.record_article_read(user_id, 2)
    system.record_article_read(user_id, 9)

    # 记录评分
    print("\n[3] 记录评分")
    system.record_rating(user_id, 9, 5, "很棒")
    system.record_rating(user_id, 2, 4)

    # 获取推荐
    print("\n[4] 获取推荐")
    recommendations = system.get_recommendations(user_id, count=3)

    # 查看画像
    print("\n[5] 用户画像")
    profile = system.get_user_profile(user_id)
    print(f"兴趣: {', '.join(profile.get('interests', []))}")
    print(f"已读: {len(profile.get('read_articles', []))}篇")


def demo_custom_config():
    """演示自定义配置"""
    print("\n" + "=" * 50)
    print("演示2: 自定义配置")
    print("=" * 50)

    print(f"\nLLM: {custom_config['llm']['config']['model']}")
    print(f"向量库: {custom_config['vector_store']['provider']}")

    try:
        system = PersonalizedRecommendationSystem(config=custom_config)
        print("✓ 初始化成功")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        system = PersonalizedRecommendationSystem()


def demo_multi_user():
    """演示多用户场景"""
    print("\n" + "=" * 50)
    print("演示3: 多用户场景")
    print("=" * 50)

    system = PersonalizedRecommendationSystem(custom_config)

    # 用户1
    print("\n[用户1] AI研究员")
    user1 = "user_ai_lover"
    system.chat(user1, "我是AI研究员，专注深度学习")
    system.record_rating(user1, 3, 5)
    recs1 = system.get_recommendations(user1, count=3)

    # 用户2
    print("\n[用户2] 编程初学者")
    user2 = "user_beginner"
    system.chat(user2, "我是编程新手，想学Python")
    system.record_rating(user2, 1, 4)
    recs2 = system.get_recommendations(user2, count=3)


def demo_memory_management():
    """演示记忆管理"""
    print("\n" + "=" * 50)
    print("演示4: 记忆管理")
    print("=" * 50)

    system = PersonalizedRecommendationSystem(custom_config)
    user_id = "user_memory_test"

    print("\n[1] 添加记忆")
    system.chat(user_id, "我喜欢技术类文章")
    system.record_rating(user_id, 4, 5)

    print("\n[2] 查看记忆")
    system.show_user_memories(user_id)

    confirm = input("\n清空? (y/n): ")
    if confirm.lower() == 'y':
        system.reset_user_memories(user_id)
        system.show_user_memories(user_id)


def demo_continuous_learning():
    """演示持续学习能力"""
    print("\n" + "=" * 50)
    print("演示5: 持续学习")
    print("=" * 50)

    system = PersonalizedRecommendationSystem(custom_config)
    user_id = "user_learning"

    print("\n[1] 初始推荐")
    system.chat(user_id, "我想学习编程")
    recs1 = system.get_recommendations(user_id, count=3)

    print("\n[2] 记录反馈")
    system.record_rating(user_id, 1, 3, "太简单")
    system.record_rating(user_id, 2, 5, "对AI更感兴趣")

    print("\n[3] 优化推荐")
    recs2 = system.get_recommendations(user_id, count=3)

    profile = system.get_user_profile(user_id)
    print(f"\n画像: {', '.join(profile.get('interests', []))}")


def interactive_demo():
    """交互式演示"""
    print("\n" + "=" * 50)
    print("演示6: 交互式体验")
    print("=" * 50)

    system = PersonalizedRecommendationSystem(custom_config)
    user_id = input("\n用户ID: ").strip() or "user_interactive"

    while True:
        print("\n操作: 1.对话 2.文章列表 3.记录阅读 4.评分 5.推荐 6.画像 7.记忆 8.退出")

        choice = input("选项: ").strip()

        if choice == "1":
            message = input("消息: ")
            response = system.chat(user_id, message)
            print(f"AI: {response}")

        elif choice == "2":
            system.list_all_articles()

        elif choice == "3":
            article_id = int(input("文章ID: "))
            try:
                system.record_article_read(user_id, article_id)
            except ValueError as e:
                print(f"错误: {e}")

        elif choice == "4":
            article_id = int(input("文章ID: "))
            rating = int(input("评分(1-5): "))
            comment = input("评论(可选): ").strip()
            try:
                system.record_rating(user_id, article_id, rating, comment)
            except ValueError as e:
                print(f"错误: {e}")

        elif choice == "5":
            count = int(input("推荐数量(默认3): ") or "3")
            recommendations = system.get_recommendations(user_id, count)

        elif choice == "6":
            profile = system.get_user_profile(user_id)
            print(f"\n画像: {', '.join(profile.get('interests', []))}")

        elif choice == "7":
            system.show_user_memories(user_id)

        elif choice == "8":
            print("\n再见!")
            break

        else:
            print("无效选项")


def main():
    """主函数"""
    print("\n个性化推荐系统 - 基于mem0")
    print("讲24｜记忆系统架构 - 练习题\n")

    while True:
        print("\n" + "=" * 50)
        print("演示: 1.基础 2.配置 3.多用户 4.管理 5.学习 6.交互 0.退出")
        print("=" * 50)

        choice = input("选项: ").strip()

        if choice == "1":
            demo_basic_usage()
        elif choice == "2":
            demo_custom_config()
        elif choice == "3":
            demo_multi_user()
        elif choice == "4":
            demo_memory_management()
        elif choice == "5":
            demo_continuous_learning()
        elif choice == "6":
            interactive_demo()
        elif choice == "0":
            print("\n再见!\n")
            break
        else:
            print("无效选项")

        if choice in ["1", "2", "3", "4", "5"]:
            input("\n[回车继续]")


if __name__ == "__main__":
    print("环境要求: pip install mem0ai openai")
    print("设置Key: export OPENAI_API_KEY='your-key'\n")

    try:
        main()
    except KeyboardInterrupt:
        print("\n程序终止")
    except Exception as e:
        print(f"\n错误: {e}")
