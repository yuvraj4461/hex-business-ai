from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DataQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    prior_spec: dict[str, Any] | None = None


class DataAnswer(BaseModel):
    question: str
    answer: str
    spec: dict[str, Any] | None = None
    spec_label: str = ""
    result: dict[str, Any]
    degraded: bool = False


class ThreadMessage(BaseModel):
    id: int
    role: str
    question: str | None = None
    answer: str | None = None
    spec: dict[str, Any] | None = None
    spec_label: str | None = None
    result: dict[str, Any] | None = None
    degraded: bool = False
    created_at: datetime | None = None


class ThreadSummary(BaseModel):
    id: int
    title: str
    message_count: int
    updated_at: datetime | None = None


class ThreadDetail(BaseModel):
    id: int
    title: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[ThreadMessage] = []
