#!/usr/bin/env python3
"""Deep Research 端到端测试脚本"""
import requests
import json
import time
import sys
import os
import subprocess
import signal
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"
TOPIC = "LangGraph 框架的优势分析"

# 颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log(msg: str, color: str = ""):
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {msg}{RESET}")


def wait_for_server(timeout: int = 30):
    """等待服务启动"""
    log("等待服务启动...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                log("服务已就绪", GREEN)
                return True
        except:
            pass
        time.sleep(1)
    return False


def check_api_keys():
    """检查API keys"""
    from dotenv import load_dotenv
    load_dotenv()

    keys = {
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
        "BOCHA_API_KEY": os.getenv("BOCHA_API_KEY"),
    }

    for name, value in keys.items():
        if value:
            log(f"{name}: {value[:8]}...", GREEN)
        else:
            log(f"{name}: 未设置!", RED)
            return False
    return True


def start_research():
    """开始研究任务"""
    log(f"开始研究: {TOPIC}", BLUE)

    resp = requests.post(
        f"{API_BASE}/deep-research/start",
        json={"topic": TOPIC, "max_analysts": 2},
        timeout=30
    )

    if resp.status_code != 200:
        log(f"启动失败: {resp.status_code} - {resp.text}", RED)
        return None

    data = resp.json()
    thread_id = data["thread_id"]
    log(f"任务已创建: {thread_id}", GREEN)
    log(f"状态: {data['status']}")
    return thread_id


def stream_events(thread_id: str):
    """获取SSE事件流"""
    log("开始获取研究进度...", BLUE)

    try:
        resp = requests.get(
            f"{API_BASE}/deep-research/{thread_id}/events",
            stream=True,
            timeout=300
        )

        if resp.status_code != 200:
            log(f"获取事件流失败: {resp.status_code}", RED)
            return

        event_count = 0
        for line in resp.iter_lines(decode_unicode=True):
            if line:
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    event_count += 1
                    log(f"[事件 {event_count}] {json.dumps(data, ensure_ascii=False)[:200]}", YELLOW)

                    # 如果是完成或错误，退出
                    if data.get("type") in ("done", "error"):
                        break

        log(f"流式事件接收完成，共 {event_count} 个事件", GREEN)

    except requests.exceptions.Timeout:
        log("获取事件超时", RED)
    except Exception as e:
        log(f"获取事件异常: {e}", RED)


def get_task_status(thread_id: str):
    """获取任务状态"""
    resp = requests.get(f"{API_BASE}/deep-research/{thread_id}", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        log(f"任务状态: {data['status']}", BLUE)
        if data.get("final_report"):
            log(f"报告长度: {len(data['final_report'])} 字符", GREEN)
        return data
    return None


def main():
    print("=" * 60)
    log("Deep Research 端到端测试", BLUE)
    print("=" * 60)

    # 检查 API keys
    if not check_api_keys():
        log("API keys 检查失败，退出", RED)
        sys.exit(1)

    # 等待服务
    if not wait_for_server():
        log("服务启动超时，请先运行: python main.py", RED)
        sys.exit(1)

    # 启动研究
    thread_id = start_research()
    if not thread_id:
        sys.exit(1)

    # 获取事件流
    stream_events(thread_id)

    # 最终状态
    get_task_status(thread_id)

    print("=" * 60)
    log("测试完成", GREEN)
    print("=" * 60)


if __name__ == "__main__":
    main()
