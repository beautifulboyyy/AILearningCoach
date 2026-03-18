"""
Agent消息组装工具
"""
from typing import Any, Dict, List
import json


def normalize_history(history: Any) -> List[Dict[str, str]]:
    """
    规范化对话历史，过滤非法消息。
    """
    if not isinstance(history, list):
        return []

    normalized: List[Dict[str, str]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant", "system"}:
            continue
        if not isinstance(content, str) or not content.strip():
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def build_context_note(context: Dict[str, Any]) -> str:
    """
    将上下文中的背景信息转为简洁说明，用于system消息补充。
    """
    lines: List[str] = []

    user_profile = context.get("user_profile") or {}
    if user_profile:
        lines.append("## 用户画像")
        lines.append(f"- 职业: {user_profile.get('occupation', '未知')}")
        lines.append(f"- 学习目标: {user_profile.get('learning_goal', '未知')}")
        current_level = user_profile.get("current_level")
        if current_level:
            lines.append(f"- 当前水平: {json.dumps(current_level, ensure_ascii=False)}")

    learning_progress = context.get("learning_progress") or {}
    if learning_progress:
        lines.append("## 学习进度")
        completed = learning_progress.get("completed_modules")
        if completed:
            if isinstance(completed, list):
                lines.append(f"- 已完成模块: {', '.join(str(item) for item in completed[:5])}")
            else:
                lines.append(f"- 已完成模块: {completed}")
        completion = learning_progress.get("overall_completion")
        if completion is not None:
            lines.append(f"- 总体完成度: {completion}%")
        current_module = learning_progress.get("current_module")
        if current_module:
            lines.append(f"- 当前模块: {current_module}")

    short_term_memory = context.get("short_term_memory") or []
    if isinstance(short_term_memory, list) and short_term_memory:
        lines.append("## 会话短期记忆")
        for memory in short_term_memory[-3:]:
            if not isinstance(memory, dict):
                continue
            content = memory.get("content")
            if isinstance(content, str) and content.strip():
                lines.append(f"- {content[:200]}")
                continue
            user_message = memory.get("metadata", {}).get("user_message") if isinstance(memory.get("metadata"), dict) else None
            assistant_message = memory.get("metadata", {}).get("assistant_message") if isinstance(memory.get("metadata"), dict) else None
            if user_message or assistant_message:
                lines.append(f"- 用户: {(user_message or '')[:80]} | 助手: {(assistant_message or '')[:80]}")

    conversation_summary = context.get("conversation_summary")
    if isinstance(conversation_summary, str) and conversation_summary.strip():
        lines.append("## 会话摘要")
        lines.append(conversation_summary.strip()[:1000])

    return "\n".join(lines).strip()


def build_agent_messages(
    system_prompt: str,
    user_input: str,
    context: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    统一组装给LLM的消息列表。
    """
    context_note = build_context_note(context)
    system_content = system_prompt.strip()
    if context_note:
        system_content = f"{system_content}\n\n以下是本轮可用上下文，请结合使用：\n{context_note}"

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
    messages.extend(normalize_history(context.get("recent_history")))
    messages.append({"role": "user", "content": user_input})
    return messages
