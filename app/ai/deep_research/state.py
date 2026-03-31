"""Deep Research 状态定义"""
import operator
from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class Analyst(TypedDict):
    """分析师数据模型"""
    name: str
    affiliation: str
    role: str
    description: str


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
    analyst: Analyst
    interview: str
    sections: list


class ResearchGraphState(TypedDict):
    """主图状态"""
    topic: str
    max_analysts: int
    human_analyst_feedback: Optional[str]
    analysts: List[Analyst]
    sections: Annotated[list, operator.add]
    introduction: str
    content: str
    conclusion: str
    final_report: str
