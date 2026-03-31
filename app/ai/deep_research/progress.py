"""Deep Research 运行时进度跟踪。"""
from datetime import datetime
from typing import Dict


_progress_store: Dict[str, Dict[str, str]] = {}


def get_progress(thread_id: str) -> Dict[str, str]:
    """获取任务当前运行时进度。"""
    return _progress_store.get(thread_id, {
        "thread_id": thread_id,
        "stage": "idle",
        "message": "",
        "updated_at": "",
    })


def update_progress(thread_id: str, stage: str, message: str) -> Dict[str, str]:
    """更新任务运行时进度。"""
    progress = {
        "thread_id": thread_id,
        "stage": stage,
        "message": message,
        "updated_at": datetime.utcnow().isoformat(),
    }
    _progress_store[thread_id] = progress
    return progress


def clear_progress(thread_id: str) -> None:
    """清理任务运行时进度。"""
    _progress_store.pop(thread_id, None)
