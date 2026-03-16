import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import OpenAI
from langchain_core.tools import tool
from langchain.messages import AIMessage, SystemMessage, ToolMessage, HumanMessage
from langchain_openai import ChatOpenAI

_ = load_dotenv("../.env")


@tool()
def get_weather(city:str):
    """这是一个获取城市天气信息的工具"""
    weather_map = {
        "北京": "今天多云转晴，气温-8~4°C，北风转西风1级，早晚寒冷需注意防寒保暖。",
        "成都": "今日多云，气温3~13°C，微风，天气逐步转好但昼夜温差明显，早晚寒意袭人。",
        "广州": "今天晴天，气温6~17°C，北风3级，干晴持续，昼夜温差大，早晚寒冷。",
        "杭州": "今日晴，气温1~11°C，东北风转西北风1级，天气晴朗，体感温度约9°C。",
        "上海": "今日以晴或多云为主，气温2~10°C，空气质量良好，偏西风主导，天气晴冷。"
    }
    return {"success": True, "data": {
        "weather_info": weather_map[city]
    }}

tools = [get_weather]
tool_map = {
    "get_weather": get_weather
}

# llm = ChatOpenAI(model="deepseek-chat")
# with_tool_llm = llm.bind_tools(tools)
#
# messages = [SystemMessage(content="你是一位智能助手，你的名字叫小智"),
#             HumanMessage(content="请告诉我现在北京的天气怎么样")]
#
# while True:
#     res = with_tool_llm.invoke(messages)
#     if res.tool_calls:
#         messages.append(res)
#         for tool in res.tool_calls:
#             funtion_name = tool["name"]
#             result = tool_map[funtion_name].invoke(tool)
#             messages.append(result)
#     else:
#         messages.append(res)
#         break
#
# print(messages)


def get_current_time():
    """这是一个获取当前时间都工具。当用户询问当前时间等类型的指令的时候，即调用此工具进行回答"""
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"success": True, "data": {
        "time": now_time
    }}


tools = [
    {"type": "function", "function": {
        "name": "get_current_time",
        "description": "这是一个获取当前时间都工具。当用户询问当前时间等类型的指令的时候，即调用此工具进行回答"
    }},
]

tools_map = {
    "get_current_time": get_current_time
}

client = OpenAI()

messages = [{"role": "system", "content": "你是一位智能助手，你的名字叫小智"},
            {"role": "user", "content": "请告诉我现在几点钟"}]

while True:
    res = client.chat.completions.create(model="deepseek-chat",
                                         messages=messages, tool_choice="required",
                                         tools=tools)
    tool_call = res.choices[0].message.tool_calls
    if tool_call:
        messages.append({"role": "assistant", "content": None, "tool_calls": tool_call})
        for tool in tool_call:
            function_name = tool.function.name
            arguments = json.loads(tool.function.arguments)
            function_result = tools_map[function_name](**arguments)
            print(function_result)
            messages.append({"role": "tool", "content": json.dumps(function_result), "tool_call_id": tool.id})

    else:
        messages.append({"role": "assistant", "content": res.choices[0].message.content})
        break

print(messages)


## MCP 调用的方式
# client = OpenAI()
#
#
# async def learn_mcp_client():
#     async with sse_client("http://localhost:8000/sse") as (file_read, file_write):
#         async with ClientSession(file_read, file_write) as file_session:
#             await file_session.initialize()
#
#             tool_list = await file_session.list_tools()
#             tools = [{"type": "function",
#                       "function": {"name": tool.name, "description": tool.description, "parameters": tool.inputSchema}}
#                      for tool in tool_list.tools]
#             messages = [{"role": "system", "content": "你是一名智能助手"},
#                         {"role": "user", "content": "有多少个Python文件？"}]
#             while True:
#                 res = client.chat.completions.create(model="deepseek-chat",
#                                                      messages=messages, tools=tools, tool_choice="auto")
#                 tool_call = res.choices[0].message.tool_calls
#                 if tool_call:
#                     messages.append({"role": "assistant", "content": None, "tool_calls": tool_call})
#                     for tool in tool_call:
#                         function_name = tool.function.name
#                         print(function_name)
#                         arguments = json.loads(tool.function.arguments)
#                         function_result = await file_session.call_tool(function_name, arguments)
#                         messages.append(
#                             {"role": "tool", "content": function_result.content[0].text, "tool_call_id": tool.id})
#
#                 else:
#                     messages.append({"role": "assistant", "content": res.choices[0].message.content})
#                     break
#             print(messages)
#
#
# if __name__ == '__main__':
#     asyncio.run(learn_mcp_client())
