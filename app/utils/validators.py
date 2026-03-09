"""
验证工具模块
"""
import re
from typing import Optional


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    验证用户名
    
    Args:
        username: 用户名
    
    Returns:
        (是否有效, 错误信息)
    """
    if not username:
        return False, "用户名不能为空"
    
    if len(username) < 3 or len(username) > 50:
        return False, "用户名长度必须在3-50个字符之间"
    
    # 只允许字母、数字、下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    验证邮箱
    
    Args:
        email: 邮箱
    
    Returns:
        (是否有效, 错误信息)
    """
    if not email:
        return False, "邮箱不能为空"
    
    # 简单的邮箱正则验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "邮箱格式不正确"
    
    return True, None


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    验证密码强度
    
    Args:
        password: 密码
    
    Returns:
        (是否有效, 错误信息)
    """
    if not password:
        return False, "密码不能为空"
    
    if len(password) < 6:
        return False, "密码长度不能少于6个字符"
    
    if len(password) > 100:
        return False, "密码长度不能超过100个字符"
    
    # 密码必须包含字母和数字
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    
    if not (has_letter and has_digit):
        return False, "密码必须同时包含字母和数字"
    
    return True, None


def sanitize_content(content: str, max_length: int = 10000) -> str:
    """
    清理内容（防止XSS等）
    
    Args:
        content: 内容
        max_length: 最大长度
    
    Returns:
        清理后的内容
    """
    if not content:
        return ""
    
    # 移除HTML标签
    content = re.sub(r'<[^>]+>', '', content)
    
    # 移除多余空白
    content = re.sub(r'\s+', ' ', content).strip()
    
    # 限制长度
    if len(content) > max_length:
        content = content[:max_length]
    
    return content


def validate_session_id(session_id: str) -> tuple[bool, Optional[str]]:
    """
    验证会话ID格式
    
    Args:
        session_id: 会话ID
    
    Returns:
        (是否有效, 错误信息)
    """
    if not session_id:
        return False, "会话ID不能为空"
    
    # 会话ID应该是UUID或类似格式
    if len(session_id) < 10 or len(session_id) > 100:
        return False, "会话ID格式不正确"
    
    return True, None
