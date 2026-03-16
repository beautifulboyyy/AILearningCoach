"""
第25讲：对话历史管理与压缩 - 智能客服系统实战

这是一个企业级智能客服系统示例，展示如何使用LangGraph + LangMem实现：
1. 短期记忆（会话内）：使用trim_messages + Checkpointer
2. 长期记忆（跨会话）：使用LangMem自动提取用户画像
3. 多会话隔离：通过thread_id和user_id管理
4. 成本优化：减少80%+ token使用

依赖安装：
pip install langchain-openai langgraph langchain-core langmem psycopg pydantic
"""

import os
from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, RemoveMessage, trim_messages
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langmem import Client as LangMemClient
from langmem.stores.postgres import AsyncPostgresStore


# ============================================================================
# 第一部分：记忆结构定义（Pydantic Schemas）
# ============================================================================

class CustomerProfile(BaseModel):
    """用户画像 - 跨会话的长期记忆"""
    name: Optional[str] = Field(None, description="客户姓名")
    customer_type: Optional[str] = Field(None, description="客户类型：普通/VIP/企业等")
    preferences: list[str] = Field(default_factory=list, description="客户偏好列表")
    contact_history: Optional[str] = Field(None, description="历史联系摘要")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "张三",
                "customer_type": "VIP",
                "preferences": ["快速响应", "电话沟通"],
                "contact_history": "多次咨询退货问题"
            }
        }


class IssueRecord(BaseModel):
    """问题记录 - 记录每次具体问题"""
    issue_type: str = Field(..., description="问题类型：退货/咨询/投诉/售后等")
    order_id: Optional[str] = Field(None, description="关联订单号")
    resolution: Optional[str] = Field(None, description="解决方案")
    status: str = Field(default="进行中", description="状态：进行中/已解决/待跟进")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "issue_type": "退货",
                "order_id": "12345",
                "resolution": "已安排上门取件，3-5天退款",
                "status": "已解决"
            }
        }


# ============================================================================
# 第二部分：状态定义
# ============================================================================

class CustomerServiceState(MessagesState):
    """客服系统状态 - 继承MessagesState获得messages字段"""
    user_id: str  # 用户标识
    session_id: str  # 会话标识
    user_profile_context: Optional[str] = None  # 从LangMem检索的用户画像上下文
    session_context: Optional[str] = None  # 本次会话的临时上下文
    current_issue: Optional[str] = None  # 当前问题描述


# ============================================================================
# 第三部分：智能客服系统主类
# ============================================================================

class IntelligentCustomerService:
    """智能客服系统 - 整合LangGraph + LangMem"""
    
    def __init__(self, use_postgres: bool = False):
        """
        初始化客服系统
        
        Args:
            use_postgres: 是否使用PostgreSQL存储（生产环境推荐）
                         False时使用内存存储（开发/演示用）
        """
        # 1. 初始化LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        # 2. 初始化LangMem（长期记忆）
        self.use_postgres = use_postgres
        if use_postgres:
            # 生产环境：使用PostgreSQL
            postgres_url = os.getenv(
                "POSTGRES_URL",
                "postgresql://postgres:postgres@localhost:5432/langmem_demo"
            )
            store = AsyncPostgresStore(postgres_url)
            self.langmem_client = LangMemClient(
                user_id="customer_service_system",
                store=store
            )
        else:
            # 开发环境：使用内存存储
            self.langmem_client = LangMemClient(
                user_id="customer_service_system"
            )
        
        # 3. 构建LangGraph工作流
        self.graph = self._build_graph()
        
        # 4. 统计信息
        self.stats = {
            "total_turns": 0,
            "total_tokens_with_full_history": 0,
            "total_tokens_actual": 0,
        }
    
    def _build_graph(self) -> StateGraph:
        """构建LangGraph工作流"""
        # 1. 创建状态图
        workflow = StateGraph(CustomerServiceState)
        
        # 2. 添加节点
        workflow.add_node("retrieve_user_profile", self._retrieve_user_profile)
        workflow.add_node("retrieve_session_context", self._retrieve_session_context)
        workflow.add_node("chatbot_respond", self._chatbot_respond)
        workflow.add_node("save_memories", self._save_memories)
        
        # 3. 定义边（工作流程）
        workflow.add_edge(START, "retrieve_user_profile")
        workflow.add_edge("retrieve_user_profile", "retrieve_session_context")
        workflow.add_edge("retrieve_session_context", "chatbot_respond")
        workflow.add_edge("chatbot_respond", "save_memories")
        workflow.add_edge("save_memories", END)
        
        # 4. 编译图（使用MemorySaver作为短期记忆存储）
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)
    
    async def _retrieve_user_profile(self, state: CustomerServiceState) -> dict:
        """节点1: 从LangMem检索用户画像"""
        user_id = state["user_id"]
        
        # 从LangMem检索用户画像（使用namespace隔离）
        namespace = ("customer", user_id, "profile")
        
        try:
            # 搜索该用户的CustomerProfile记忆
            memories = await self.langmem_client.search(
                query=f"用户{user_id}的基本信息和历史",
                namespace=namespace,
                limit=5
            )
            
            if memories:
                # 构建用户画像上下文
                profile_text = "\n".join([
                    f"- {mem.get('content', mem)}" 
                    for mem in memories
                ])
                context = f"用户历史信息:\n{profile_text}"
            else:
                context = None
            
            return {"user_profile_context": context}
        
        except Exception as e:
            print(f"检索用户画像失败: {e}")
            return {"user_profile_context": None}
    
    async def _retrieve_session_context(self, state: CustomerServiceState) -> dict:
        """节点2: 检索本次会话的临时上下文"""
        user_id = state["user_id"]
        session_id = state["session_id"]
        
        # 从LangMem检索本次会话的上下文
        namespace = ("customer", user_id, "session", session_id)
        
        try:
            memories = await self.langmem_client.search(
                query="本次会话的问题和进展",
                namespace=namespace,
                limit=3
            )
            
            if memories:
                session_text = "\n".join([
                    f"- {mem.get('content', mem)}" 
                    for mem in memories
                ])
                context = f"本次会话上下文:\n{session_text}"
            else:
                context = None
            
            return {"session_context": context}
        
        except Exception as e:
            print(f"检索会话上下文失败: {e}")
            return {"session_context": None}
    
    async def _chatbot_respond(self, state: CustomerServiceState) -> dict:
        """节点3: 生成客服回复"""
        messages = state["messages"]
        user_profile_context = state.get("user_profile_context")
        session_context = state.get("session_context")
        
        # 1. 构建系统提示
        system_prompt = self._build_system_prompt(
            user_profile_context,
            session_context
        )
        
        # 2. 使用trim_messages保留最近的对话（控制token使用）
        trimmed_messages = trim_messages(
            messages,
            max_tokens=2000,
            strategy="last",
            token_counter=self.llm,
            include_system=True,
            start_on="human"
        )
        
        # 3. 将系统提示添加到消息列表开头
        final_messages = [SystemMessage(content=system_prompt)] + trimmed_messages
        
        # 4. 调用LLM生成回复
        response = await self.llm.ainvoke(final_messages)
        
        # 5. 更新统计信息（估算）
        self.stats["total_turns"] += 1
        # 完整历史的token数（假设每条消息平均150 tokens）
        self.stats["total_tokens_with_full_history"] += len(messages) * 150
        # 实际使用的token数
        self.stats["total_tokens_actual"] += len(trimmed_messages) * 150
        
        return {"messages": [response]}
    
    def _build_system_prompt(
        self, 
        user_profile_context: Optional[str],
        session_context: Optional[str]
    ) -> str:
        """构建系统提示（包含用户画像和会话上下文）"""
        base_prompt = """你是一个专业的客服AI助手。

请遵循以下原则:
1. 基于客户画像提供个性化服务
2. 结合对话上下文,避免重复询问
3. 专业、友好、高效地解决问题
4. 如果需要更多信息,主动询问
"""
        
        # 添加用户画像
        if user_profile_context:
            base_prompt += f"\n{user_profile_context}\n"
        
        # 添加会话上下文
        if session_context:
            base_prompt += f"\n{session_context}\n"
        
        return base_prompt.strip()
    
    async def _save_memories(self, state: CustomerServiceState) -> dict:
        """节点4: 保存记忆到LangMem"""
        user_id = state["user_id"]
        session_id = state["session_id"]
        messages = state["messages"]
        
        # 获取最近的对话（最后2轮）
        recent_messages = messages[-4:] if len(messages) >= 4 else messages
        conversation_text = "\n".join([
            f"{'用户' if isinstance(msg, HumanMessage) else '客服'}: {msg.content}"
            for msg in recent_messages
        ])
        
        try:
            # 1. 保存用户画像（使用CustomerProfile schema）
            profile_namespace = ("customer", user_id, "profile")
            await self.langmem_client.add(
                memories=[conversation_text],
                namespace=profile_namespace,
                schemas=[CustomerProfile]  # LangMem会自动提取结构化信息
            )
            
            # 2. 保存会话上下文（临时信息）
            session_namespace = ("customer", user_id, "session", session_id)
            await self.langmem_client.add(
                memories=[conversation_text],
                namespace=session_namespace
            )
            
        except Exception as e:
            print(f"保存记忆失败: {e}")
        
        return {}
    
    async def chat(
        self, 
        user_id: str, 
        session_id: str, 
        user_message: str
    ) -> str:
        """
        进行对话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（用于隔离不同会话）
            user_message: 用户消息
            
        Returns:
            客服回复
        """
        # 构建配置（使用thread_id隔离会话）
        config = {
            "configurable": {
                "thread_id": f"{user_id}_{session_id}"
            }
        }
        
        # 构建输入
        input_state = {
            "messages": [HumanMessage(content=user_message)],
            "user_id": user_id,
            "session_id": session_id
        }
        
        # 调用图
        result = await self.graph.ainvoke(input_state, config)
        
        # 返回最后一条AI消息
        last_message = result["messages"][-1]
        return last_message.content
    
    async def record_issue_resolution(
        self,
        user_id: str,
        issue_type: str,
        order_id: Optional[str] = None,
        resolution: Optional[str] = None
    ):
        """
        记录问题解决方案（使用IssueRecord schema）
        
        当客服成功解决问题时调用此方法
        """
        issue_text = f"""
问题类型: {issue_type}
订单号: {order_id or '无'}
解决方案: {resolution or '待定'}
状态: 已解决
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        namespace = ("customer", user_id, "issues")
        
        try:
            await self.langmem_client.add(
                memories=[issue_text],
                namespace=namespace,
                schemas=[IssueRecord]  # 使用IssueRecord结构化提取
            )
            print(f"✓ 已记录问题解决方案: {issue_type}")
        except Exception as e:
            print(f"记录问题失败: {e}")
    
    async def get_user_history(self, user_id: str) -> dict:
        """
        获取用户的完整历史记忆
        
        用于人工客服接入时快速了解用户背景
        """
        all_memories = {}
        
        try:
            # 1. 获取用户画像
            profile_namespace = ("customer", user_id, "profile")
            profile_memories = await self.langmem_client.search(
                query="用户信息",
                namespace=profile_namespace,
                limit=10
            )
            all_memories["profile"] = profile_memories
            
            # 2. 获取问题记录
            issues_namespace = ("customer", user_id, "issues")
            issue_memories = await self.langmem_client.search(
                query="历史问题",
                namespace=issues_namespace,
                limit=20
            )
            all_memories["issues"] = issue_memories
            
            return all_memories
        
        except Exception as e:
            print(f"获取用户历史失败: {e}")
            return {}
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        actual = self.stats["total_tokens_actual"]
        full = self.stats["total_tokens_with_full_history"]
        
        if full > 0:
            saved = full - actual
            saved_percent = (saved / full) * 100
        else:
            saved = 0
            saved_percent = 0
        
        return {
            "total_turns": self.stats["total_turns"],
            "estimated_tokens_full_history": full,
            "actual_tokens_used": actual,
            "tokens_saved": saved,
            "save_percentage": f"{saved_percent:.1f}%"
        }


# ============================================================================
# 第四部分：演示代码
# ============================================================================

async def demo_customer_service():
    """演示智能客服系统"""
    print("=" * 80)
    print("智能客服系统演示 - LangGraph + LangMem")
    print("=" * 80)
    print()
    
    # 创建客服系统（使用内存存储进行演示）
    service = IntelligentCustomerService(use_postgres=False)
    
    # 用户信息
    user_id = "user_001"
    
    # ========================================================================
    # 场景1：第1天，第1次咨询（session_001）
    # ========================================================================
    print("📅 第1天 - 第1次咨询（session_001）")
    print("-" * 80)
    
    session_id = "session_001"
    
    # 第1轮
    print("\n👤 用户: 你好，我想咨询退货问题")
    response = await service.chat(user_id, session_id, "你好，我想咨询退货问题")
    print(f"🤖 客服: {response}")
    
    # 第2轮
    print("\n👤 用户: 我是VIP客户，我叫张三，订单号是12345")
    response = await service.chat(
        user_id, 
        session_id, 
        "我是VIP客户，我叫张三，订单号是12345"
    )
    print(f"🤖 客服: {response}")
    
    # 第3轮
    print("\n👤 用户: 商品有质量问题，我要退货")
    response = await service.chat(
        user_id, 
        session_id, 
        "商品有质量问题，我要退货"
    )
    print(f"🤖 客服: {response}")
    
    # 记录问题解决
    await service.record_issue_resolution(
        user_id=user_id,
        issue_type="退货",
        order_id="12345",
        resolution="已安排上门取件，承诺3-5天退款"
    )
    
    # ========================================================================
    # 场景2：第2天，第2次咨询（session_002）- 新会话
    # ========================================================================
    print("\n" + "=" * 80)
    print("📅 第2天 - 第2次咨询（session_002，新会话）")
    print("-" * 80)
    
    session_id = "session_002"
    
    print("\n👤 用户: 你好，我想查询一下退款进度")
    response = await service.chat(
        user_id, 
        session_id, 
        "你好，我想查询一下退款进度"
    )
    print(f"🤖 客服: {response}")
    print("\n⭐ 关键: 新会话，但通过LangMem记住了VIP客户张三和订单信息")
    
    # ========================================================================
    # 场景3：第5天，第3次咨询（session_003）- 又一个新会话
    # ========================================================================
    print("\n" + "=" * 80)
    print("📅 第5天 - 第3次咨询（session_003，又一个新会话）")
    print("-" * 80)
    
    session_id = "session_003"
    
    print("\n👤 用户: 我想买一个新产品")
    response = await service.chat(
        user_id, 
        session_id, 
        "我想买一个新产品"
    )
    print(f"🤖 客服: {response}")
    print("\n⭐ 关键: 系统仍记得VIP身份，提供个性化服务")
    
    # ========================================================================
    # 统计信息
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 系统统计")
    print("-" * 80)
    
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # ========================================================================
    # 用户历史记录
    # ========================================================================
    print("\n" + "=" * 80)
    print("📝 用户历史记录")
    print("-" * 80)
    
    history = await service.get_user_history(user_id)
    print(f"\n总记录数: {len(history.get('profile', [])) + len(history.get('issues', []))}")
    
    if history.get('profile'):
        print(f"\n用户画像记录: {len(history['profile'])}条")
        for i, mem in enumerate(history['profile'][:3], 1):
            content = mem.get('content', str(mem))
            print(f"  {i}. {content[:100]}...")
    
    if history.get('issues'):
        print(f"\n问题记录: {len(history['issues'])}条")
        for i, mem in enumerate(history['issues'][:3], 1):
            content = mem.get('content', str(mem))
            print(f"  {i}. {content[:100]}...")
    
    print("\n" + "=" * 80)
    print("✅ 演示完成！")
    print("=" * 80)


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数"""
    # 确保设置了OpenAI API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误: 请设置 OPENAI_API_KEY 环境变量")
        print("   export OPENAI_API_KEY='your-api-key'")
        return
    
    # 运行演示
    await demo_customer_service()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
