"""
讲21-Planning与执行 - LangGraph实现
包含5个练习题的完整实现
"""

import json
import operator
from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from datetime import datetime
import random

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()




# ============================================================================
# 状态定义
# ============================================================================

class Step(TypedDict):
    """单个执行步骤"""
    step: int
    description: str
    tool: str
    dependencies: List[int]
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"]
    result: Optional[str]
    error: Optional[str]
    execution_time: Optional[float]
    retry_count: int


class PlanningState(TypedDict):
    """Planning Agent的状态"""
    # 输入
    task: str
    available_tools: List[str]
    
    # Planning相关
    plan: Optional[Dict[str, Any]]
    steps: List[Step]
    
    # Execution相关
    current_step: int
    total_steps: int
    completed_steps: List[int]
    
    # 监控相关
    progress: float
    status: Literal["planning", "executing", "completed", "failed", "replanning"]
    
    # 错误恢复相关
    max_retries: int
    replan_count: int
    max_replan: int
    
    # 消息历史
    messages: Annotated[List, operator.add]
    
    # 最终结果
    final_result: Optional[str]


# ============================================================================
# 模拟工具函数
# ============================================================================

class MockTools:
    """模拟工具集合"""
    
    @staticmethod
    def search(query: str) -> str:
        """搜索工具"""
        results = {
            "生日派对": "找到10个生日派对策划方案",
            "北京天气": "北京今天多云，有30%降雨概率",
            "雨伞品牌": "找到热门雨伞品牌：天堂伞、红叶伞、梅花伞",
            "场地": "找到3个派对场地选项",
            "蛋糕店": "找到5家附近的蛋糕店"
        }
        for key, value in results.items():
            if key in query:
                return value
        return f"搜索'{query}'：未找到相关结果"
    
    @staticmethod
    def send_email(to: str, subject: str, content: str) -> str:
        """发送邮件工具"""
        return f"已发送邮件给 {to}，主题：{subject}"
    
    @staticmethod
    def calculator(expression: str) -> str:
        """计算器工具"""
        try:
            result = eval(expression)
            return f"计算结果：{result}"
        except:
            return "计算错误"
    
    @staticmethod
    def book_venue(venue: str, date: str) -> str:
        """预订场地工具"""
        return f"已预订场地：{venue}，日期：{date}"
    
    @staticmethod
    def weather_check(city: str) -> str:
        """查询天气工具"""
        # 随机返回下雨或晴天
        weather = random.choice(["下雨", "晴天", "多云"])
        return f"{city}的天气：{weather}"
    
    @staticmethod
    def get_data(source: str) -> str:
        """获取数据工具 - 模拟可能失败"""
        # 30%概率失败，用于测试错误恢复
        if random.random() < 0.3:
            raise Exception(f"无法从{source}获取数据：连接超时")
        return f"成功从{source}获取到100条数据"
    
    @staticmethod
    def process_data(data: str) -> str:
        """处理数据工具"""
        return f"数据处理完成：{data}"
    
    @staticmethod
    def create_invitation(event: str, date: str) -> str:
        """创建邀请函工具"""
        return f"已创建邀请函：{event}，日期：{date}"


# ============================================================================
# 工具执行器
# ============================================================================

def execute_tool(tool_name: str, **kwargs) -> str:
    """执行工具并返回结果"""
    tools = MockTools()
    
    tool_map = {
        "search": tools.search,
        "send_email": tools.send_email,
        "calculator": tools.calculator,
        "book_venue": tools.book_venue,
        "weather_check": tools.weather_check,
        "get_data": tools.get_data,
        "process_data": tools.process_data,
        "create_invitation": tools.create_invitation,
    }
    
    if tool_name not in tool_map:
        return f"错误：工具'{tool_name}'不存在"
    
    try:
        result = tool_map[tool_name](**kwargs)
        return result
    except Exception as e:
        raise e


# ============================================================================
# Planning节点
# ============================================================================

def planning_node(state: PlanningState) -> PlanningState:
    """Planning节点：生成任务执行计划"""
    print("\n" + "="*80)
    print("📋 Planning阶段：生成执行计划")
    print("="*80)
    
    llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    
    # 构建Planning Prompt
    planning_prompt = f"""你是一个任务规划专家。请将用户的任务分解为具体的、可执行的子任务。

用户任务：{state['task']}

可用工具：{', '.join(state['available_tools'])}

请按照以下要求分解任务：
1. 子任务应该是具体的、可执行的
2. 明确子任务之间的依赖关系
3. 每个子任务应该有明确的完成标准
4. 合理选择使用的工具

输出格式（JSON）：
{{
  "goal": "任务目标",
  "steps": [
    {{
      "step": 1,
      "description": "子任务描述",
      "tool": "工具名称",
      "dependencies": [],
      "estimated_time": "预估时间"
    }},
    ...
  ]
}}

请只输出JSON，不要包含其他内容。"""
    
    messages = [SystemMessage(content=planning_prompt)]
    response = llm.invoke(messages)
    
    # 解析计划
    try:
        # 提取JSON部分
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        plan = json.loads(content)
        
        # 转换为Step对象
        steps = []
        for s in plan['steps']:
            steps.append(Step(
                step=s['step'],
                description=s['description'],
                tool=s['tool'],
                dependencies=s.get('dependencies', []),
                status="pending",
                result=None,
                error=None,
                execution_time=None,
                retry_count=0
            ))
        
        print(f"\n✅ 计划生成成功！")
        print(f"目标：{plan['goal']}")
        print(f"共{len(steps)}个步骤：")
        for step in steps:
            deps = f"(依赖步骤: {step['dependencies']})" if step['dependencies'] else ""
            print(f"  步骤{step['step']}: {step['description']} {deps}")
        
        return {
            "plan": plan,
            "steps": steps,
            "total_steps": len(steps),
            "current_step": 0,
            "status": "executing",
            "messages": [AIMessage(content=f"计划已生成：{len(steps)}个步骤")]
        }
        
    except Exception as e:
        print(f"❌ 计划解析失败：{e}")
        return {
            "status": "failed",
            "final_result": f"Planning失败：{e}",
            "messages": [AIMessage(content=f"Planning失败：{e}")]
        }


# ============================================================================
# Execution节点
# ============================================================================

def execution_node(state: PlanningState) -> PlanningState:
    """Execution节点：执行当前步骤"""
    current_idx = state['current_step']
    steps = state['steps']
    
    if current_idx >= len(steps):
        # 所有步骤执行完成
        return {
            "status": "completed",
            "progress": 100.0,
            "final_result": "所有步骤执行完成！",
            "messages": [AIMessage(content="✅ 所有步骤执行完成！")]
        }
    
    current_step = steps[current_idx]
    
    print(f"\n{'='*80}")
    print(f"⚙️  执行步骤 {current_step['step']}/{len(steps)}")
    print(f"{'='*80}")
    print(f"描述：{current_step['description']}")
    print(f"工具：{current_step['tool']}")
    print(f"状态：{current_step['status']}")
    
    # 检查依赖
    for dep in current_step['dependencies']:
        dep_step = steps[dep - 1]
        if dep_step['status'] != 'completed':
            print(f"⚠️  依赖步骤{dep}未完成，无法执行")
            return {
                "status": "failed",
                "final_result": f"步骤{current_step['step']}的依赖未满足",
                "messages": [AIMessage(content=f"依赖未满足：步骤{dep}")]
            }
    
    # 更新状态为执行中
    current_step['status'] = 'in_progress'
    
    # 执行工具
    try:
        start_time = datetime.now()
        
        # 根据工具名称执行
        if current_step['tool'] == 'search':
            result = execute_tool('search', query=current_step['description'])
        elif current_step['tool'] == 'weather_check':
            result = execute_tool('weather_check', city='北京')
        elif current_step['tool'] == 'get_data':
            result = execute_tool('get_data', source='database')
        elif current_step['tool'] == 'calculator':
            result = execute_tool('calculator', expression='100*1.2')
        elif current_step['tool'] == 'send_email':
            result = execute_tool('send_email', to='guests@example.com', 
                                subject='邀请函', content='欢迎参加派对')
        elif current_step['tool'] == 'book_venue':
            result = execute_tool('book_venue', venue='派对厅', date='2024-12-25')
        elif current_step['tool'] == 'create_invitation':
            result = execute_tool('create_invitation', event='生日派对', date='2024-12-25')
        else:
            result = f"工具{current_step['tool']}执行成功（模拟）"
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 更新步骤状态
        current_step['status'] = 'completed'
        current_step['result'] = result
        current_step['execution_time'] = execution_time
        
        print(f"✅ 执行成功！")
        print(f"结果：{result}")
        print(f"耗时：{execution_time:.2f}秒")
        
        # 更新整体状态
        completed = [i for i, s in enumerate(steps) if s['status'] == 'completed']
        progress = len(completed) / len(steps) * 100
        
        return {
            "steps": steps,
            "current_step": current_idx + 1,
            "completed_steps": completed,
            "progress": progress,
            "messages": [AIMessage(content=f"步骤{current_step['step']}完成：{result}")]
        }
        
    except Exception as e:
        print(f"❌ 执行失败：{e}")
        current_step['status'] = 'failed'
        current_step['error'] = str(e)
        
        return {
            "steps": steps,
            "status": "error",
            "messages": [AIMessage(content=f"步骤{current_step['step']}失败：{e}")]
        }


# ============================================================================
# 错误恢复节点
# ============================================================================

def error_recovery_node(state: PlanningState) -> PlanningState:
    """错误恢复节点：处理执行失败"""
    print(f"\n{'='*80}")
    print("🔧 错误恢复：尝试恢复失败的步骤")
    print(f"{'='*80}")
    
    current_idx = state['current_step']
    steps = state['steps']
    current_step = steps[current_idx]
    max_retries = state.get('max_retries', 3)
    
    print(f"步骤{current_step['step']}失败：{current_step['error']}")
    print(f"当前重试次数：{current_step['retry_count']}/{max_retries}")
    
    # 策略1: 重试
    if current_step['retry_count'] < max_retries:
        print(f"📝 策略1：重试机制（第{current_step['retry_count'] + 1}次重试）")
        current_step['retry_count'] += 1
        current_step['status'] = 'pending'
        current_step['error'] = None
        
        return {
            "steps": steps,
            "status": "executing",
            "messages": [AIMessage(content=f"重试步骤{current_step['step']}（第{current_step['retry_count']}次）")]
        }
    
    # 策略2: 备选方案（简化版：跳过可选步骤）
    print(f"📝 策略2：检查是否可以跳过")
    # 假设某些步骤是可选的
    optional_keywords = ['可选', '建议', '优化']
    is_optional = any(kw in current_step['description'] for kw in optional_keywords)
    
    if is_optional:
        print(f"✅ 步骤{current_step['step']}是可选的，跳过继续执行")
        current_step['status'] = 'skipped'
        
        return {
            "steps": steps,
            "current_step": current_idx + 1,
            "status": "executing",
            "messages": [AIMessage(content=f"跳过可选步骤{current_step['step']}")]
        }
    
    # 策略3: 触发重规划
    print(f"📝 策略3：触发重规划")
    replan_count = state.get('replan_count', 0)
    max_replan = state.get('max_replan', 2)
    
    if replan_count < max_replan:
        return {
            "status": "replanning",
            "replan_count": replan_count + 1,
            "messages": [AIMessage(content=f"触发重规划（第{replan_count + 1}次）")]
        }
    
    # 所有策略都失败
    print(f"❌ 所有恢复策略都失败，任务终止")
    return {
        "status": "failed",
        "final_result": f"步骤{current_step['step']}失败，无法恢复",
        "messages": [AIMessage(content="所有恢复策略都失败，任务终止")]
    }


# ============================================================================
# 重规划节点
# ============================================================================

def replanning_node(state: PlanningState) -> PlanningState:
    """重规划节点：根据当前状态重新生成计划"""
    print(f"\n{'='*80}")
    print("🔄 重规划：根据当前情况调整计划")
    print(f"{'='*80}")
    
    llm = ChatOpenAI(model="deepseek-chat", temperature=0,base_url="https://api.deepseek.com",api_key="sk-f44d19e89dd5485eb87bf6a9fb187762")
    
    # 收集已完成的步骤信息
    completed_info = []
    for step in state['steps']:
        if step['status'] == 'completed':
            completed_info.append(f"步骤{step['step']}: {step['description']} - 已完成")
        elif step['status'] == 'failed':
            completed_info.append(f"步骤{step['step']}: {step['description']} - 失败({step['error']})")
    
    # 构建重规划Prompt
    replan_prompt = f"""你是一个任务规划专家。原计划执行过程中遇到问题，需要重新规划。

原始任务：{state['task']}

已完成的步骤：
{chr(10).join(completed_info)}

当前状态：步骤{state['current_step'] + 1}失败

请重新规划剩余的任务，要求：
1. 考虑已完成的步骤成果
2. 避免之前失败的方法
3. 找到替代方案
4. 确保任务目标仍能达成

输出格式（JSON）：
{{
  "goal": "调整后的任务目标",
  "steps": [
    {{
      "step": 1,
      "description": "子任务描述",
      "tool": "工具名称",
      "dependencies": []
    }},
    ...
  ],
  "changes": "说明本次调整的主要变化"
}}

请只输出JSON。"""
    
    messages = [SystemMessage(content=replan_prompt)]
    response = llm.invoke(messages)
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        plan = json.loads(content)
        
        # 转换为Step对象
        new_steps = []
        for s in plan['steps']:
            new_steps.append(Step(
                step=s['step'],
                description=s['description'],
                tool=s['tool'],
                dependencies=s.get('dependencies', []),
                status="pending",
                result=None,
                error=None,
                execution_time=None,
                retry_count=0
            ))
        
        print(f"\n✅ 重规划完成！")
        print(f"调整说明：{plan.get('changes', '无')}")
        print(f"新计划共{len(new_steps)}个步骤")
        
        return {
            "plan": plan,
            "steps": new_steps,
            "total_steps": len(new_steps),
            "current_step": 0,
            "status": "executing",
            "messages": [AIMessage(content=f"重规划完成：{plan.get('changes', '')}")]
        }
        
    except Exception as e:
        print(f"❌ 重规划失败：{e}")
        return {
            "status": "failed",
            "final_result": f"重规划失败：{e}",
            "messages": [AIMessage(content=f"重规划失败：{e}")]
        }


# ============================================================================
# 监控节点
# ============================================================================

def monitor_node(state: PlanningState) -> PlanningState:
    """监控节点：显示执行进度"""
    print(f"\n{'='*80}")
    print("📊 执行监控")
    print(f"{'='*80}")
    
    total = state['total_steps']
    current = state['current_step']
    progress = state.get('progress', 0)
    
    # 统计各状态的步骤数
    status_count = {
        'pending': 0,
        'in_progress': 0,
        'completed': 0,
        'failed': 0,
        'skipped': 0
    }
    
    for step in state['steps']:
        status_count[step['status']] += 1
    
    print(f"整体进度：{progress:.1f}% ({current}/{total})")
    print(f"  ✅ 已完成：{status_count['completed']}")
    print(f"  ⚙️  执行中：{status_count['in_progress']}")
    print(f"  ⏳ 待执行：{status_count['pending']}")
    print(f"  ❌ 失败：{status_count['failed']}")
    print(f"  ⏭️  跳过：{status_count['skipped']}")
    
    # 进度条
    bar_length = 50
    filled = int(bar_length * progress / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\n进度条：[{bar}] {progress:.1f}%")
    
    # 详细步骤列表
    print(f"\n步骤详情：")
    for step in state['steps']:
        status_icon = {
            'pending': '⏳',
            'in_progress': '⚙️',
            'completed': '✅',
            'failed': '❌',
            'skipped': '⏭️'
        }[step['status']]
        
        print(f"  {status_icon} 步骤{step['step']}: {step['description']}")
        if step['status'] == 'completed' and step['result']:
            print(f"      结果：{step['result'][:50]}...")
        if step['status'] == 'failed' and step['error']:
            print(f"      错误：{step['error']}")
    
    return {}


# ============================================================================
# 路由函数
# ============================================================================

def should_continue(state: PlanningState) -> str:
    """决定下一步执行什么节点"""
    status = state['status']
    
    if status == 'planning':
        return 'plan'
    elif status == 'executing':
        # 检查是否所有步骤都完成
        if state['current_step'] >= state['total_steps']:
            return 'monitor'
        else:
            return 'execute'
    elif status == 'error':
        return 'recover'
    elif status == 'replanning':
        return 'replan'
    elif status == 'completed':
        return 'end'
    elif status == 'failed':
        return 'end'
    else:
        return 'end'


def after_execution(state: PlanningState) -> str:
    """执行后的路由"""
    current_idx = state['current_step']
    
    # 检查当前步骤是否失败
    if current_idx > 0:
        prev_step = state['steps'][current_idx - 1]
        if prev_step['status'] == 'failed':
            return 'recover'
    
    # 检查是否还有待执行的步骤
    if current_idx >= state['total_steps']:
        return 'monitor'
    else:
        return 'execute'


# ============================================================================
# 构建LangGraph
# ============================================================================

def create_planning_graph():
    """创建Planning + Execution图"""
    
    # 创建图
    workflow = StateGraph(PlanningState)
    
    # 添加节点
    workflow.add_node("plan", planning_node)
    workflow.add_node("execute", execution_node)
    workflow.add_node("recover", error_recovery_node)
    workflow.add_node("replan", replanning_node)
    workflow.add_node("monitor", monitor_node)
    
    # 设置入口点
    workflow.set_entry_point("plan")
    
    # 添加边
    workflow.add_edge("plan", "execute")
    
    # 执行后的条件边
    workflow.add_conditional_edges(
        "execute",
        after_execution,
        {
            "execute": "execute",
            "recover": "recover",
            "monitor": "monitor"
        }
    )
    
    # 恢复后的边
    workflow.add_conditional_edges(
        "recover",
        lambda s: s['status'],
        {
            "executing": "execute",
            "replanning": "replan",
            "failed": "monitor"
        }
    )
    
    # 重规划后的边
    workflow.add_edge("replan", "execute")
    
    # 监控后的边
    workflow.add_conditional_edges(
        "monitor",
        lambda s: "end" if s['status'] in ['completed', 'failed'] else "execute",
        {
            "end": END,
            "execute": "execute"
        }
    )
    
    # 编译图
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


# ============================================================================
# 练习实现
# ============================================================================

def exercise_1():
    """练习1：观察LLM如何分解任务"""
    print("\n" + "🎯" * 40)
    print("练习1：观察LLM如何分解任务 - 准备生日派对")
    print("🎯" * 40)
    
    app = create_planning_graph()
    

    initial_state = {
        "task": "准备一次生日派对",
        "available_tools": ["search", "send_email", "calculator", "book_venue", "create_invitation"],
        "plan": None,
        "steps": [],
        "current_step": 0,
        "total_steps": 0,
        "completed_steps": [],
        "progress": 0.0,
        "status": "planning",
        "max_retries": 3,
        "replan_count": 0,
        "max_replan": 2,
        "messages": [],
        "final_result": None
    }
    
    config = {"configurable": {"thread_id": "exercise_1"}}
    
    # 只执行Planning阶段，不执行
    result = app.invoke(initial_state, config)
    
    print("\n" + "="*80)
    print("💡 练习1总结")
    print("="*80)
    print("思考问题：")
    print("1. 分解的粒度是否合适？")
    print("2. 子任务之间的依赖关系是否清晰？")
    print("3. 是否遗漏了关键步骤？")
    
    return result


def exercise_2_planning():
    """练习2：Planning方式 - 查天气+雨伞"""
    print("\n" + "🎯" * 40)
    print("练习2-A：Planning方式 - 查北京天气，如果下雨就搜索雨伞品牌")
    print("🎯" * 40)
    
    app = create_planning_graph()
    
    initial_state = {
        "task": "查北京天气，如果下雨就搜索雨伞品牌",
        "available_tools": ["weather_check", "search"],
        "plan": None,
        "steps": [],
        "current_step": 0,
        "total_steps": 0,
        "completed_steps": [],
        "progress": 0.0,
        "status": "planning",
        "max_retries": 3,
        "replan_count": 0,
        "max_replan": 2,
        "messages": [],
        "final_result": None
    }
    
    config = {"configurable": {"thread_id": "exercise_2_planning"}}
    result = app.invoke(initial_state, config)
    
    return result


def exercise_2_react():
    """练习2：ReAct方式 - 查天气+雨伞"""
    print("\n" + "🎯" * 40)
    print("练习2-B：ReAct方式 - 边思考边执行")
    print("🎯" * 40)
    
    # ReAct方式：边思考边行动
    print("\n步骤1：思考 - 我需要先查询天气")
    result1 = execute_tool('weather_check', city='北京')
    print(f"行动：查询天气 -> {result1}")
    
    print("\n步骤2：思考 - 根据天气决定下一步")
    if "下雨" in result1:
        print("观察：天气是下雨，需要搜索雨伞")
        print("行动：搜索雨伞品牌")
        result2 = execute_tool('search', query='雨伞品牌')
        print(f"结果：{result2}")
    else:
        print("观察：天气不是下雨，无需搜索雨伞")
    
    print("\n" + "="*80)
    print("💡 练习2总结")
    print("="*80)
    print("对比维度：")
    print("1. Planning方式：先完整规划所有步骤，再依次执行")
    print("   - 优点：全局视野，步骤清晰，可预测")
    print("   - 缺点：可能规划过度，条件分支处理复杂")
    print("2. ReAct方式：边思考边行动，动态决定")
    print("   - 优点：灵活，适合条件任务，调用次数可能更少")
    print("   - 缺点：缺乏全局规划，难以预测")


def exercise_3():
    """练习3：测试错误恢复机制"""
    print("\n" + "🎯" * 40)
    print("练习3：测试错误恢复机制")
    print("🎯" * 40)
    
    # 手动创建一个会失败的计划
    initial_state = {
        "task": "获取数据并处理",
        "available_tools": ["get_data", "process_data"],
        "plan": {
            "goal": "获取并处理数据",
            "steps": [
                {"step": 1, "description": "从数据库获取数据", "tool": "get_data", "dependencies": []},
                {"step": 2, "description": "处理获取的数据", "tool": "process_data", "dependencies": [1]}
            ]
        },
        "steps": [
            Step(
                step=1,
                description="从数据库获取数据",
                tool="get_data",
                dependencies=[],
                status="pending",
                result=None,
                error=None,
                execution_time=None,
                retry_count=0
            ),
            Step(
                step=2,
                description="处理获取的数据",
                tool="process_data",
                dependencies=[1],
                status="pending",
                result=None,
                error=None,
                execution_time=None,
                retry_count=0
            )
        ],
        "current_step": 0,
        "total_steps": 2,
        "completed_steps": [],
        "progress": 0.0,
        "status": "executing",
        "max_retries": 3,
        "replan_count": 0,
        "max_replan": 2,
        "messages": [],
        "final_result": None
    }
    
    app = create_planning_graph()
    config = {"configurable": {"thread_id": "exercise_3"}}
    
    # 执行（get_data有30%概率失败，会触发重试）
    result = app.invoke(initial_state, config)
    
    print("\n" + "="*80)
    print("💡 练习3总结")
    print("="*80)
    print("恢复策略顺序：")
    print("1. 重试机制：自动重试失败的步骤（最多3次）")
    print("2. 备选方案：使用预设的替代工具或方法")
    print("3. 跳过步骤：评估是否可以跳过该步骤继续执行")
    print("观察：系统会依次尝试不同的恢复方法")
    
    return result


def exercise_4():
    """练习4：监控任务执行的实时进度"""
    print("\n" + "🎯" * 40)
    print("练习4：监控任务执行的实时进度")
    print("🎯" * 40)
    
    app = create_planning_graph()
    
    initial_state = {
        "task": "组织一次技术分享会",
        "available_tools": ["search", "book_venue", "send_email", "create_invitation", "calculator"],
        "plan": None,
        "steps": [],
        "current_step": 0,
        "total_steps": 0,
        "completed_steps": [],
        "progress": 0.0,
        "status": "planning",
        "max_retries": 3,
        "replan_count": 0,
        "max_replan": 2,
        "messages": [],
        "final_result": None
    }
    
    config = {"configurable": {"thread_id": "exercise_4"}}
    result = app.invoke(initial_state, config)
    
    print("\n" + "="*80)
    print("💡 练习4总结")
    print("="*80)
    print("监控信息包括：")
    print("- 每个子任务的状态（待执行、执行中、已完成、失败）")
    print("- 整体进度百分比")
    print("- 当前正在执行的任务")
    print("- 详细的步骤执行情况")
    print("\n思考：这种可视化对调试和用户体验有什么帮助？")
    print("- 帮助用户了解任务进展")
    print("- 便于定位问题所在")
    print("- 提供透明的执行过程")
    
    return result


def exercise_5():
    """练习5：体验动态重规划能力"""
    print("\n" + "🎯" * 40)
    print("练习5：体验动态重规划能力")
    print("🎯" * 40)
    
    # 手动创建一个会在步骤3失败的计划
    initial_state = {
        "task": "数据分析任务",
        "available_tools": ["get_data", "process_data", "calculator"],
        "plan": {
            "goal": "完成数据分析",
            "steps": [
                {"step": 1, "description": "获取用户数据", "tool": "get_data", "dependencies": []},
                {"step": 2, "description": "获取订单数据", "tool": "get_data", "dependencies": []},
                {"step": 3, "description": "获取产品数据（必然失败）", "tool": "get_data", "dependencies": []},
                {"step": 4, "description": "分析数据", "tool": "calculator", "dependencies": [1, 2, 3]}
            ]
        },
        "steps": [
            Step(step=1, description="获取用户数据", tool="get_data", dependencies=[], 
                 status="completed", result="成功获取用户数据", error=None, execution_time=0.1, retry_count=0),
            Step(step=2, description="获取订单数据", tool="get_data", dependencies=[], 
                 status="completed", result="成功获取订单数据", error=None, execution_time=0.1, retry_count=0),
            Step(step=3, description="获取产品数据（必然失败）", tool="get_data", dependencies=[], 
                 status="failed", result=None, error="数据源不可用", execution_time=None, retry_count=3),
            Step(step=4, description="分析数据", tool="calculator", dependencies=[1, 2, 3], 
                 status="pending", result=None, error=None, execution_time=None, retry_count=0)
        ],
        "current_step": 2,  # 当前在步骤3（索引2）
        "total_steps": 4,
        "completed_steps": [0, 1],
        "progress": 50.0,
        "status": "error",
        "max_retries": 3,
        "replan_count": 0,
        "max_replan": 2,
        "messages": [],
        "final_result": None
    }
    
    app = create_planning_graph()
    config = {"configurable": {"thread_id": "exercise_5"}}
    
    # 执行（会触发重规划）
    result = app.invoke(initial_state, config)
    
    print("\n" + "="*80)
    print("💡 练习5总结")
    print("="*80)
    print("重规划流程：")
    print("1. 检测到某个步骤执行失败")
    print("2. 分析失败的根本原因")
    print("3. 评估对后续步骤的影响")
    print("4. 调整或重新生成剩余的执行计划")
    print("5. 继续执行新计划")
    print("\n观察重点：")
    print("- 系统如何识别失败的原因")
    print("- 新计划与原计划的差异")
    print("- 重规划是否解决了问题")
    print("- 在什么情况下应该停止重规划")
    
    return result


# ============================================================================
# 主函数
# ============================================================================

def main():
    """运行所有练习"""
    print("\n" + "🎓" * 40)
    print("讲21-Planning与执行 - 五个练习题实现")
    print("🎓" * 40)
    
    # 练习1
    print("\n按Enter键开始练习1...")
    input()
    exercise_1()
    
    # 练习2
    print("\n按Enter键开始练习2...")
    input()
    exercise_2_planning()
    exercise_2_react()
    
    # 练习3
    print("\n按Enter键开始练习3...")
    input()
    exercise_3()
    
    # 练习4
    print("\n按Enter键开始练习4...")
    input()
    exercise_4()
    
    # 练习5
    print("\n按Enter键开始练习5...")
    input()
    exercise_5()
    
    print("\n" + "🎉" * 40)
    print("所有练习完成！")
    print("🎉" * 40)


if __name__ == "__main__":
    main()
