"""
讲08 | Function Calling原理与Schema - 执行演示
展示5个练习的完整执行过程
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

_ = load_dotenv()
client = OpenAI()
DEFAULT_MODEL = "deepseek-chat"


def call_deepseek(messages: List[Dict[str, str]], functions: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """调用DeepSeek API"""
    try:
        kwargs = {"model": DEFAULT_MODEL, "messages": messages, "temperature": 0}
        if functions:
            kwargs["tools"] = [{"type": "function", "function": func} for func in functions]

        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        result = {"content": message.content, "role": "assistant"}
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_call = message.tool_calls[0]
            result["function_call"] = {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }
            result["tool_call_id"] = tool_call.id
        return result
    except Exception as e:
        return {"content": f"错误: {str(e)}", "role": "assistant"}


# ============================================================================
# 练习1: 计算器函数
# ============================================================================

CALCULATOR_FUNCTION = {
    "name": "calculator",
    "description": "执行基础数学运算（加减乘除）",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
            "num1": {"type": "number"},
            "num2": {"type": "number"}
        },
        "required": ["operation", "num1", "num2"]
    }
}


def calculator(operation: str, num1: float, num2: float) -> Dict[str, Any]:
    """执行计算"""
    ops = {
        "add": (num1 + num2, "加法"),
        "subtract": (num1 - num2, "减法"),
        "multiply": (num1 * num2, "乘法"),
        "divide": (num1 / num2 if num2 != 0 else None, "除法")
    }

    if operation not in ops or (operation == "divide" and num2 == 0):
        return {"success": False, "error": "除数不能为0" if num2 == 0 else "不支持的运算"}

    result, op_text = ops[operation]
    return {"success": True, "operation": op_text, "num1": num1, "num2": num2, "result": result}


print("=" * 80)
print("练习1: 计算器函数")
print("=" * 80)

test_cases_1 = [
    "计算15加28等于多少？",
    "144除以12等于几？",
    "10除以0会怎样？"
]

for i, query in enumerate(test_cases_1, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")

    messages = [{"role": "user", "content": query}]
    response = call_deepseek(messages, functions=[CALCULATOR_FUNCTION])

    if "function_call" in response:
        func_call = response["function_call"]
        print(f"\n模型决策: 调用函数")
        print(f"  函数名: {func_call['name']}")
        args = json.loads(func_call['arguments'])
        print(f"  参数: {json.dumps(args, ensure_ascii=False)}")

        result = calculator(**args)
        print(f"  执行结果: {json.dumps(result, ensure_ascii=False)}")

        messages.append({
            "role": "assistant", "content": None,
            "tool_calls": [{
                "id": response.get("tool_call_id", "call_1"),
                "type": "function",
                "function": {"name": func_call["name"], "arguments": func_call["arguments"]}
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": response.get("tool_call_id", "call_1"),
            "content": json.dumps(result, ensure_ascii=False)
        })

        final = call_deepseek(messages)
        print(f"\n最终回复: {final['content']}")
    else:
        print(f"\n模型决策: 直接回复")
        print(f"  {response['content']}")

# ============================================================================
# 练习2: 图书搜索函数
# ============================================================================

BOOKS_DATABASE = [
    {"id": 1, "title": "Python编程从入门到实践", "author": "Eric Matthes", "category": "编程", "available": True},
    {"id": 2, "title": "深度学习", "author": "Ian Goodfellow", "category": "人工智能", "available": True},
    {"id": 3, "title": "机器学习实战", "author": "Peter Harrington", "category": "人工智能", "available": False},
    {"id": 4, "title": "算法导论", "author": "Thomas Cormen", "category": "算法", "available": True},
]

SEARCH_BOOKS_FUNCTION = {
    "name": "search_books",
    "description": "在图书管理系统中搜索图书",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "书名关键词"},
            "author": {"type": "string", "description": "作者姓名"},
            "category": {"type": "string", "enum": ["编程", "人工智能", "算法"]},
            "available_only": {"type": "boolean", "description": "仅显示可借阅的图书"}
        }
    }
}


def search_books(title=None, author=None, category=None, available_only=False, limit=10):
    """搜索图书"""
    results = BOOKS_DATABASE.copy()
    if title:
        results = [b for b in results if title.lower() in b["title"].lower()]
    if author:
        results = [b for b in results if author.lower() in b["author"].lower()]
    if category:
        results = [b for b in results if b["category"] == category]
    if available_only:
        results = [b for b in results if b["available"]]
    return {"success": True, "count": len(results[:limit]), "books": results[:limit]}


print("\n\n" + "=" * 80)
print("练习2: 图书搜索函数")
print("=" * 80)

test_cases_2 = [
    "帮我找一下关于Python的书",
    "有没有Ian Goodfellow写的书？",
    "查询人工智能类别的图书"
]

for i, query in enumerate(test_cases_2, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")

    messages = [{"role": "user", "content": query}]
    response = call_deepseek(messages, functions=[SEARCH_BOOKS_FUNCTION])

    if "function_call" in response:
        func_call = response["function_call"]
        print(f"\n模型决策: 调用函数")
        print(f"  函数名: {func_call['name']}")
        args = json.loads(func_call['arguments'])
        print(f"  参数: {json.dumps(args, ensure_ascii=False)}")

        result = search_books(**args)
        print(f"  找到图书: {result['count']}本")

        messages.append({
            "role": "assistant", "content": None,
            "tool_calls": [{
                "id": response.get("tool_call_id", "call_1"),
                "type": "function",
                "function": {"name": func_call["name"], "arguments": func_call["arguments"]}
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": response.get("tool_call_id", "call_1"),
            "content": json.dumps(result, ensure_ascii=False)
        })

        final = call_deepseek(messages)
        print(f"\n最终回复: {final['content']}")

# ============================================================================
# 练习3: 任务管理函数
# ============================================================================

TASKS_DATABASE = []
TASK_ID_COUNTER = 1

CREATE_TASK_FUNCTION = {
    "name": "create_task",
    "description": "创建新任务",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "任务标题"},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            "due_date": {"type": "string", "description": "截止日期 YYYY-MM-DD"}
        },
        "required": ["title"]
    }
}

UPDATE_TASK_FUNCTION = {
    "name": "update_task",
    "description": "更新已存在的任务",
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"},
            "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
        },
        "required": ["task_id"]
    }
}


def create_task(title: str, priority: str = "medium", due_date=None, **kwargs):
    """创建任务"""
    global TASK_ID_COUNTER
    task = {
        "id": TASK_ID_COUNTER,
        "title": title,
        "priority": priority,
        "status": "pending",
        "due_date": due_date,
        "created_at": datetime.now().isoformat()
    }
    TASKS_DATABASE.append(task)
    TASK_ID_COUNTER += 1
    return {"success": True, "message": "任务创建成功", "task": task}


def update_task(task_id: int, status=None, priority=None, **kwargs):
    """更新任务"""
    for task in TASKS_DATABASE:
        if task["id"] == task_id:
            updated = []
            if status:
                task["status"] = status
                updated.append("状态")
            if priority:
                task["priority"] = priority
                updated.append("优先级")
            return {"success": True, "message": f"更新了: {', '.join(updated)}", "task": task}
    return {"success": False, "error": f"任务ID {task_id} 不存在"}


print("\n\n" + "=" * 80)
print("练习3: 任务管理函数")
print("=" * 80)

test_cases_3 = [
    "帮我创建一个任务：完成项目报告，优先级高",
    "新建一个任务：给妈妈打电话",
    "把任务1标记为已完成"
]

functions_3 = [CREATE_TASK_FUNCTION, UPDATE_TASK_FUNCTION]

for i, query in enumerate(test_cases_3, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")

    messages = [{"role": "user", "content": query}]
    response = call_deepseek(messages, functions=functions_3)

    if "function_call" in response:
        func_call = response["function_call"]
        print(f"\n模型决策: 调用函数")
        print(f"  函数名: {func_call['name']}")
        args = json.loads(func_call['arguments'])
        print(f"  参数: {json.dumps(args, ensure_ascii=False)}")

        if func_call['name'] == 'create_task':
            result = create_task(**args)
        else:
            result = update_task(**args)

        print(f"  执行结果: {result.get('message', result.get('error'))}")

        messages.append({
            "role": "assistant", "content": None,
            "tool_calls": [{
                "id": response.get("tool_call_id", "call_1"),
                "type": "function",
                "function": {"name": func_call["name"], "arguments": func_call["arguments"]}
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": response.get("tool_call_id", "call_1"),
            "content": json.dumps(result, ensure_ascii=False)
        })

        final = call_deepseek(messages)
        print(f"\n最终回复: {final['content']}")

print(f"\n当前任务列表: {len(TASKS_DATABASE)}个任务")
for task in TASKS_DATABASE:
    print(f"  #{task['id']} [{task['status']}] {task['title']} (优先级: {task['priority']})")

# ============================================================================
# 练习4: 多函数智能助手
# ============================================================================

WEATHER_FUNCTION = {
    "name": "get_weather",
    "description": "获取城市天气信息",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "date": {"type": "string", "enum": ["today", "tomorrow"]}
        },
        "required": ["city"]
    }
}

NEWS_FUNCTION = {
    "name": "search_news",
    "description": "搜索新闻资讯",
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {"type": "string"},
            "category": {"type": "string", "enum": ["technology", "business", "sports"]}
        }
    }
}

REMINDER_FUNCTION = {
    "name": "set_reminder",
    "description": "设置提醒事项",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "time": {"type": "string"}
        },
        "required": ["content", "time"]
    }
}


def get_weather(city: str, date: str = "today"):
    """获取天气"""
    return {"success": True, "city": city, "date": date,
            "weather": {"temperature": 15, "condition": "晴"}}


def search_news(keyword=None, category=None, limit=3):
    """搜索新闻"""
    return {"success": True, "count": 2,
            "news": [{"title": "AI技术突破", "category": "technology"}]}


def set_reminder(content: str, time: str, repeat: str = "once"):
    """设置提醒"""
    return {"success": True, "message": "提醒已设置",
            "reminder": {"content": content, "time": time}}


print("\n\n" + "=" * 80)
print("练习4: 多函数智能助手")
print("=" * 80)

functions_4 = [WEATHER_FUNCTION, NEWS_FUNCTION, REMINDER_FUNCTION]

test_cases_4 = [
    "北京今天天气怎么样？",
    "帮我查一下最新的科技新闻",
    "提醒我明天下午3点开会"
]

for i, query in enumerate(test_cases_4, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")

    messages = [{"role": "user", "content": query}]
    response = call_deepseek(messages, functions=functions_4)

    if "function_call" in response:
        func_call = response["function_call"]
        print(f"\n模型决策: 调用函数")
        print(f"  选择函数: {func_call['name']}")
        args = json.loads(func_call['arguments'])
        print(f"  参数: {json.dumps(args, ensure_ascii=False)}")

        function_map = {
            "get_weather": get_weather,
            "search_news": search_news,
            "set_reminder": set_reminder
        }

        result = function_map[func_call['name']](**args)
        print(f"  执行结果: {result.get('message', '成功')}")

        messages.append({
            "role": "assistant", "content": None,
            "tool_calls": [{
                "id": response.get("tool_call_id", "call_1"),
                "type": "function",
                "function": {"name": func_call["name"], "arguments": func_call["arguments"]}
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": response.get("tool_call_id", "call_1"),
            "content": json.dumps(result, ensure_ascii=False)
        })

        final = call_deepseek(messages)
        print(f"\n最终回复: {final['content']}")

# ============================================================================
# 练习5: 错误处理与参数验证
# ============================================================================

TRANSFER_MONEY_FUNCTION = {
    "name": "transfer_money",
    "description": "转账功能（敏感操作）",
    "parameters": {
        "type": "object",
        "properties": {
            "from_account": {"type": "string", "pattern": "^[0-9]{10,20}$"},
            "to_account": {"type": "string", "pattern": "^[0-9]{10,20}$"},
            "amount": {"type": "number", "minimum": 0.01, "maximum": 1000000},
            "currency": {"type": "string", "enum": ["CNY", "USD", "EUR"]}
        },
        "required": ["from_account", "to_account", "amount", "currency"]
    }
}


def transfer_money(from_account: str, to_account: str, amount: float, currency: str, note: str = ""):
    """转账功能 - 完整参数验证"""

    # 验证账户号码格式
    if not re.match(r'^[0-9]{10,20}$', from_account):
        return {"success": False, "error": "转出账户格式错误", "error_code": "INVALID_FROM_ACCOUNT"}

    if not re.match(r'^[0-9]{10,20}$', to_account):
        return {"success": False, "error": "转入账户格式错误", "error_code": "INVALID_TO_ACCOUNT"}

    # 验证业务逻辑
    if from_account == to_account:
        return {"success": False, "error": "不能转给自己", "error_code": "SAME_ACCOUNT"}

    # 验证金额
    if amount <= 0:
        return {"success": False, "error": "金额必须大于0", "error_code": "INVALID_AMOUNT"}

    if amount > 1000000:
        return {"success": False, "error": "超过单笔限额", "error_code": "AMOUNT_EXCEEDED"}

    # 检查余额（模拟）
    mock_balances = {"1234567890": 10000, "1111111111": 100}
    balance = mock_balances.get(from_account, 0)

    if balance < amount:
        return {"success": False, "error": f"余额不足（当前: {balance}）", "error_code": "INSUFFICIENT_BALANCE"}

    # 验证通过
    transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {
        "success": True,
        "message": "转账成功",
        "transaction": {
            "transaction_id": transaction_id,
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "currency": currency
        }
    }


print("\n\n" + "=" * 80)
print("练习5: 错误处理与参数验证")
print("=" * 80)

test_cases_5 = [
    {"from_account": "1234567890", "to_account": "9876543210", "amount": 100, "currency": "CNY"},
    {"from_account": "123", "to_account": "9876543210", "amount": 100, "currency": "CNY"},  # 格式错误
    {"from_account": "1234567890", "to_account": "1234567890", "amount": 100, "currency": "CNY"},  # 相同账户
    {"from_account": "1234567890", "to_account": "9876543210", "amount": -50, "currency": "CNY"},  # 负数
    {"from_account": "1111111111", "to_account": "9876543210", "amount": 500, "currency": "CNY"},  # 余额不足
    {"from_account": "1234567890", "to_account": "9876543210", "amount": 2000000, "currency": "CNY"}  # 超限
]

for i, args in enumerate(test_cases_5, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"参数: {json.dumps(args, ensure_ascii=False)}")

    result = transfer_money(**args)

    if result["success"]:
        print(f"✓ 成功: {result['message']}")
        print(f"  交易ID: {result['transaction']['transaction_id']}")
    else:
        print(f"✗ 失败: {result['error']}")
        print(f"  错误代码: {result.get('error_code')}")

print("\n\n" + "=" * 80)
print("所有练习执行完成")
print("=" * 80)
