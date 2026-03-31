"""Deep Research 状态定义"""
import operator
from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


def keep_latest(_current, new_value):
    """并行分支合流时保留最新的标量配置值。"""
    return new_value


class Analyst(TypedDict):
    """分析师数据模型"""
    name: str
    affiliation: str
    role: str
    description: str


class SourceItem(TypedDict, total=False):
    """结构化来源元信息"""
    source_type: str
    query: str
    url: str
    title: str
    snippet: str
    site_name: str


class SectionDocument(TypedDict, total=False):
    """按小节沉淀的报告与来源数据"""
    title: str
    content: str
    sources: List[SourceItem]


class GenerateAnalystsState(TypedDict):
    """分析师生成状态"""
    topic: str
    max_analysts: int
    human_analyst_feedback: Optional[str]
    analysts: List[Analyst]


class InterviewState(TypedDict):
    """访谈子图状态"""
    messages: Annotated[List[BaseMessage], operator.add]
    max_num_turns: int
    context: Annotated[list, operator.add]
    sources: Annotated[List[SourceItem], operator.add]
    analyst: Analyst
    interview: str
    sections: list
    section_documents: Annotated[List[SectionDocument], operator.add]


class ResearchGraphState(TypedDict):
    """主图状态"""
    topic: str
    max_analysts: int
    max_num_turns: Annotated[int, keep_latest]
    human_analyst_feedback: Optional[str]
    analysts: List[Analyst]
    sections: Annotated[list, operator.add]
    section_documents: Annotated[List[SectionDocument], operator.add]
    introduction: str
    content: str
    conclusion: str
    final_report: str
