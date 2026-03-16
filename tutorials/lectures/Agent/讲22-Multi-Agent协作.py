"""
讲22｜Multi-Agent协作 - 实战案例：内容创作Multi-Agent系统

本案例实现一个自动生成技术博客的Multi-Agent系统,展示：
1. 顺序协作模式 - Agent按流水线依次工作
2. 循环协作模式 - Writer和Editor多轮优化
3. Agent间通信 - 标准化的消息传递
4. 任务协调 - 整体流程控制

系统包含5个专业Agent:
- Research Agent: 搜集资料
- Outline Agent: 设计大纲
- Writer Agent: 撰写文章
- Editor Agent: 审核修改
- Formatter Agent: 格式化输出

技术栈：
- LLM: DeepSeek-Chat
- 协作模式: 顺序协作 + 循环协作
"""

from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# 加载环境变量
load_dotenv()

# 配置DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = "deepseek-chat"


class Message:
    """标准化的Agent间消息"""
    
    def __init__(self, msg_type, from_agent, to_agent, content, metadata=None):
        self.message_id = f"msg_{datetime.now().timestamp()}"
        self.timestamp = datetime.now().isoformat()
        self.type = msg_type  # task_assignment, result_report, info_request等
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self):
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "type": self.type,
            "from": self.from_agent,
            "to": self.to_agent,
            "content": self.content,
            "metadata": self.metadata
        }


class BaseAgent:
    """Agent基类"""
    
    def __init__(self, agent_id, role, description):
        self.agent_id = agent_id
        self.role = role
        self.description = description
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        self.message_history = []
    
    def process_task(self, task_content, context=None):
        """处理任务 - 子类实现"""
        raise NotImplementedError
    
    def send_message(self, msg_type, to_agent, content, metadata=None):
        """发送消息"""
        message = Message(msg_type, self.agent_id, to_agent, content, metadata)
        self.message_history.append(message)
        return message
    
    def _call_llm(self, system_prompt, user_message, temperature=0.7):
        """调用LLM"""
        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content


class ResearchAgent(BaseAgent):
    """研究员Agent - 搜集资料"""
    
    def __init__(self):
        super().__init__(
            agent_id="research_agent",
            role="研究员",
            description="搜索和整理主题相关资料"
        )
    
    def process_task(self, topic, context=None):
        """搜集主题资料"""
        print(f"\n[{self.role}] 开始搜集资料: {topic}")
        
        system_prompt = f"""你是一个专业的研究员。
你的任务是搜集和整理关于"{topic}"的相关资料。

要求：
1. 列出该主题的核心概念和关键知识点
2. 提供相关的技术要点和最佳实践
3. 整理成结构化的资料包
4. 保持客观和准确

输出格式：
- 核心概念：...
- 关键知识点：...
- 技术要点：...
- 最佳实践：..."""
        
        result = self._call_llm(system_prompt, f"请搜集关于'{topic}'的资料")
        
        print(f"✅ 资料搜集完成!")
        return result


class OutlineAgent(BaseAgent):
    """大纲设计师Agent - 设计文章结构"""
    
    def __init__(self):
        super().__init__(
            agent_id="outline_agent",
            role="大纲设计师",
            description="根据资料设计文章大纲"
        )
    
    def process_task(self, research_materials, context=None):
        """设计文章大纲"""
        print(f"\n[{self.role}] 开始设计大纲...")
        
        system_prompt = """你是一个专业的大纲设计师。
你的任务是根据研究资料设计一篇技术博客的大纲。

要求：
1. 设计清晰的文章结构
2. 每个章节有明确的主题
3. 逻辑连贯,循序渐进
4. 适合技术博客的风格

输出格式：
一、章节1
  1.1 小节
  1.2 小节
二、章节2
  2.1 小节
..."""
        
        result = self._call_llm(
            system_prompt, 
            f"请根据以下资料设计文章大纲:\n\n{research_materials}"
        )
        
        print(f"✅ 大纲设计完成!")
        return result


class WriterAgent(BaseAgent):
    """作家Agent - 撰写文章"""
    
    def __init__(self):
        super().__init__(
            agent_id="writer_agent",
            role="作家",
            description="根据大纲撰写文章内容"
        )
    
    def process_task(self, outline, research_materials, feedback=None):
        """撰写文章"""
        if feedback:
            print(f"\n[{self.role}] 根据反馈修改文章...")
        else:
            print(f"\n[{self.role}] 开始撰写文章...")
        
        system_prompt = """你是一个专业的技术作家。
你的任务是根据大纲和资料撰写技术博客文章。

要求：
1. 内容准确,逻辑清晰
2. 语言通俗易懂
3. 包含具体例子说明概念
4. 保持专业性和可读性
5. 每个章节内容充实"""
        
        user_message = f"""请根据以下内容撰写文章:

大纲:
{outline}

参考资料:
{research_materials}
"""
        
        if feedback:
            user_message += f"\n编辑反馈:\n{feedback}\n\n请根据反馈修改文章。"
        
        result = self._call_llm(system_prompt, user_message, temperature=0.8)
        
        print(f"✅ 文章{'修改' if feedback else '撰写'}完成!")
        return result


class EditorAgent(BaseAgent):
    """编辑Agent - 审核和优化"""
    
    def __init__(self):
        super().__init__(
            agent_id="editor_agent",
            role="编辑",
            description="审核文章质量并提供修改建议"
        )
    
    def process_task(self, article, is_final_review=False):
        """审核文章"""
        print(f"\n[{self.role}] {'最终审核' if is_final_review else '审核初稿'}...")
        
        system_prompt = """你是一个专业的技术编辑。
你的任务是审核技术博客文章的质量。

审核维度：
1. 内容准确性 - 技术概念是否正确
2. 逻辑性 - 结构是否清晰,论述是否连贯
3. 可读性 - 语言是否通俗,是否易于理解
4. 完整性 - 是否涵盖了所有要点
5. 专业性 - 术语使用是否规范

输出格式：
如果需要修改：
- 问题1: ...
- 问题2: ...
- 修改建议: ...

如果通过：
✅ 文章质量良好,通过审核!"""
        
        result = self._call_llm(
            system_prompt,
            f"请审核以下文章:\n\n{article}"
        )
        
        # 判断是否通过
        approved = "通过" in result or "✅" in result
        
        if approved:
            print(f"✅ 审核通过!")
        else:
            print(f"📝 需要修改,已提供反馈")
        
        return {
            "approved": approved,
            "feedback": result
        }


class FormatterAgent(BaseAgent):
    """格式化Agent - 排版美化"""
    
    def __init__(self):
        super().__init__(
            agent_id="formatter_agent",
            role="排版师",
            description="Markdown格式化和美化"
        )
    
    def process_task(self, article, context=None):
        """格式化文章"""
        print(f"\n[{self.role}] 开始格式化...")
        
        system_prompt = """你是一个专业的Markdown排版师。
你的任务是将文章进行格式化和美化。

要求：
1. 使用Markdown格式
2. 合理使用标题层级(#, ##, ###)
3. 重点内容使用加粗
4. 代码概念使用`代码标记`
5. 添加适当的分隔线和列表
6. 保持整洁美观

注意：保持原文内容不变,只优化格式。"""
        
        result = self._call_llm(
            system_prompt,
            f"请格式化以下文章:\n\n{article}"
        )
        
        print(f"✅ 格式化完成!")
        return result


class ContentCreationOrchestrator:
    """内容创作协调器 - 管理整个流程"""
    
    def __init__(self):
        # 初始化所有Agent
        self.research_agent = ResearchAgent()
        self.outline_agent = OutlineAgent()
        self.writer_agent = WriterAgent()
        self.editor_agent = EditorAgent()
        self.formatter_agent = FormatterAgent()
        
        self.workflow_log = []
        self.max_revision_rounds = 2  # 最多修改2轮
    
    def create_article(self, topic):
        """创建文章的完整流程"""
        
        print("="*60)
        print(f"内容创作Multi-Agent系统启动")
        print(f"主题: {topic}")
        print("="*60)
        
        # 步骤1: Research Agent搜集资料
        research_materials = self.research_agent.process_task(topic)
        self._log_step("Research", "资料搜集完成")
        
        # 步骤2: Outline Agent设计大纲
        outline = self.outline_agent.process_task(research_materials)
        self._log_step("Outline", "大纲设计完成")
        
        # 步骤3-5: Writer和Editor循环协作
        article = None
        feedback = None
        
        for round_num in range(1, self.max_revision_rounds + 1):
            print(f"\n--- 第{round_num}轮写作与审核 ---")
            
            # Writer撰写/修改
            article = self.writer_agent.process_task(
                outline, 
                research_materials,
                feedback
            )
            self._log_step(f"Write-Round{round_num}", "文章撰写完成")
            
            # Editor审核
            review_result = self.editor_agent.process_task(
                article,
                is_final_review=(round_num == self.max_revision_rounds)
            )
            
            if review_result["approved"]:
                self._log_step(f"Review-Round{round_num}", "审核通过")
                print(f"\n✅ 文章在第{round_num}轮通过审核!")
                break
            else:
                feedback = review_result["feedback"]
                self._log_step(f"Review-Round{round_num}", "需要修改")
                if round_num < self.max_revision_rounds:
                    print(f"⚠️  需要修改,进入下一轮...")
                else:
                    print(f"⚠️  已达最大修改轮次,使用当前版本")
        
        # 步骤6: Formatter Agent格式化
        final_article = self.formatter_agent.process_task(article)
        self._log_step("Format", "格式化完成")
        
        print("\n" + "="*60)
        print("文章创作完成!")
        print("="*60)
        
        return {
            "topic": topic,
            "research_materials": research_materials,
            "outline": outline,
            "final_article": final_article,
            "workflow_log": self.workflow_log
        }
    
    def _log_step(self, step, status):
        """记录工作流程"""
        self.workflow_log.append({
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    def print_workflow_summary(self):
        """打印工作流程摘要"""
        print("\n" + "="*60)
        print("工作流程摘要")
        print("="*60)
        
        for i, log in enumerate(self.workflow_log, 1):
            print(f"{i}. [{log['step']}] {log['status']}")
        
        print(f"\n总步骤数: {len(self.workflow_log)}")
        print("="*60)


# ==================== 使用示例 ====================

def demo_full_system():
    """演示完整的Multi-Agent系统"""
    
    # 创建协调器
    orchestrator = ContentCreationOrchestrator()
    
    # 创建文章
    topic = "AI Agent的记忆系统设计"
    result = orchestrator.create_article(topic)
    
    # 打印工作流程
    orchestrator.print_workflow_summary()
    
    # 显示最终文章
    print("\n" + "="*60)
    print("最终文章")
    print("="*60)
    print(result["final_article"])
    print("\n" + "="*60)
    
    return result


if __name__ == "__main__":
    # 检查API配置
    if not DEEPSEEK_API_KEY:
        print("❌ 错误: 请在.env文件中配置DEEPSEEK_API_KEY")
        exit(1)
    
    print(f"✅ DeepSeek API配置成功")
    print(f"   模型: {DEEPSEEK_MODEL}\n")
    
    # 运行完整Multi-Agent系统
    print("🚀 启动Multi-Agent内容创作系统...\n")
    print("⚠️  注意: 系统会调用多次LLM API,需要一定时间和token消耗\n")
    
    confirm = input("确认开始创作? (y/n, 默认y): ").strip().lower() or "y"
    
    if confirm == 'y':
        demo_full_system()
    else:
        print("已取消")
    
    print("\n✨ 完成!")
