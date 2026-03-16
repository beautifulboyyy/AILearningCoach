"""
讲20｜基于LangGraph实现ReAct Agent

本示例展示如何使用LangGraph框架构建一个入门级的ReAct Agent
包含完整的Thought-Action-Observation循环

安装依赖:
pip install langgraph langchain-openai langchain-core python-dotenv
"""

import os
from typing import TypedDict, Annotated, Sequence
from operator import add
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# 加载环境变量
load_dotenv()


# ============================================================================
# 第一步: 定义工具 (Tools)
# ============================================================================

@tool
def search(query: str) -> str:
    """
    在互联网上搜索信息。
    当需要查找实时信息、新闻、资料时使用此工具。
    
    Args:
        query: 搜索查询关键词
        
    Returns:
        搜索结果摘要
    """
    # 这里是模拟实现,实际应该调用真实的搜索API
    mock_results = {
        "埃菲尔铁塔": "埃菲尔铁塔位于法国巴黎战神广场,高324米,是巴黎的标志性建筑。",
        "巴黎人口": "巴黎市区人口约220万(2024年数据),大巴黎地区人口约1200万。",
        "Python语言": "Python是一种高级编程语言,由Guido van Rossum于1991年创建,广泛用于数据科学和AI开发。",
        "北京天气": "北京今天晴转多云,温度10-18℃,空气质量良好。"
    }
    
    # 简单的关键词匹配
    for key, value in mock_results.items():
        if key in query:
            return value
    
    return f"关于'{query}'的搜索结果: 这是一个模拟搜索结果。实际应用中应该调用真实的搜索API。"


@tool
def calculator(expression: str) -> str:
    """
    执行数学计算。
    当需要进行算术运算、数学计算时使用此工具。
    
    Args:
        expression: 数学表达式,如 "2+3*4" 或 "sqrt(16)"
        
    Returns:
        计算结果
    """
    try:
        # 注意: eval在生产环境中有安全风险,这里仅作演示
        # 实际应该使用更安全的表达式解析器
        result = eval(expression, {"__builtins__": {}}, {
            "sqrt": lambda x: x ** 0.5,
            "pow": pow,
            "abs": abs,
        })
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}。请检查表达式格式。"


@tool
def weather_api(city: str, date: str = "今天") -> str:
    """
    查询指定城市的天气信息。
    当用户询问天气情况时使用此工具。
    
    Args:
        city: 城市名称,如 "北京"、"上海"
        date: 日期,如 "今天"、"明天"
        
    Returns:
        天气信息
    """
    # 模拟天气数据
    mock_weather = {
        "北京": {"今天": "晴,温度10-18℃", "明天": "小雨,温度8-15℃"},
        "上海": {"今天": "多云,温度15-22℃", "明天": "晴,温度16-23℃"},
        "深圳": {"今天": "晴,温度20-28℃", "明天": "晴,温度21-29℃"},
    }
    
    if city in mock_weather and date in mock_weather[city]:
        return f"{city}{date}天气: {mock_weather[city][date]}"
    else:
        return f"抱歉,暂无{city}的天气数据。"


# 工具列表
tools = [search, calculator, weather_api]


# ============================================================================
# 第二步: 定义Agent状态 (State)
# ============================================================================

class AgentState(TypedDict):
    """
    Agent的状态定义
    
    在LangGraph中,状态会在图的节点之间传递和更新
    """
    # 消息历史 (使用add操作符来追加消息)
    messages: Annotated[Sequence[BaseMessage], add]
    # 当前步骤数
    step_count: int


# ============================================================================
# 第三步: 定义节点函数 (Node Functions)
# ============================================================================

def call_model(state: AgentState):
    """
    调用LLM模型进行推理
    
    这个节点会:
    1. 接收当前状态
    2. 调用LLM思考下一步行动
    3. 返回LLM的响应(可能包含工具调用)
    """
    messages = state["messages"]
    
    # 创建LLM实例 (绑定工具)
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(tools)
    
    # 调用LLM
    response = llm_with_tools.invoke(messages)
    
    # 更新步骤计数
    step_count = state.get("step_count", 0) + 1
    
    return {
        "messages": [response],
        "step_count": step_count
    }


def should_continue(state: AgentState):
    """
    决定是否继续执行
    
    这个函数检查:
    1. 最后一条消息是否包含工具调用
    2. 是否超过最大步骤数
    
    Returns:
        "continue": 继续执行工具
        "end": 结束流程
    """
    messages = state["messages"]
    last_message = messages[-1]
    step_count = state.get("step_count", 0)
    
    # 最大步骤限制
    MAX_STEPS = 10
    
    if step_count >= MAX_STEPS:
        print(f"\n⚠️ 已达到最大步骤数 {MAX_STEPS}, 停止执行")
        return "end"
    
    # 检查是否有工具调用
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "continue"
    else:
        return "end"


# ============================================================================
# 第四步: 构建Agent图 (Build Graph)
# ============================================================================

def create_react_agent():
    """
    创建ReAct Agent的图结构
    
    图的结构:
    START -> call_model -> should_continue -> [tools | END]
                ↑                                |
                └────────────────────────────────┘
    """
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("agent", call_model)  # Agent思考节点
    workflow.add_node("tools", ToolNode(tools))  # 工具执行节点
    
    # 设置入口点
    workflow.set_entry_point("agent")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "agent",  # 从agent节点出发
        should_continue,  # 使用should_continue函数判断
        {
            "continue": "tools",  # 如果需要继续,去执行工具
            "end": END  # 如果完成,结束
        }
    )
    
    # 添加普通边: 工具执行完后回到agent
    workflow.add_edge("tools", "agent")
    
    # 编译图
    app = workflow.compile()
    
    return app


# ============================================================================
# 第五步: 运行Agent
# ============================================================================

def run_agent(query: str, verbose: bool = True):
    """
    运行ReAct Agent
    
    Args:
        query: 用户查询
        verbose: 是否打印详细过程
    """
    print("=" * 80)
    print("🤖 LangGraph ReAct Agent 演示")
    print("=" * 80)
    print(f"\n📝 用户问题: {query}\n")
    print("-" * 80)
    
    # 创建Agent
    app = create_react_agent()
    
    # 初始化状态
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "step_count": 0
    }
    
    # 执行Agent
    final_state = None
    for step, state in enumerate(app.stream(initial_state), 1):
        if verbose:
            print(f"\n📍 步骤 {step}:")
            
            # 打印当前节点
            node_name = list(state.keys())[0]
            print(f"   当前节点: {node_name}")
            
            # 打印消息
            if "messages" in state[node_name]:
                for msg in state[node_name]["messages"]:
                    if isinstance(msg, AIMessage):
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            print(f"\n   🤔 Agent思考: 需要调用工具")
                            for tool_call in msg.tool_calls:
                                print(f"      工具: {tool_call['name']}")
                                print(f"      参数: {tool_call['args']}")
                        else:
                            print(f"\n   💬 Agent回答: {msg.content}")
                    elif isinstance(msg, ToolMessage):
                        print(f"\n   🔧 工具结果: {msg.content}")
            
            print("-" * 80)
        
        final_state = state
    
    # 获取最终答案
    if final_state:
        last_node = list(final_state.keys())[0]
        messages = final_state[last_node]["messages"]
        final_message = messages[-1]
        
        if isinstance(final_message, AIMessage):
            print("\n" + "=" * 80)
            print("✅ 最终答案:")
            print("=" * 80)
            print(final_message.content)
            print("=" * 80)
        
        # 打印统计信息
        total_steps = final_state[last_node].get("step_count", 0)
        print(f"\n📊 统计: 共执行 {total_steps} 个步骤")


# ============================================================================
# 示例运行
# ============================================================================

if __name__ == "__main__":
    # 示例1: 简单的信息查询
    print("\n" + "🔹" * 40)
    print("示例1: 信息查询")
    print("🔹" * 40)
    run_agent("埃菲尔铁塔在哪个城市?那个城市的人口是多少?")
    
    print("\n\n" + "🔹" * 40)
    print("示例2: 数学计算")
    print("🔹" * 40)
    run_agent("计算一下 (25 + 15) * 3 - 20 等于多少?")
    
    print("\n\n" + "🔹" * 40)
    print("示例3: 天气查询")
    print("🔹" * 40)
    run_agent("北京明天的天气怎么样?适合户外活动吗?")
    
    print("\n\n" + "🔹" * 40)
    print("示例4: 多工具协作")
    print("🔹" * 40)
    run_agent("搜索一下Python语言的信息,然后计算一下2024年距离1991年多少年了")


# ============================================================================
# 关键知识点总结
# ============================================================================

"""
🎯 LangGraph ReAct Agent 核心概念:

1. **工具定义 (Tools)**
   - 使用 @tool 装饰器定义工具
   - 清晰的文档字符串(LLM据此选择工具)
   - 类型标注的参数

2. **状态管理 (State)**
   - TypedDict 定义状态结构
   - messages: 消息历史
   - Annotated[Sequence, add]: 追加式更新

3. **图结构 (Graph)**
   - 节点 (Node): 执行具体操作
     * agent节点: 调用LLM思考
     * tools节点: 执行工具
   - 边 (Edge): 连接节点
     * 普通边: 固定流转
     * 条件边: 根据状态决定流转

4. **执行流程**
   START -> agent -> 判断 -> [tools -> agent] 或 END
   
5. **与传统ReAct的对比**
   传统: 手动管理循环、解析输出
   LangGraph: 
     - 自动管理状态流转
     - 内置工具调用机制
     - 图结构清晰易扩展

6. **优势**
   - 声明式定义流程
   - 自动处理工具调用
   - 可视化图结构
   - 易于调试和监控
   - 支持复杂的控制流

7. **适用场景**
   ✅ 需要多步推理的任务
   ✅ 工具调用频繁的场景
   ✅ 需要复杂控制流的Agent
   ✅ 团队协作开发(图结构清晰)

下一步学习:
- LangGraph的高级功能(子图、并行执行)
- 持久化状态和检查点
- 人机交互节点(Human-in-the-loop)
- 多Agent协作
"""
