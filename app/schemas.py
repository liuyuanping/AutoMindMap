from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Block(BaseModel):
    id: str
    doc_path: str
    chapter_index: int
    section_index: int
    title: str
    content: str
    start_line: int
    end_line: int
    level: int
    parent_id: Optional[str] = None


class Relation(BaseModel):
    source: str
    target: str
    score: float


class GraphMetadata(BaseModel):
    created_at: str
    doc_count: int
    block_count: int


class GraphData(BaseModel):
    nodes: list
    edges: list
    metadata: GraphMetadata


class AnalyzeRequest(BaseModel):
    dir_path: str
    threshold: float = 0.3


class SaveRequest(BaseModel):
    graph: dict
    filename: str