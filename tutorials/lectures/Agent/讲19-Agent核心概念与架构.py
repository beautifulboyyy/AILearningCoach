"""
讲19｜Agent核心概念与架构 - 实践练习
基于LangChain最新版本实现5个Agent练习

依赖安装:
pip install langchain langchain-openai python-dotenv

配置说明:
在项目根目录创建 .env 文件，内容如下：
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_API_BASE=https://api.deepseek.com

注意：本代码适配 LangChain 1.0+ 版本，使用 create_agent API
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()


# ==================== 工具定义 ====================
@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气信息。
    
    Args:
        city: 城市名称，如"北京"、"上海"、"深圳"
    
    Returns:
        该城市的详细天气信息
    """
    # 模拟天气数据
    weather_data = {
        "北京": {"temperature": 15, "condition": "多云转小雨", "humidity": 65, "precipitation": 70},
        "上海": {"temperature": 20, "condition": "晴", "humidity": 55, "precipitation": 10},
        "深圳": {"temperature": 28, "condition": "阴", "humidity": 75, "precipitation": 30},
        "杭州": {"temperature": 18, "condition": "小雨", "humidity": 80, "precipitation": 85},
    }

    if city in weather_data:
        data = weather_data[city]
        return f"{city}的天气情况：温度{data['temperature']}°C，{data['condition']}，湿度{data['humidity']}%，降水概率{data['precipitation']}%"
    else:
        return f"抱歉，暂无{city}的天气信息"


@tool
def calculator_tool(expression: str) -> str:
    """执行数学计算。
    
    Args:
        expression: 数学表达式，如"2+3*4"、"(100-20)*0.7"
    
    Returns:
        计算结果
    """
    try:
        # 安全的数学表达式计算
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含非法字符"

        result = eval(expression)
        return f"计算结果: {result}"
    except ZeroDivisionError:
        return "错误：除数不能为零"
    except SyntaxError:
        return "错误：表达式语法错误"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def search_tool(query: str) -> str:
    """搜索工具：查找信息和知识。
    
    Args:
        query: 搜索关键词
    
    Returns:
        搜索结果
    """
    # 模拟搜索结果
    search_db = {
        "Python": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。特点：简洁易学、功能强大、应用广泛。",
        "机器学习": "机器学习是人工智能的一个分支，通过算法让计算机从数据中学习规律。主要方法：监督学习、无监督学习、强化学习。",
        "北京": "北京是中国的首都，位于华北平原，面积16410平方公里，人口超过2100万。著名景点：故宫、长城、天安门。",
    }

    for key in search_db:
        if key in query:
            return f"搜索结果：{search_db[key]}"

    return f"未找到关于'{query}'的相关信息"


# ==================== 练习1: 基础Agent实现 ====================


def exercise_1_basic_agent():
    """
    练习1: 实现基础的Agent
    使用LangChain最新版本的create_agent方法
    """
    # 初始化LLM（使用deepseek平台）
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # 定义系统提示词
    system_prompt = """你是一个智能天气助手，可以使用工具来回答用户的天气相关问题。

当用户询问天气信息时：
1. 识别城市名称
2. 使用 get_weather 工具查询天气
3. 基于查询结果给出友好的回答和建议

如果用户的问题涉及多个城市的对比，需要分别查询每个城市的天气。"""

    # 创建 Agent
    tools = [get_weather]
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )

    # 测试问题
    test_questions = [
        "北京今天的天气怎么样？",
        "上海和深圳哪个城市温度更高？",
        "如果明天去杭州旅游，需要带伞吗？"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 60}")
        print(f"测试 {i}: {question}")
        print('=' * 60)

        try:
            # 调用 Agent
            result = agent.invoke({"messages": [{"role": "user", "content": question}]})

            # 获取最终答案
            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                print(f"\n✅ Agent回答: {final_message.content}")

        except Exception as e:
            print(f"\n❌ 执行出错: {str(e)}")

    print("\n" + "=" * 80)
    print("练习1总结:")
    print("- 使用 create_agent() 方法创建Agent")
    print("- Agent会自动调用工具并循环执行直到得到最终答案")
    print("- 系统提示词用于指导Agent的行为")
    print("=" * 80 + "\n")


# ==================== 练习2: 多工具Agent ====================


def exercise_2_multi_tool_agent():
    """
    练习2: 实现多工具Agent
    测试多个工具的协同使用
    """
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    system_prompt = """你是一个智能助手，可以使用多个工具来完成任务：

1. get_weather: 查询城市天气信息
2. calculator_tool: 执行数学计算
3. search_tool: 搜索知识和信息

根据用户的问题：
- 如果需要天气信息，使用 get_weather
- 如果需要计算，使用 calculator_tool
- 如果需要查找信息，使用 search_tool
- 如果需要多个步骤，依次使用相应的工具

最后给出清晰、友好的回答。"""

    # 创建多工具 Agent
    tools = [get_weather, calculator_tool, search_tool]
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )

    # 测试复杂任务
    test_tasks = [
        "Python编程语言是什么时候创建的？",
        "查询上海和深圳的温度，然后计算它们的平均温度",
        "搜索机器学习的定义"
    ]

    for i, task in enumerate(test_tasks, 1):
        print(f"\n{'=' * 60}")
        print(f"任务 {i}: {task}")
        print('=' * 60)

        try:
            result = agent.invoke({"messages": [{"role": "user", "content": task}]})

            # 获取最终答案
            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                print(f"\n✅ Agent回答: {final_message.content}")

        except Exception as e:
            print(f"\n❌ 执行出错: {str(e)}")

    print("\n" + "=" * 80)
    print("练习2总结:")
    print("- 多工具Agent可以根据任务需求选择合适的工具")
    print("- Agent会自动循环执行直到完成任务")
    print("- 工具之间可以协同工作")
    print("=" * 80 + "\n")


# ==================== 练习3: Agent执行循环与调试 ====================


def exercise_3_execution_loop():
    """
    练习3: 观察Agent的执行循环
    包括工具调用、错误处理等
    """
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    system_prompt = """你是一个数学助手，可以使用calculator_tool工具解决数学问题。

工作流程：
1. 理解用户的数学问题
2. 将问题转换为数学表达式
3. 使用calculator_tool计算
4. 解释计算结果

如果遇到错误（如除以0），要向用户说明原因。"""

    tools = [calculator_tool]
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        debug=True  # 开启调试模式
    )

    # 测试案例
    test_cases = [
        ("正常计算", "计算 (123 + 456) * 2 的结果"),
        ("复杂表达式", "如果一件商品原价200元，打7折后再减30元，最后价格是多少？"),
        ("边界情况", "100 除以 0 等于多少？"),
    ]

    for case_name, question in test_cases:
        print(f"\n{'=' * 60}")
        print(f"测试案例: {case_name}")
        print(f"问题: {question}")
        print('=' * 60)

        try:
            result = agent.invoke({"messages": [{"role": "user", "content": question}]})

            # 获取消息历史，观察执行过程
            messages = result.get("messages", [])
            print(f"\n📊 总共执行了 {len(messages)} 步")

            # 显示最终答案
            if messages:
                final_message = messages[-1]
                print(f"✅ 最终答案: {final_message.content}")

        except Exception as e:
            print(f"\n❌ 执行失败: {str(e)}")

    print("\n" + "=" * 80)
    print("练习3总结:")
    print("- Agent会自动管理执行循环")
    print("- 开启debug模式可以观察详细的执行过程")
    print("- 工具错误会被Agent捕获并处理")
    print("=" * 80 + "\n")


# ==================== 练习4: System Prompt优化对比 ====================


def exercise_4_prompt_optimization():
    """
    练习4: 对比不同System Prompt的效果
    """
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # 不同版本的System Prompt
    prompts = {
        "基础版": "你是一个助手，可以使用工具。",

        "详细版": """你是一个专业的天气助手，擅长分析天气信息并提供建议。

当用户询问天气时：
1. 使用get_weather工具获取信息
2. 基于查询结果给出专业建议""",

        "优化版": """你是一个智能天气助手，具备以下能力：
1. 理解用户的天气查询需求
2. 使用get_weather工具获取准确的天气数据
3. 分析天气数据并提供实用建议
4. 用友好、专业的语言回复用户

工作流程：
- 识别用户问题中的城市名称
- 调用get_weather工具
- 基于数据给出建议（如是否需要带伞、穿衣建议等）
- 确保回复清晰、实用"""
    }

    test_question = "北京今天天气怎么样？降水概率高的话需要带伞吗？"
    tools = [get_weather]

    for prompt_name, system_prompt in prompts.items():
        print(f"\n{'=' * 60}")
        print(f"测试 {prompt_name} Prompt")
        print('=' * 60)

        try:
            agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=system_prompt
            )

            result = agent.invoke({"messages": [{"role": "user", "content": test_question}]})

            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                print(f"\n✅ Agent回答: {final_message.content}")

        except Exception as e:
            print(f"\n❌ 执行出错: {str(e)}")

    print("\n" + "=" * 80)
    print("练习4总结:")
    print("- 清晰的角色定义能帮助Agent更好地理解职责")
    print("- 详细的工作流程说明能提升执行准确性")
    print("- 好的Prompt设计是Agent性能的关键因素")
    print("=" * 80 + "\n")


# ==================== 练习5: Agent性能评估 ====================


def exercise_5_evaluation():
    """
    练习5: 评估Agent在不同任务上的表现
    """
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    system_prompt = """你是一个智能助手，可以使用多个工具：
1. get_weather: 查询城市天气
2. calculator_tool: 执行数学计算
3. search_tool: 搜索信息

根据用户问题选择合适的工具完成任务。"""

    tools = [get_weather, calculator_tool, search_tool]
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )

    # 评估测试集
    test_cases = [
        {
            "question": "Python是什么？",
            "type": "单工具-信息查询"
        },
        {
            "question": "计算 123 + 456",
            "type": "单工具-计算"
        },
        {
            "question": "北京今天天气如何？",
            "type": "单工具-天气"
        },
        {
            "question": "搜索机器学习的定义，然后查询深圳天气",
            "type": "多工具协同"
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['type']}")
        print(f"问题: {test_case['question']}")
        print('=' * 60)

        start_time = datetime.now()
        success = False

        try:
            result = agent.invoke({"messages": [{"role": "user", "content": test_case['question']}]})

            execution_time = (datetime.now() - start_time).total_seconds()

            # 获取最终答案
            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                success = True
                print(f"\n✅ 完成")
                print(f"   答案: {final_message.content}...")
                print(f"   耗时: {execution_time:.2f}秒")

            results.append({
                "type": test_case['type'],
                "success": success,
                "execution_time": execution_time
            })

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            results.append({
                "type": test_case['type'],
                "success": False,
                "execution_time": 0
            })

    # 性能统计
    print("\n" + "=" * 60)
    print("📊 性能统计")
    print("=" * 60)

    total = len(results)
    successful = sum(1 for r in results if r['success'])
    avg_time = sum(r['execution_time'] for r in results) / total if total > 0 else 0

    print(f"任务完成率: {successful}/{total} ({successful / total * 100:.1f}%)")
    print(f"平均执行时间: {avg_time:.2f}秒")

    print("\n" + "=" * 80)
    print("练习5总结:")
    print("- 系统化测试可以全面评估Agent性能")
    print("- 完成率和执行时间是关键指标")
    print("- 评估结果可以指导优化方向")
    print("=" * 80 + "\n")


# ==================== 主函数 ====================
def main():
    """
    运行所有练习
    """
    print("\n" + "=" * 80)
    print("讲19｜Agent核心概念与架构 - LangChain最新版实践")
    print("=" * 80)
    print("\n注意：运行前请确保在项目根目录创建.env文件")
    print("内容格式：")
    print("  OPENAI_API_KEY=your_deepseek_api_key")
    print("  OPENAI_API_BASE=https://api.deepseek.com\n")

    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告：未检测到OPENAI_API_KEY环境变量")
        print("   请在项目根目录创建.env文件并设置以下内容：")
        print("   OPENAI_API_KEY=your_deepseek_api_key")
        print("   OPENAI_API_BASE=https://api.deepseek.com\n")
        return

    # 显示当前配置
    api_base = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com")
    print(f"✅ 使用配置:")
    print(f"   API Base: {api_base}")
    print(f"   Model: deepseek-chat")
    print(f"   使用 create_agent API\n")

    try:
        # 练习1: 基础Agent实现
        exercise_1_basic_agent()

        # 练习2: 多工具Agent
        exercise_2_multi_tool_agent()

        # 练习3: Agent执行循环与调试
        exercise_3_execution_loop()

        # 练习4: System Prompt优化对比
        exercise_4_prompt_optimization()

        # 练习5: Agent性能评估
        exercise_5_evaluation()

        print("\n" + "=" * 80)
        print("🎉 所有练习完成！")
        print("=" * 80)
        print("\n关键收获：")
        print("1. 使用 create_agent() 方法创建Agent")
        print("2. Agent会自动管理工具调用循环")
        print("3. System Prompt直接影响Agent表现")
        print("4. 支持多工具协同处理复杂任务")
        print("5. 可以通过debug模式观察执行过程")
        print("\n下一步：学习讲20-实现ReAct Agent 和 讲21-Planning与执行")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")
        print("请检查：")
        print("1. API密钥是否正确设置")
        print("2. 网络连接是否正常")
        print("3. 依赖包是否正确安装：pip install langchain langchain-openai python-dotenv")


if __name__ == "__main__":
    main()
