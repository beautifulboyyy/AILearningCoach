from app.ai.agents.message_builder import (
    normalize_history,
    build_context_note,
    build_agent_messages,
)


def test_normalize_history_filters_invalid_items():
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
        {"role": "tool", "content": "ignored"},
        {"role": "user", "content": "   "},
        "invalid",
    ]
    normalized = normalize_history(history)
    assert len(normalized) == 2
    assert normalized[0]["role"] == "user"
    assert normalized[1]["role"] == "assistant"


def test_build_context_note_contains_summary_and_short_term_memory():
    context = {
        "user_profile": {"occupation": "工程师", "learning_goal": "systematic_learning"},
        "learning_progress": {"overall_completion": 40, "current_module": "RAG"},
        "short_term_memory": [
            {"content": "用户在学习RAG基础"},
            {"metadata": {"user_message": "向量数据库怎么选", "assistant_message": "可以先用Milvus"}}
        ],
        "conversation_summary": "用户正在构建多轮对话系统，重点关注上下文记忆。"
    }
    note = build_context_note(context)
    assert "会话摘要" in note
    assert "会话短期记忆" in note
    assert "多轮对话系统" in note


def test_build_agent_messages_order():
    context = {
        "recent_history": [
            {"role": "user", "content": "上次我们聊到哪了？"},
            {"role": "assistant", "content": "聊到了RAG的召回和重排。"},
        ],
        "conversation_summary": "在实现RAG问答系统。"
    }
    messages = build_agent_messages("你是测试助手。", "继续说说重排。", context)
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    assert messages[-1]["content"] == "继续说说重排。"
