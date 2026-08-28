from datetime import datetime

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    source_type: str = Field(examples=["file_upload", "sql"])
    display_name: str
    config: dict = Field(default_factory=dict)
    # Secrets — encrypted at rest, never echoed back.
    credentials: dict = Field(default_factory=dict)


class ConnectionUpdate(BaseModel):
    display_name: str | None = None
    config: dict | None = None
    credentials: dict | None = None
    status: str | None = None


class ConnectionOut(BaseModel):
    id: int
    organization_id: int
    source_type: str
    display_name: str
    status: str
    config: dict
    cursor: dict
    has_credentials: bool
    last_sync_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class TestResult(BaseModel):
    ok: bool
    message: str


class SyncResult(BaseModel):
    connection_id: int
    duration_ms: int
    entities: dict
    rows_written: int
    errors: list[str]
    status: str


class ReadinessDomain(BaseModel):
    domain: str
    status: str  # READY | PARTIAL | MISSING
    detail: str
    row_count: int
    synced_row_count: int
    last_synced_at: datetime | None
    sources: list[str]


class ReadinessOut(BaseModel):
    organization_id: int
    overall: str
    domains: list[ReadinessDomain]
