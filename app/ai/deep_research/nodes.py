"""Deep Research 节点函数"""
from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, interrupt

from app.ai.deep_research.llm import get_llm
from app.ai.deep_research.progress import update_progress
from app.ai.deep_research.prompts import (
    analyst_instructions, question_instructions, answer_instructions,
    section_writer_instructions, report_writer_instructions,
    intro_conclusion_instructions, search_instructions
)
from app.ai.deep_research.tools.tavily import get_tavily_tool
from app.ai.deep_research.tools.bocha import BochaSearchTool


bocha_tool = BochaSearchTool()
MAX_SOURCES_PER_SECTION = 3
MAX_TOTAL_SOURCES = 8


# ===== Pydantic 模型 =====
class Analyst(BaseModel):
    """分析师数据模型"""
    affiliation: str = Field(description="分析师的主要隶属机构或组织")
    name: str = Field(description="分析师姓名")
    role: str = Field(description="分析师在研究主题中的具体角色定位")
    description: str = Field(description="分析师的关注焦点、关切点和动机的详细描述")

    @property
    def persona(self) -> str:
        """生成分析师人设描述"""
        return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\n"


class Perspectives(BaseModel):
    """分析师集合数据模型"""
    analysts: List[Analyst] = Field(description="包含所有分析师角色和隶属机构的综合列表")


class SearchQuery(BaseModel):
    """搜索查询数据模型"""
    search_query: str = Field(None, description="用于检索的搜索查询语句")


def dedupe_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 URL 去重并保留首次出现顺序。"""
    deduped: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for source in sources or []:
        url = (source or {}).get("url", "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(source)

    return deduped


def _coerce_text(value: Any) -> str:
    """将任意值转为可安全拼接的字符串。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def normalize_tavily_results(raw_docs: Any, query: str) -> List[Dict[str, Any]]:
    """将 Tavily 返回结果标准化为统一来源结构。"""
    if isinstance(raw_docs, dict):
        results = raw_docs.get("results") or raw_docs.get("items") or []
    elif isinstance(raw_docs, list):
        results = raw_docs
    else:
        results = []

    normalized = []
    for item in results:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "source_type": "tavily",
            "query": query,
            "url": _coerce_text(item.get("url")),
            "title": _coerce_text(item.get("title") or item.get("name")),
            "snippet": _coerce_text(item.get("content") or item.get("snippet")),
            "site_name": _coerce_text(item.get("source") or item.get("site_name")),
        })

    return dedupe_sources(normalized)


def normalize_bocha_results(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """将 Bocha 返回结果标准化为统一来源结构。"""
    normalized = []
    for item in results or []:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "source_type": "bocha",
            "query": query,
            "url": _coerce_text(item.get("url")),
            "title": _coerce_text(item.get("name") or item.get("title")),
            "snippet": _coerce_text(item.get("snippet")),
            "site_name": _coerce_text(item.get("siteName") or item.get("site_name")),
        })

    return dedupe_sources(normalized)


def format_sources_for_context(sources: List[Dict[str, Any]]) -> str:
    """把结构化来源格式化成 LLM 可消费的上下文。"""
    blocks = []
    for idx, source in enumerate(dedupe_sources(sources), start=1):
        title = source.get("title") or "Untitled"
        url = source.get("url") or ""
        site_name = source.get("site_name") or source.get("source_type") or ""
        snippet = source.get("snippet") or ""
        blocks.append(
            f"[{idx}] {title}\nURL: {url}\nSite: {site_name}\nSummary: {snippet}"
        )
    return "\n\n".join(blocks)


def extract_section_title(section_content: str) -> str:
    """从 Markdown 小节中提取标题。"""
    for line in (section_content or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            return stripped[4:].strip()
        if stripped.startswith("## "):
            return stripped[3:].strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return "未命名小节"


def format_report_sources(section_documents: List[Dict[str, Any]]) -> str:
    """按小节组织最终 URL 引用区。"""
    if not section_documents:
        return ""

    lines = ["## 引用"]
    seen_urls: set[str] = set()
    total_kept = 0

    for section in section_documents:
        title = _coerce_text((section or {}).get("title")) or "未命名小节"
        section_sources = []
        for source in (section or {}).get("sources", []):
            url = _coerce_text((source or {}).get("url"))
            if not url or url in seen_urls:
                continue
            if len(section_sources) >= MAX_SOURCES_PER_SECTION:
                continue
            if total_kept >= MAX_TOTAL_SOURCES:
                break
            seen_urls.add(url)
            section_sources.append(source)
            total_kept += 1

        if not section_sources:
            continue

        lines.append(f"### {title}")
        for idx, source in enumerate(section_sources, start=1):
            label = _coerce_text(source.get("title")) or _coerce_text(source.get("site_name")) or source.get("url")
            lines.append(f"{idx}. {label}")
            lines.append(f"   URL: {source.get('url')}")

    if len(lines) == 1:
        return ""

    return "\n".join(lines)


def ensure_markdown_heading(content: str, heading: str) -> str:
    """确保内容以指定 Markdown 标题开头。"""
    stripped = (content or "").strip()
    if not stripped:
        return heading
    if stripped.startswith(heading):
        return stripped
    return f"{heading}\n{stripped}"


def ensure_introduction_shape(content: str, topic: str) -> str:
    """确保引言包含总标题与单个引言标题，避免重复。"""
    stripped = (content or "").strip()
    if not stripped:
        return f"# {topic} 研究报告\n\n## 引言"

    lines = [line.rstrip() for line in stripped.splitlines()]
    title_line = f"# {topic} 研究报告"
    has_title = any(line.strip().startswith("# ") for line in lines)
    has_intro_heading = any(line.strip() == "## 引言" for line in lines)

    if not has_title:
        lines.insert(0, title_line)

    if not has_intro_heading:
        insert_at = 1 if lines and lines[0].startswith("# ") else 0
        lines.insert(insert_at, "")
        lines.insert(insert_at + 1, "## 引言")

    seen_intro = False
    normalized_lines: List[str] = []
    for line in lines:
        if line.strip() == "## 引言":
            if seen_intro:
                continue
            seen_intro = True
        normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def ensure_main_body_heading(content: str) -> str:
    """确保主体内容使用统一标题。"""
    stripped = (content or "").strip()
    if not stripped:
        return "## 主体内容"
    if stripped.startswith("## Insights"):
        stripped = stripped[len("## Insights"):].strip()
    if stripped.startswith("## 主体内容"):
        return stripped
    return f"## 主体内容\n{stripped}"


def _report_progress(config: RunnableConfig | None, stage: str, message: str) -> None:
    """在节点运行时上报当前阶段。"""
    thread_id = ((config or {}).get("configurable") or {}).get("thread_id")
    if thread_id:
        update_progress(thread_id, stage, message)


# ===== 节点函数 =====
def create_analysts(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """创建分析师团队"""
    _report_progress(config, "creating_analysts", "正在生成分析师")
    topic = state["topic"]
    max_analysts = state["max_analysts"]
    human_feedback = state.get("human_analyst_feedback", "")

    system_msg = analyst_instructions.format(
        topic=topic,
        human_analyst_feedback=human_feedback,
        max_analysts=max_analysts
    )

    structured_llm = get_llm().with_structured_output(Perspectives)

    try:
        result = structured_llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content="生成分析师集合。")
        ])
        if result is None or not hasattr(result, 'analysts') or result.analysts is None:
            analysts = []
        else:
            analysts = result.analysts
    except Exception as e:
        print(f"[ERROR] create_analysts failed: {e}")
        analysts = []

    # 转换为字典以兼容checkpoint序列化
    return {"analysts": [a.model_dump() if hasattr(a, 'model_dump') else a for a in analysts]}


def human_feedback(state: Dict[str, Any], config: RunnableConfig | None = None) -> Command[Literal["create_analysts", "dispatch_interviews"]]:
    """在分析师生成后暂停，等待用户确认或要求重新生成"""
    _report_progress(config, "awaiting_feedback", "请确认分析师或提供新的自然语言要求")
    response = interrupt(
        {
            "type": "analyst_review",
            "topic": state["topic"],
            "max_analysts": state["max_analysts"],
            "analysts": state.get("analysts", []),
        }
    )

    action = (response or {}).get("action", "approve")
    if action == "regenerate":
        feedback = (response or {}).get("feedback", "")
        return Command(
            update={"human_analyst_feedback": feedback},
            goto="create_analysts",
        )

    return Command(
        update={"human_analyst_feedback": None},
        goto="dispatch_interviews",
    )


def generate_question(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """生成访谈问题"""
    _report_progress(config, "interviewing", "正在分析师讨论中")
    analyst = state["analyst"]
    messages = state["messages"]

    # 构建人设描述
    persona = f"Name: {analyst['name']}\nRole: {analyst['role']}\nAffiliation: {analyst['affiliation']}\nDescription: {analyst['description']}"

    system_msg = question_instructions.format(goals=persona)
    try:
        question = get_llm().invoke([SystemMessage(content=system_msg)] + messages)
    except Exception as e:
        print(f"[ERROR] generate_question failed: {e}")
        question = AIMessage(content="抱歉，我无法生成问题。")

    return {"messages": [question]}


def search_web(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Tavily Web搜索"""
    _report_progress(config, "searching", "正在并行检索 Tavily 和 Bocha")
    messages = state["messages"]

    try:
        structured_llm = get_llm().with_structured_output(SearchQuery)
        search_query = structured_llm.invoke([SystemMessage(content=search_instructions)] + messages)
        query_str = getattr(search_query, 'search_query', None) or ""
    except Exception as e:
        print(f"[ERROR] search_web LLM failed: {e}")
        query_str = ""

    try:
        docs = get_tavily_tool().invoke(query_str)
        sources = normalize_tavily_results(docs, query_str)
    except Exception as e:
        print(f"[ERROR] search_web tavily failed: {e}")
        sources = []

    formatted = format_sources_for_context(sources)

    return {"context": [formatted] if formatted else [], "sources": sources}


def search_bocha(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Bocha Web搜索"""
    _report_progress(config, "searching", "正在并行检索 Tavily 和 Bocha")
    messages = state["messages"]

    try:
        structured_llm = get_llm().with_structured_output(SearchQuery)
        search_query = structured_llm.invoke([SystemMessage(content=search_instructions)] + messages)
        query_str = getattr(search_query, 'search_query', None) or ""
    except Exception as e:
        print(f"[ERROR] search_bocha LLM failed: {e}")
        query_str = ""

    try:
        docs = bocha_tool._search(query=query_str, count=10)
        sources = normalize_bocha_results(docs, query_str)
    except Exception as e:
        print(f"[ERROR] search_bocha failed: {e}")
        sources = []

    formatted = format_sources_for_context(sources)

    return {"context": [formatted] if formatted else [], "sources": sources}


def generate_answer(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """生成专家回答"""
    _report_progress(config, "interviewing", "正在分析师讨论中")
    analyst = state["analyst"]
    messages = state["messages"]
    context = state.get("context", [])

    persona = f"Name: {analyst['name']}\nRole: {analyst['role']}\nAffiliation: {analyst['affiliation']}\nDescription: {analyst['description']}"

    system_msg = answer_instructions.format(
        goals=persona,
        context="\n".join(context)
    )

    try:
        answer = get_llm().invoke([SystemMessage(content=system_msg)] + messages)
        answer.name = "expert"
    except Exception as e:
        print(f"[ERROR] generate_answer failed: {e}")
        answer = AIMessage(content="抱歉，我无法生成回答。", name="expert")

    return {"messages": [answer]}


def route_messages(state: Dict[str, Any]) -> str:
    """路由函数"""
    messages = state["messages"]
    max_num_turns = state.get("max_num_turns", 3)

    num_responses = len([
        m for m in messages
        if isinstance(m, AIMessage) and m.name == "expert"
    ])

    if num_responses >= max_num_turns:
        return "save_interview"

    # Check if analyst ended the interview (check second-to-last message, which is the analyst's question)
    if len(messages) >= 2:
        last_question = messages[-2]
        if isinstance(last_question, HumanMessage) and "非常感谢您的帮助" in last_question.content:
            return "save_interview"

    return "ask_question"


def save_interview(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """保存访谈"""
    _report_progress(config, "writing_sections", "正在整理访谈并撰写小节")
    messages = state["messages"]
    interview = get_buffer_string(messages)
    return {"interview": interview}


def write_section(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """撰写报告小节"""
    _report_progress(config, "writing_sections", "正在整理访谈并撰写小节")
    analyst = state["analyst"]
    context = state.get("context", [])
    sources = dedupe_sources(state.get("sources", []))

    system_msg = section_writer_instructions.format(focus=analyst["description"])

    try:
        section = get_llm().invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=f"使用这些来源撰写你的小节:\n\n{chr(10).join(context)}")
        ])
    except Exception as e:
        print(f"[ERROR] write_section failed: {e}")
        section = type('obj', (object,), {'content': ''})()

    section_content = section.content.strip()
    if not section_content.startswith("## "):
        section_title = analyst["description"][:28] or "研究小节"
        section_content = f"## {section_title}\n{section_content}"
    section_document = {
        "title": extract_section_title(section_content),
        "content": section_content,
        "sources": sources,
    }

    return {
        "sections": [section_content],
        "section_documents": [section_document],
    }


def write_report(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """撰写报告主体"""
    _report_progress(config, "writing_report", "正在撰写报告")
    sections = state.get("sections", [])
    topic = state.get("topic", "")

    formatted = "\n\n".join(sections)
    system_msg = report_writer_instructions.format(topic=topic, context=formatted)

    try:
        report = get_llm().invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content="基于这些备忘录撰写报告。")
        ])
    except Exception as e:
        print(f"[ERROR] write_report failed: {e}")
        report = type('obj', (object,), {'content': ''})()

    return {"content": ensure_main_body_heading(report.content)}


def write_introduction(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """撰写引言"""
    _report_progress(config, "finalizing_report", "正在整合最终报告")
    sections = state.get("sections", [])
    topic = state.get("topic", "")

    formatted = "\n\n".join(sections)
    instructions = intro_conclusion_instructions.format(
        topic=topic,
        formatted_str_sections=formatted
    )

    try:
        intro = get_llm().invoke([
            SystemMessage(content=instructions),
            HumanMessage(content="撰写报告引言")
        ])
    except Exception as e:
        print(f"[ERROR] write_introduction failed: {e}")
        intro = type('obj', (object,), {'content': ''})()

    return {"introduction": ensure_introduction_shape(intro.content, topic)}


def write_conclusion(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """撰写结论"""
    _report_progress(config, "finalizing_report", "正在整合最终报告")
    sections = state.get("sections", [])
    topic = state.get("topic", "")

    formatted = "\n\n".join(sections)
    instructions = intro_conclusion_instructions.format(
        topic=topic,
        formatted_str_sections=formatted
    )

    try:
        conclusion = get_llm().invoke([
            SystemMessage(content=instructions),
            HumanMessage(content="撰写报告结论")
        ])
    except Exception as e:
        print(f"[ERROR] write_conclusion failed: {e}")
        conclusion = type('obj', (object,), {'content': ''})()

    return {"conclusion": ensure_markdown_heading(conclusion.content, "## 结论")}


def finalize_report(state: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
    """整合最终报告"""
    _report_progress(config, "finalizing_report", "正在整合最终报告")
    content = state.get("content", "")

    if "## Sources" in content:
        try:
            content, sources = content.split("\n## Sources\n")
        except:
            sources = None
    else:
        sources = None

    introduction = state.get("introduction", "")
    conclusion = state.get("conclusion", "")

    introduction = introduction.strip()
    content = ensure_main_body_heading(content)
    conclusion = ensure_markdown_heading(conclusion, "## 结论")

    final_report = "\n\n".join(
        part for part in [introduction, content, conclusion] if (part or "").strip()
    )

    structured_sources = format_report_sources(state.get("section_documents", []))

    if structured_sources:
        final_report += "\n\n" + structured_sources
    elif sources:
        final_report += "\n\n## Sources\n" + sources

    return {"final_report": final_report}
