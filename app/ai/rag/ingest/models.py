"""
摄取流程统一数据结构
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IngestedAsset:
    asset_key: str
    asset_type: str
    page_idx: int | None
    asset_path: str
    caption: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestedDocument:
    source_path: str
    file_name: str
    file_type: str
    content: str
    loader_name: str
    page_start: int | None = None
    page_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    assets: list[IngestedAsset] = field(default_factory=list)


@dataclass
class IngestedChunk:
    chunk_id: str
    source_path: str
    file_type: str
    chunk_index: int
    content: str
    page_start: int | None = None
    page_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    related_asset_keys: list[str] = field(default_factory=list)
