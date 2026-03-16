# 练习1：基础调用
import os
import time

from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import asyncio

_ = load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')


def sync_openai_api_block():
    client = OpenAI(base_url="http://182.242.159.112:6666/v1",api_key="xxx")
    res = client.chat.completions.create(model="qwen3-8b",
                                         messages=[{"role": "user", "content": "你好，你叫什么名字"}], stream=False)
    print(res)
    print(res.choices[0].message.content)


def sync_openai_api_stream():
    client = OpenAI()
    res = client.chat.completions.create(model="deepseek-chat",
                                         messages=[{"role": "user", "content": "你好，你叫什么名字"}], stream=True)
    for chunk in res:
        print(chunk.choices[0].delta.content, end="")


async def async_openai_api_block():
    start_time = time.time()
    client = AsyncOpenAI()
    res = await client.chat.completions.create(model="deepseek-chat",
                                               messages=[{"role": "user", "content": "你好，你叫什么名字"}],
                                               stream=False)
    print(time.time() - start_time)
    print(res)


async def async_openai_api_stream():
    start_time = time.time()
    client = AsyncOpenAI()

    res = await client.chat.completions.create(model="deepseek-chat",
                                               messages=[{"role": "user", "content": "你好，你叫什么名字"}], stream=True)
    async for chunk in res:
        print(time.time() - start_time)
        print(chunk.choices[0].delta.content, end="")


# 练习2：参数实验

def temperature_llm():
    client = OpenAI()
    temperature_list = [0, 0.5, 1, 1.5]
    for temperature in temperature_list:
        res = client.chat.completions.create(model="deepseek-chat",
                                             messages=[
                                                 {"role": "user", "content": "请用一个形容词形容一下春天是什么样子"}],
                                             stream=False, temperature=temperature)
        print("温度为{}:".format(temperature), res.choices[0].message.content)


# 练习3：多轮对话
def mutil_message_llm():
    client = OpenAI()
    messages = [{"role": "system", "content": "你是一位智能助手，你的名字叫小艺"}]
    max_round = 10
    counter = 0
    while counter <= max_round:
        query = input("请输入指令：")
        messages.append({"role": "user", "content": query})
        res = client.chat.completions.create(model="deepseek-chat",
                                             messages=messages, stream=True)
        content = ""
        for chunk in res:
            print(chunk.choices[0].delta.content, end="")
            content += chunk.choices[0].delta.content
        messages.append({"role": "assistant", "content": content})
        counter += 1
    print(messages)


# 练习4：流式输出
def sync_openai_api_stream():
    client = OpenAI()
    res = client.chat.completions.create(model="deepseek-chat",
                                         messages=[{"role": "user", "content": "你好，你叫什么名字"}], stream=True)
    for chunk in res:
        print(chunk.choices[0].delta.content, end="")


if __name__ == '__main__':
    sync_openai_api_block()

