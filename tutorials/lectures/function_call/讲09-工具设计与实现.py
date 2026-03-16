"""
讲09 | 工具设计与实现 - 执行演示
参考讲08的实现方式，展示5个练习的执行过程
"""

import json
import csv
import re
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

_ = load_dotenv()
client = OpenAI()


# ============================================================================
# 练习1: 图书查询工具
# ============================================================================

print("=" * 80)
print("练习1: 设计查询工具 - 图书查询（书名、作者、ISBN）")
print("=" * 80)

# 模拟图书数据库
BOOKS_DB = [
    {"id": 1, "title": "Python编程", "author": "Eric Matthes", "isbn": "9787115428028", "stock": 15},
    {"id": 2, "title": "深度学习", "author": "Ian Goodfellow", "isbn": "9787115461476", "stock": 8},
    {"id": 3, "title": "算法导论", "author": "Thomas Cormen", "isbn": "9787111407010", "stock": 5},
]


def search_books(title=None, author=None, isbn=None):
    """查询图书"""
    results = []
    for book in BOOKS_DB:
        if isbn and book["isbn"] == isbn:
            results.append(book)
        elif title and title.lower() in book["title"].lower():
            results.append(book)
        elif author and author.lower() in book["author"].lower():
            results.append(book)
    return {"success": True, "books": results}


tools_1 = [
    {"type": "function", "function": {
        "name": "search_books",
        "description": "在图书库中查询图书，支持按书名、作者、ISBN查询",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "书名关键词"},
                "author": {"type": "string", "description": "作者姓名"},
                "isbn": {"type": "string", "description": "ISBN号码"}
            }
        }
    }}
]

tools_map_1 = {"search_books": search_books}

queries_1 = [
    "找一本Python相关的书",
    "查询ISBN是9787115461476的图书",
]

for i, query in enumerate(queries_1, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")
    
    messages = [{"role": "user", "content": query}]
    
    while True:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tool_choice="auto",
            tools=tools_1
        )
        
        tool_calls = res.choices[0].message.tool_calls
        
        if tool_calls:
            print(f"\n模型决策: 调用函数")
            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  函数名: {function_name}")
                print(f"  参数: {json.dumps(arguments, ensure_ascii=False)}")
                
                result = tools_map_1[function_name](**arguments)
                print(f"  返回: 找到 {len(result['books'])} 本图书")
                
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                    "tool_call_id": tool_call.id
                })
        else:
            print(f"\n模型决策: 生成最终回复")
            final_response = res.choices[0].message.content
            print(f"  AI回复: {final_response}")
            messages.append({"role": "assistant", "content": final_response})
            break


# ============================================================================
# 练习2: 日期计算工具
# ============================================================================

print("\n\n" + "=" * 80)
print("练习2: 实现计算工具 - 日期计算")
print("=" * 80)


def calculate_days(start_date, end_date):
    """计算两个日期之间的天数"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = abs((end - start).days)
        return {
            "success": True,
            "start": start_date,
            "end": end_date,
            "days": days
        }
    except:
        return {"success": False, "error": "日期格式错误"}


tools_2 = [
    {"type": "function", "function": {
        "name": "calculate_days",
        "description": "计算两个日期之间相差的天数，日期格式为YYYY-MM-DD",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"}
            },
            "required": ["start_date", "end_date"]
        }
    }}
]

tools_map_2 = {"calculate_days": calculate_days}

queries_2 = [
    "计算2024年1月1日到2024年12月31日有多少天",
    "从2024-06-01到2024-06-30相差几天",
]

for i, query in enumerate(queries_2, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")
    
    messages = [{"role": "user", "content": query}]
    
    while True:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tool_choice="auto",
            tools=tools_2
        )
        
        tool_calls = res.choices[0].message.tool_calls
        
        if tool_calls:
            print(f"\n模型决策: 调用函数")
            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  函数名: {function_name}")
                print(f"  参数: {json.dumps(arguments, ensure_ascii=False)}")
                
                result = tools_map_2[function_name](**arguments)
                
                if result['success']:
                    print(f"  返回: {result['days']} 天")
                else:
                    print(f"  错误: {result['error']}")
                
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                    "tool_call_id": tool_call.id
                })
        else:
            print(f"\n模型决策: 生成最终回复")
            final_response = res.choices[0].message.content
            print(f"  AI回复: {final_response}")
            messages.append({"role": "assistant", "content": final_response})
            break


# ============================================================================
# 练习3: CSV文件读取工具
# ============================================================================

print("\n\n" + "=" * 80)
print("练习3: 文件操作工具 - CSV文件读取")
print("=" * 80)


def read_csv(file_path):
    """读取CSV文件"""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": "文件不存在"}
        
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        
        return {
            "success": True,
            "rows": len(data),
            "columns": list(data[0].keys()) if data else [],
            "data": data[:3]  # 只返回前3行
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 创建测试CSV
test_dir = Path("test_data")
test_dir.mkdir(exist_ok=True)
csv_file = test_dir / "users.csv"

with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["姓名", "年龄", "城市"])
    writer.writerow(["张三", "28", "北京"])
    writer.writerow(["李四", "32", "上海"])

tools_3 = [
    {"type": "function", "function": {
        "name": "read_csv",
        "description": "读取CSV文件并返回数据，参数为文件路径",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "CSV文件路径"}
            },
            "required": ["file_path"]
        }
    }}
]

tools_map_3 = {"read_csv": read_csv}

print(f"\n测试文件: {csv_file}")
print(f"用户: 读取test_data/users.csv文件")

messages = [{"role": "user", "content": f"读取{csv_file}文件"}]

while True:
    res = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tool_choice="auto",
        tools=tools_3
    )
    
    tool_calls = res.choices[0].message.tool_calls
    
    if tool_calls:
        print(f"\n模型决策: 调用函数")
        messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"  函数名: {function_name}")
            print(f"  参数: {json.dumps(arguments, ensure_ascii=False)}")
            
            result = tools_map_3[function_name](**arguments)
            
            if result['success']:
                print(f"  返回: 读取 {result['rows']} 行数据")
                print(f"  列名: {result['columns']}")
            else:
                print(f"  错误: {result['error']}")
            
            messages.append({
                "role": "tool",
                "content": json.dumps(result, ensure_ascii=False),
                "tool_call_id": tool_call.id
            })
    else:
        print(f"\n模型决策: 生成最终回复")
        final_response = res.choices[0].message.content
        print(f"  AI回复: {final_response}")
        break

# 清理测试文件
csv_file.unlink()
test_dir.rmdir()


# ============================================================================
# 练习4: 天气查询工具（API集成）
# ============================================================================

print("\n\n" + "=" * 80)
print("练习4: API集成 - 天气查询工具")
print("=" * 80)


def get_weather(city):
    """获取天气（模拟API）"""
    weather_data = {
        "北京": {"temp": 15, "condition": "晴", "humidity": 45},
        "上海": {"temp": 18, "condition": "多云", "humidity": 65},
        "深圳": {"temp": 25, "condition": "阴", "humidity": 75},
    }
    
    if city in weather_data:
        data = weather_data[city]
        return {
            "success": True,
            "city": city,
            "temperature": data["temp"],
            "condition": data["condition"],
            "humidity": data["humidity"]
        }
    else:
        return {"success": False, "error": f"不支持城市'{city}'"}


tools_4 = [
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息，包括温度、天气状况、湿度",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如北京、上海"}
            },
            "required": ["city"]
        }
    }}
]

tools_map_4 = {"get_weather": get_weather}

queries_4 = [
    "北京今天天气怎么样？",
    "查询一下深圳的天气",
]

for i, query in enumerate(queries_4, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")
    
    messages = [{"role": "user", "content": query}]
    
    while True:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tool_choice="auto",
            tools=tools_4
        )
        
        tool_calls = res.choices[0].message.tool_calls
        
        if tool_calls:
            print(f"\n模型决策: 调用函数")
            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  函数名: {function_name}")
                print(f"  参数: {json.dumps(arguments, ensure_ascii=False)}")
                
                result = tools_map_4[function_name](**arguments)
                
                if result['success']:
                    print(f"  返回: {result['city']} {result['temperature']}°C {result['condition']}")
                else:
                    print(f"  错误: {result['error']}")
                
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                    "tool_call_id": tool_call.id
                })
        else:
            print(f"\n模型决策: 生成最终回复")
            final_response = res.choices[0].message.content
            print(f"  AI回复: {final_response}")
            messages.append({"role": "assistant", "content": final_response})
            break


# ============================================================================
# 练习5: 完整错误处理 - 用户注册工具
# ============================================================================

print("\n\n" + "=" * 80)
print("练习5: 错误处理 - 完整的输入验证和错误处理")
print("=" * 80)

USERS = []


def register_user(username, email, password):
    """用户注册（包含完整验证）"""
    # 1. 用户名验证
    if len(username) < 3:
        return {"success": False, "error": "用户名至少3个字符", "error_code": "INVALID_USERNAME"}
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return {"success": False, "error": "用户名只能包含字母、数字、下划线", "error_code": "INVALID_USERNAME"}
    
    if any(u['username'] == username for u in USERS):
        return {"success": False, "error": "用户名已存在", "error_code": "DUPLICATE_USERNAME"}
    
    # 2. 邮箱验证
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return {"success": False, "error": "邮箱格式不正确", "error_code": "INVALID_EMAIL"}
    
    # 3. 密码验证
    if len(password) < 8:
        return {"success": False, "error": "密码至少8个字符", "error_code": "WEAK_PASSWORD"}
    
    if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
        return {"success": False, "error": "密码必须包含字母和数字", "error_code": "WEAK_PASSWORD"}
    
    # 注册成功
    user_id = len(USERS) + 1
    USERS.append({"id": user_id, "username": username, "email": email})
    
    return {"success": True, "message": "注册成功", "user_id": user_id}


tools_5 = [
    {"type": "function", "function": {
        "name": "register_user",
        "description": "用户注册，需要用户名（3-20字符）、邮箱和密码（至少8位，含字母数字）",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "用户名"},
                "email": {"type": "string", "description": "邮箱地址"},
                "password": {"type": "string", "description": "密码"}
            },
            "required": ["username", "email", "password"]
        }
    }}
]

tools_map_5 = {"register_user": register_user}

test_cases = [
    "注册用户zhangsan，邮箱zhang@test.com，密码pass1234",
    "注册用户ab，邮箱test@test.com，密码pass1234",  # 用户名太短
    "注册用户lisi，邮箱invalid-email，密码pass1234",  # 邮箱错误
]

for i, query in enumerate(test_cases, 1):
    print(f"\n{'─' * 80}")
    print(f"【测试 {i}】")
    print(f"用户: {query}")
    
    messages = [{"role": "user", "content": query}]
    
    while True:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tool_choice="auto",
            tools=tools_5
        )
        
        tool_calls = res.choices[0].message.tool_calls
        
        if tool_calls:
            print(f"\n模型决策: 调用函数")
            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  函数名: {function_name}")
                print(f"  参数: {json.dumps(arguments, ensure_ascii=False)}")
                
                result = tools_map_5[function_name](**arguments)
                
                if result['success']:
                    print(f"  返回: ✓ {result['message']} (ID: {result['user_id']})")
                else:
                    print(f"  返回: ✗ {result['error']} ({result['error_code']})")
                
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                    "tool_call_id": tool_call.id
                })
        else:
            print(f"\n模型决策: 生成最终回复")
            final_response = res.choices[0].message.content
            print(f"  AI回复: {final_response}")
            messages.append({"role": "assistant", "content": final_response})
            break

print(f"\n当前注册用户: {len(USERS)} 个")
for user in USERS:
    print(f"  - ID:{user['id']} {user['username']} ({user['email']})")


print("\n\n" + "=" * 80)
print("所有练习执行完成")
print("=" * 80)
