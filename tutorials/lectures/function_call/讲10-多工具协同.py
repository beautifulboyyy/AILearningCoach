"""
讲10 | 多工具协同 - 实践练习
展示并行调用、工具链、重试、降级和复杂流程
"""

import json
import time
import concurrent.futures
from openai import OpenAI
from dotenv import load_dotenv

_ = load_dotenv()
client = OpenAI()


# ============================================================================
# 练习1: 理解并行调用的好处 - 同时查询3个城市的天气
# ============================================================================

print("=" * 80)
print("练习1: 并行调用 - 同时查询3个城市的天气")
print("=" * 80)


def get_weather(city):
    """获取天气（模拟API调用，每次耗时1秒）"""
    print(f"    → 正在查询{city}天气...")
    time.sleep(1)  # 模拟网络延迟

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


tools_1 = [
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息，包括温度、天气状况、湿度",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如北京、上海、深圳"}
            },
            "required": ["city"]
        }
    }}
]

tools_map_1 = {"get_weather": get_weather}

print("\n【测试】用户: 北京、上海、深圳今天天气怎么样？")

messages = [{"role": "user", "content": "北京、上海、深圳今天天气怎么样？"}]

# 第一次调用：LLM决定要调用哪些函数
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools_1,
    tool_choice="auto"
)

tool_calls = response.choices[0].message.tool_calls

if tool_calls:
    print(f"\n模型决策: 需要调用 {len(tool_calls)} 个函数")
    for tc in tool_calls:
        args = json.loads(tc.function.arguments)
        print(f"  - {tc.function.name}({args})")

    # 记录开始时间
    start_time = time.time()

    # 并行执行所有函数调用
    print("\n执行方式: 并行调用")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            # 提交到线程池
            future = executor.submit(tools_map_1[function_name], **arguments)
            futures.append((tool_call, future))

        # 收集结果
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls
        })

        for tool_call, future in futures:
            result = future.result()
            if result['success']:
                print(f"    ✓ {result['city']}: {result['temperature']}°C {result['condition']}")

            messages.append({
                "role": "tool",
                "content": json.dumps(result, ensure_ascii=False),
                "tool_call_id": tool_call.id
            })

    elapsed_time = time.time() - start_time
    print(f"\n总耗时: {elapsed_time:.2f}秒")
    print(f"说明: 如果串行调用需要3秒，并行调用只需要约{elapsed_time:.2f}秒")

    # 第二次调用：LLM生成最终回复
    final_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools_1
    )

    print(f"\nAI回复: {final_response.choices[0].message.content}")


print("\n" + "─" * 80)
print("练习1总结:")
print("✓ 并行调用适用于: 多个独立的工具调用，互不依赖")
print("✓ 性能优势: N个调用耗时≈1个调用的时间")
print("✗ 不适用于: 后续调用依赖前一个调用的结果")


# ============================================================================
# 练习2: 工具调用链 - 查询订单详情
# ============================================================================

print("\n\n" + "=" * 80)
print("练习2: 工具调用链 - 查询订单总价")
print("=" * 80)

# 模拟订单数据库
ORDERS_DB = {
    "ORD123": {
        "order_id": "ORD123",
        "items": [
            {"name": "Python编程书", "price": 89, "quantity": 2},
            {"name": "数据线", "price": 29, "quantity": 1}
        ]
    },
    "ORD456": {
        "order_id": "ORD456",
        "items": [
            {"name": "机械键盘", "price": 399, "quantity": 1}
        ]
    }
}


def get_order_info(order_id):
    """查询订单信息"""
    print(f"  → 步骤1: 查询订单 {order_id}")

    if order_id in ORDERS_DB:
        order = ORDERS_DB[order_id]
        return {
            "success": True,
            "order_id": order_id,
            "items": order["items"]
        }
    else:
        return {
            "success": False,
            "error": f"订单{order_id}不存在"
        }


def calculate_order_total(items):
    """计算订单总价"""
    print(f"  → 步骤2: 计算总价（基于{len(items)}个商品）")

    total = sum(item["price"] * item["quantity"] for item in items)

    return {
        "success": True,
        "total": total,
        "currency": "CNY"
    }


tools_2 = [
    {"type": "function", "function": {
        "name": "get_order_info",
        "description": "根据订单号查询订单详细信息，返回商品列表和数量",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "订单号，如ORD123"}
            },
            "required": ["order_id"]
        }
    }},
    {"type": "function", "function": {
        "name": "calculate_order_total",
        "description": "计算订单总价，输入商品列表（每个商品包含price和quantity）",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "商品列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                            "quantity": {"type": "integer"}
                        }
                    }
                }
            },
            "required": ["items"]
        }
    }}
]

tools_map_2 = {
    "get_order_info": get_order_info,
    "calculate_order_total": calculate_order_total
}

print("\n【测试】用户: 我的订单ORD123总共多少钱？")

messages = [{"role": "user", "content": "我的订单ORD123总共多少钱？"}]

# 执行工具调用链（最多迭代5次）
for iteration in range(5):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools_2,
        tool_choice="auto"
    )

    tool_calls = response.choices[0].message.tool_calls

    if not tool_calls:
        # 没有工具调用，说明LLM已经生成最终答案
        final_answer = response.choices[0].message.content
        print(f"\nAI回复: {final_answer}")
        break

    # 有工具调用，执行它们
    print(f"\n轮次{iteration + 1}: 调用工具")
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls
    })

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"  函数: {function_name}")
        print(f"  参数: {json.dumps(arguments, ensure_ascii=False)}")

        result = tools_map_2[function_name](**arguments)

        if result['success']:
            if 'total' in result:
                print(f"  返回: 总价 ¥{result['total']}")
            else:
                print(f"  返回: {len(result.get('items', []))} 个商品")
        else:
            print(f"  错误: {result['error']}")

        messages.append({
            "role": "tool",
            "content": json.dumps(result, ensure_ascii=False),
            "tool_call_id": tool_call.id
        })

print("\n" + "─" * 80)
print("练习2总结:")
print("✓ 工具调用链: 步骤1的输出是步骤2的输入")
print("✓ 依赖关系: 必须先查询订单，才能计算总价")
print("✓ LLM自动编排: 模型决定调用顺序和参数传递")


# ============================================================================
# 练习3: 重试策略 - 带重试的天气查询
# ============================================================================

print("\n\n" + "=" * 80)
print("练习3: 重试策略 - 处理API失败")
print("=" * 80)

# 模拟不稳定的API
call_count = {"count": 0}


def get_weather_unstable(city):
    """不稳定的天气API（前2次会失败）"""
    call_count["count"] += 1
    print(f"  → 第{call_count['count']}次尝试查询{city}天气...")
    
    # 前2次失败
    if call_count["count"] <= 2:
        time.sleep(0.5)
        return {
            "success": False,
            "error": "网络超时，请重试",
            "error_code": "TIMEOUT"
        }
    
    # 第3次成功
    time.sleep(0.5)
    return {
        "success": True,
        "city": city,
        "temperature": 20,
        "condition": "晴"
    }


def get_weather_with_retry(city, max_retries=3):
    """带重试的天气查询"""
    for attempt in range(max_retries):
        result = get_weather_unstable(city)
        
        if result['success']:
            print(f"    ✓ 成功!")
            return result
        else:
            print(f"    ✗ 失败: {result['error']}")
            
            if attempt < max_retries - 1:
                # 指数退避：1秒、2秒、4秒
                delay = 2 ** attempt
                print(f"    等待{delay}秒后重试...")
                time.sleep(delay)
            else:
                print(f"    已达到最大重试次数({max_retries})")
                return result


tools_3 = [
    {"type": "function", "function": {
        "name": "get_weather_with_retry",
        "description": "带重试机制的天气查询，最多重试3次",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        }
    }}
]

tools_map_3 = {"get_weather_with_retry": get_weather_with_retry}

print("\n【测试】用户: 查询北京天气")

call_count["count"] = 0  # 重置计数
messages = [{"role": "user", "content": "查询北京天气"}]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools_3,
    tool_choice="auto"
)

tool_calls = response.choices[0].message.tool_calls

if tool_calls:
    print(f"\n模型决策: 调用函数")
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls
    })
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        print(f"函数: {function_name}")
        print(f"参数: {json.dumps(arguments, ensure_ascii=False)}\n")
        
        result = tools_map_3[function_name](**arguments)
        
        messages.append({
            "role": "tool",
            "content": json.dumps(result, ensure_ascii=False),
            "tool_call_id": tool_call.id
        })
    
    # 生成最终回复
    final_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools_3
    )
    
    print(f"\nAI回复: {final_response.choices[0].message.content}")

print("\n" + "─" * 80)
print("练习3总结:")
print("✓ 重试策略: 遇到临时错误时自动重试")
print("✓ 指数退避: 等待时间逐渐增加（1秒→2秒→4秒）")
print("✓ 限制次数: 防止无限重试，保护系统资源")
print("✗ 不重试: 永久性错误（如参数错误）不应该重试")


# ============================================================================
# 练习4: 降级策略 - 搜索功能的多级降级
# ============================================================================

print("\n\n" + "=" * 80)
print("练习4: 降级策略 - 搜索功能备用方案")
print("=" * 80)


def ai_search(query):
    """AI智能搜索（主方案，可能失败）"""
    print(f"  → 方案1: AI智能搜索 '{query}'")
    
    # 模拟AI搜索失败（50%概率）
    import random
    if random.random() < 0.7:  # 70%失败率
        time.sleep(0.3)
        print(f"    ✗ AI搜索服务不可用")
        raise Exception("AI搜索服务超时")
    
    return {
        "method": "AI搜索",
        "results": [
            {"title": "Python高级教程", "relevance": 0.95},
            {"title": "Python实战项目", "relevance": 0.92}
        ]
    }


def database_search(query):
    """数据库搜索（备用方案1）"""
    print(f"  → 方案2: 数据库关键词搜索 '{query}'")
    time.sleep(0.2)
    
    return {
        "method": "数据库搜索",
        "results": [
            {"title": "Python基础教程", "relevance": 0.75},
            {"title": "Python入门指南", "relevance": 0.70}
        ]
    }


def get_popular_results():
    """热门推荐（备用方案2）"""
    print(f"  → 方案3: 返回热门推荐")
    time.sleep(0.1)
    
    return {
        "method": "热门推荐",
        "results": [
            {"title": "热门课程1", "relevance": 0.5},
            {"title": "热门课程2", "relevance": 0.5}
        ]
    }


def search_with_fallback(query):
    """带降级的搜索"""
    # 尝试方案1: AI搜索
    try:
        result = ai_search(query)
        print(f"    ✓ 使用: {result['method']}")
        return {"success": True, **result}
    except Exception as e:
        print(f"    ✗ 失败，尝试降级...")
        
        # 尝试方案2: 数据库搜索
        try:
            result = database_search(query)
            print(f"    ✓ 使用: {result['method']}")
            return {"success": True, **result}
        except Exception as e:
            print(f"    ✗ 失败，继续降级...")
            
            # 方案3: 热门推荐（总是成功）
            result = get_popular_results()
            print(f"    ✓ 使用: {result['method']}")
            return {"success": True, **result}


tools_4 = [
    {"type": "function", "function": {
        "name": "search_with_fallback",
        "description": "搜索内容，自动使用最佳可用方案（AI搜索→数据库搜索→热门推荐）",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }
    }}
]

tools_map_4 = {"search_with_fallback": search_with_fallback}

print("\n【测试】用户: 搜索Python教程")

messages = [{"role": "user", "content": "搜索Python教程"}]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools_4,
    tool_choice="auto"
)

tool_calls = response.choices[0].message.tool_calls

if tool_calls:
    print(f"\n模型决策: 调用搜索功能\n")
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls
    })
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        result = tools_map_4[function_name](**arguments)
        
        print(f"\n最终结果:")
        print(f"  方法: {result['method']}")
        print(f"  找到: {len(result['results'])} 个结果")
        for r in result['results']:
            print(f"    - {r['title']} (相关度: {r['relevance']})")
        
        messages.append({
            "role": "tool",
            "content": json.dumps(result, ensure_ascii=False),
            "tool_call_id": tool_call.id
        })
    
    # 生成最终回复
    final_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools_4
    )
    
    print(f"\nAI回复: {final_response.choices[0].message.content}")

print("\n" + "─" * 80)
print("练习4总结:")
print("✓ 降级策略: 主方案失败时自动切换到备用方案")
print("✓ 保证可用: 即使所有高级方案失败，也能返回基础结果")
print("✓ 用户体验: 用户感知不到失败，只是结果质量略有下降")


# ============================================================================
# 练习5: 复杂流程 - 智能酒店预订助手
# ============================================================================

print("\n\n" + "=" * 80)
print("练习5: 复杂流程 - 智能酒店预订助手")
print("=" * 80)

# 全局状态
booking_state = {}


def collect_travel_info(destination, check_in_date=None, nights=None, budget=None):
    """收集旅行信息"""
    print(f"  → 步骤1: 收集信息")
    print(f"    目的地: {destination}")
    
    booking_state['destination'] = destination
    booking_state['check_in_date'] = check_in_date
    booking_state['nights'] = nights
    booking_state['budget'] = budget
    
    missing = []
    if not check_in_date:
        missing.append("入住日期")
    if not nights:
        missing.append("住宿晚数")
    if not budget:
        missing.append("预算")
    
    if missing:
        return {
            "success": False,
            "message": f"还需要以下信息: {', '.join(missing)}"
        }
    
    return {
        "success": True,
        "message": "信息收集完成",
        "data": booking_state
    }


def search_hotels(destination, budget):
    """搜索酒店"""
    print(f"  → 步骤2A: 搜索{destination}的酒店（预算¥{budget}）")
    time.sleep(0.8)
    
    hotels = [
        {"name": "北京国际酒店", "price": 599, "rating": 4.5},
        {"name": "北京商务酒店", "price": 399, "rating": 4.2},
        {"name": "北京快捷酒店", "price": 199, "rating": 3.8}
    ]
    
    # 根据预算筛选
    suitable = [h for h in hotels if h['price'] <= budget]
    
    return {
        "success": True,
        "hotels": suitable,
        "count": len(suitable)
    }


def get_weather_forecast(city, date):
    """查询天气预报"""
    print(f"  → 步骤2B: 查询{city}的天气（{date}）")
    time.sleep(0.8)
    
    return {
        "success": True,
        "city": city,
        "date": date,
        "forecast": "晴，15-25°C"
    }


def recommend_hotel(hotels, weather, budget):
    """推荐酒店"""
    print(f"  → 步骤3: 综合推荐")
    
    if not hotels:
        return {
            "success": False,
            "message": "没有符合条件的酒店"
        }
    
    # 简单推荐：性价比最高
    best = max(hotels, key=lambda h: h['rating'] / h['price'])
    
    return {
        "success": True,
        "recommendation": best,
        "reason": f"性价比高，评分{best['rating']}分"
    }


def book_hotel(hotel_name):
    """预订酒店"""
    print(f"  → 步骤4: 预订酒店 '{hotel_name}'")
    time.sleep(0.5)
    
    return {
        "success": True,
        "confirmation_code": "BK20240107001",
        "hotel_name": hotel_name,
        "message": "预订成功"
    }


tools_5 = [
    {"type": "function", "function": {
        "name": "collect_travel_info",
        "description": "收集旅行信息，包括目的地、入住日期、住宿晚数、预算",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "目的地城市"},
                "check_in_date": {"type": "string", "description": "入住日期 YYYY-MM-DD"},
                "nights": {"type": "integer", "description": "住宿晚数"},
                "budget": {"type": "number", "description": "每晚预算（元）"}
            },
            "required": ["destination"]
        }
    }},
    {"type": "function", "function": {
        "name": "search_hotels",
        "description": "搜索酒店，返回符合预算的酒店列表",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "budget": {"type": "number"}
            },
            "required": ["destination", "budget"]
        }
    }},
    {"type": "function", "function": {
        "name": "get_weather_forecast",
        "description": "查询天气预报",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "date": {"type": "string"}
            },
            "required": ["city", "date"]
        }
    }},
    {"type": "function", "function": {
        "name": "recommend_hotel",
        "description": "根据酒店列表、天气和预算推荐最合适的酒店",
        "parameters": {
            "type": "object",
            "properties": {
                "hotels": {"type": "array", "items": {"type": "object"}},
                "weather": {"type": "object"},
                "budget": {"type": "number"}
            },
            "required": ["hotels", "weather", "budget"]
        }
    }},
    {"type": "function", "function": {
        "name": "book_hotel",
        "description": "预订指定的酒店",
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_name": {"type": "string", "description": "酒店名称"}
            },
            "required": ["hotel_name"]
        }
    }}
]

tools_map_5 = {
    "collect_travel_info": collect_travel_info,
    "search_hotels": search_hotels,
    "get_weather_forecast": get_weather_forecast,
    "recommend_hotel": recommend_hotel,
    "book_hotel": book_hotel
}

print("\n【测试】用户: 我要去北京旅游，1月15日入住，住2晚，预算500元")

messages = [{
    "role": "user",
    "content": "我要去北京旅游，1月15日入住，住2晚，预算500元，帮我订个酒店"
}]

# 执行复杂工作流（最多迭代10次）
for iteration in range(10):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools_5,
        tool_choice="auto"
    )
    
    tool_calls = response.choices[0].message.tool_calls
    
    if not tool_calls:
        # 完成
        final_answer = response.choices[0].message.content
        print(f"\n{'─' * 60}")
        print(f"AI回复: {final_answer}")
        break
    
    # 执行工具调用
    if iteration == 0:
        print(f"\n工作流开始:\n")
    
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls
    })
    
    # 检查是否有并行调用
    if len(tool_calls) > 1:
        print(f"【并行执行 {len(tool_calls)} 个任务】")
        
        # 并行执行
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                future = executor.submit(tools_map_5[function_name], **arguments)
                futures.append((tool_call, future))
            
            for tool_call, future in futures:
                result = future.result()
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                    "tool_call_id": tool_call.id
                })
    else:
        # 串行执行
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            result = tools_map_5[function_name](**arguments)
            
            messages.append({
                "role": "tool",
                "content": json.dumps(result, ensure_ascii=False),
                "tool_call_id": tool_call.id
            })
    
    print()

print("\n" + "─" * 80)
print("练习5总结:")
print("✓ 复杂流程: 包含串行和并行的混合执行")
print("✓ 步骤1: 收集信息（串行，必须先做）")
print("✓ 步骤2: 搜索酒店 + 查天气（并行，可同时进行）")
print("✓ 步骤3: 推荐酒店（串行，需要步骤2的结果）")
print("✓ 步骤4: 确认预订（串行，需要用户确认）")
print("✓ LLM智能编排: 自动识别哪些可并行，哪些需串行")


print("\n\n" + "=" * 80)
print("所有练习完成!")
print("=" * 80)
print("\n核心要点:")
print("1. 并行调用: 独立任务同时执行，大幅提升性能")
print("2. 工具调用链: 步骤化处理复杂任务，前后依赖")
print("3. 重试策略: 临时故障自动重试，指数退避")
print("4. 降级策略: 主方案失败时使用备用方案，保证可用性")
print("5. 复杂流程: 混合使用并行和串行，LLM智能编排")

