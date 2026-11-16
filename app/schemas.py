from pydantic import BaseModel, Field
from typing import Any

class QueryRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)

class Citation(BaseModel):
    source: str
    supplier: str
    clause: str
    chunk_id: str
    score: float | None = None
    excerpt: str | None = None

class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    scores: dict[str, Any]
    filters_applied: dict[str, Any] = {}
    retrieved_chunks: int = 0
