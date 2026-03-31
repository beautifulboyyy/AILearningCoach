"""节点函数测试"""
from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from app.ai.deep_research.nodes import (
    dedupe_sources,
    finalize_report,
    format_report_sources,
    route_messages,
    write_conclusion,
    write_introduction,
    write_report,
    write_section,
)
from app.ai.deep_research.state import GenerateAnalystsState


def test_generate_analysts_state_structure():
    """测试状态结构"""
    state = GenerateAnalystsState(
        topic="测试主题",
        max_analysts=3,
        human_analyst_feedback="",
        analysts=[]
    )
    assert state["topic"] == "测试主题"
    assert state["max_analysts"] == 3


def test_route_messages_stops_after_max_turns():
    """测试专家回答次数达到上限后结束访谈"""
    state = {
        "messages": [
            HumanMessage(content="问题1"),
            AIMessage(content="回答1", name="expert"),
            HumanMessage(content="问题2"),
            AIMessage(content="回答2", name="expert"),
            HumanMessage(content="问题3"),
            AIMessage(content="回答3", name="expert"),
        ],
        "max_num_turns": 3,
    }

    assert route_messages(state) == "save_interview"


def test_route_messages_stops_when_human_message_thanks():
    """测试分析师在上一轮致谢时结束访谈"""
    state = {
        "messages": [
            HumanMessage(content="前置问题"),
            AIMessage(content="前置回答", name="expert"),
            HumanMessage(content="非常感谢您的帮助!"),
            AIMessage(content="不客气", name="expert"),
        ],
        "max_num_turns": 5,
    }

    assert route_messages(state) == "save_interview"


def test_route_messages_continues_when_turns_not_reached():
    """测试未达到结束条件时继续提问"""
    state = {
        "messages": [
            HumanMessage(content="问题"),
            AIMessage(content="回答", name="expert"),
        ],
        "max_num_turns": 3,
    }

    assert route_messages(state) == "ask_question"


def test_finalize_report_strips_insights_and_keeps_sources():
    """测试最终报告会去掉主体中的 Insights 标题并保留 Sources"""
    state = {
        "introduction": "## 引言\n引言内容",
        "content": "## Insights\n主体内容\n## Sources\n[1] https://example.com",
        "conclusion": "## 结论\n结论内容",
    }

    result = finalize_report(state)

    assert result["final_report"].startswith("## 引言")
    assert "主体内容" in result["final_report"]
    assert "## Insights" not in result["final_report"]
    assert "## Sources\n[1] https://example.com" in result["final_report"]


def test_dedupe_sources_keeps_first_url_order():
    """测试来源按 URL 去重并保留首次出现顺序"""
    sources = [
        {"url": "https://a.example.com", "title": "A1"},
        {"url": "https://b.example.com", "title": "B"},
        {"url": "https://a.example.com", "title": "A2"},
        {"url": "", "title": "empty"},
    ]

    result = dedupe_sources(sources)

    assert [item["url"] for item in result] == [
        "https://a.example.com",
        "https://b.example.com",
    ]
    assert result[0]["title"] == "A1"


def test_format_report_sources_groups_urls_by_section():
    """测试最终引用区会按小节组织 URL 引用"""
    section_documents = [
        {
            "title": "Agent 架构",
            "sources": [
                {"url": "https://a.example.com", "title": "A"},
                {"url": "https://b.example.com", "title": "B"},
            ],
        },
        {
            "title": "治理",
            "sources": [
                {"url": "https://b.example.com", "title": "B again"},
                {"url": "https://c.example.com", "title": "C"},
            ],
        },
    ]

    markdown = format_report_sources(section_documents)

    assert markdown.startswith("## 引用")
    assert "### Agent 架构" in markdown
    assert "### 治理" in markdown
    assert "https://a.example.com" in markdown
    assert "https://c.example.com" in markdown
    assert markdown.count("https://b.example.com") == 1


def test_format_report_sources_limits_urls_per_section_and_total():
    """测试最终引用区会限制每个小节和全局的 URL 数量"""
    section_documents = [
        {
            "title": "小节一",
            "sources": [
                {"url": f"https://one-{idx}.example.com", "title": f"One {idx}"}
                for idx in range(1, 6)
            ],
        },
        {
            "title": "小节二",
            "sources": [
                {"url": f"https://two-{idx}.example.com", "title": f"Two {idx}"}
                for idx in range(1, 6)
            ],
        },
        {
            "title": "小节三",
            "sources": [
                {"url": f"https://three-{idx}.example.com", "title": f"Three {idx}"}
                for idx in range(1, 6)
            ],
        },
    ]

    markdown = format_report_sources(section_documents)

    assert markdown.count("URL:") <= 8
    assert "https://one-4.example.com" not in markdown
    assert "https://three-4.example.com" not in markdown


def test_finalize_report_prefers_structured_section_urls():
    """测试最终报告会附加基于小节元信息生成的 URL 引用"""
    state = {
        "introduction": "## 引言\n引言内容",
        "content": "## Insights\n主体内容\n## Sources\n[1] 旧的来源占位",
        "conclusion": "## 结论\n结论内容",
        "section_documents": [
            {
                "title": "Agent 架构",
                "sources": [
                    {"url": "https://a.example.com", "title": "A"},
                    {"url": "https://b.example.com", "title": "B"},
                ],
            }
        ],
    }

    result = finalize_report(state)

    assert "主体内容" in result["final_report"]
    assert "## 引用" in result["final_report"]
    assert "https://a.example.com" in result["final_report"]
    assert "旧的来源占位" not in result["final_report"]


def test_finalize_report_uses_main_body_heading_and_trimmed_sources():
    """测试最终报告包含明确主体标题且引用区为收口后的结构化 URL"""
    state = {
        "introduction": "# Agent 研究报告\n\n## 引言\n引言内容",
        "content": "## 主体内容\n### 架构趋势\n主体段落",
        "conclusion": "## 结论\n结论内容",
        "section_documents": [
            {
                "title": "架构趋势",
                "sources": [
                    {"url": "https://a.example.com", "title": "A"},
                    {"url": "https://b.example.com", "title": "B"},
                ],
            },
            {
                "title": "应用落地",
                "sources": [
                    {"url": "https://c.example.com", "title": "C"},
                ],
            },
        ],
    }

    result = finalize_report(state)

    assert "# Agent 研究报告" in result["final_report"]
    assert "## 引言" in result["final_report"]
    assert "## 主体内容" in result["final_report"]
    assert "## 结论" in result["final_report"]
    assert "## 引用" in result["final_report"]
    assert result["final_report"].count("URL:") <= 8


class _FakeStructuredLLM:
    def __init__(self, search_query: str):
        self.search_query = search_query

    def invoke(self, _messages):
        return SimpleNamespace(search_query=self.search_query)


class _FakeLLM:
    def __init__(self, content: str):
        self.content = content

    def invoke(self, _messages):
        return SimpleNamespace(content=self.content)

    def with_structured_output(self, _schema):
        return _FakeStructuredLLM("agent orchestration patterns")


def test_write_section_persists_structured_section_document(monkeypatch):
    """测试小节节点会输出可汇总的 section 与结构化来源数据"""
    monkeypatch.setattr(
        "app.ai.deep_research.nodes.get_llm",
        lambda: _FakeLLM("## Agent 架构视角\n### 摘要\n这里是带引用的结构化小节 [1]")
    )

    state = {
        "analyst": {
            "name": "A",
            "affiliation": "Org",
            "role": "Architect",
            "description": "关注 Agent 架构演进",
        },
        "context": ["[1] Doc\nURL: https://a.example.com\nSummary: snippet"],
        "sources": [
            {"url": "https://a.example.com", "title": "A"},
            {"url": "https://b.example.com", "title": "B"},
        ],
    }

    result = write_section(state)

    assert result["sections"][0].startswith("## Agent 架构视角")
    assert result["section_documents"][0]["title"] == "Agent 架构视角"
    assert result["section_documents"][0]["sources"][0]["url"] == "https://a.example.com"


def test_write_report_generates_main_body_heading(monkeypatch):
    """测试主体内容节点会生成明确的主体标题"""
    monkeypatch.setattr(
        "app.ai.deep_research.nodes.get_llm",
        lambda: _FakeLLM("## 主体内容\n### 核心发现\n这是主体内容。")
    )

    result = write_report(
        {
            "topic": "Agent",
            "sections": ["## 小节一\n内容", "## 小节二\n内容"],
        }
    )

    assert result["content"].startswith("## 主体内容")
    assert "### 核心发现" in result["content"]


def test_write_introduction_and_conclusion_keep_expected_headings(monkeypatch):
    """测试引言和结论节点保留明确中文标题"""
    outputs = iter([
        "# Agent 研究报告\n\n## 引言\n这是引言。",
        "## 结论\n这是结论。",
    ])

    monkeypatch.setattr(
        "app.ai.deep_research.nodes.get_llm",
        lambda: _FakeLLM(next(outputs))
    )

    intro = write_introduction({"topic": "Agent", "sections": ["## 小节\n内容"]})
    conclusion = write_conclusion({"topic": "Agent", "sections": ["## 小节\n内容"]})

    assert "# Agent 研究报告" in intro["introduction"]
    assert "## 引言" in intro["introduction"]
    assert conclusion["conclusion"].startswith("## 结论")
