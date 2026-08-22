from datetime import datetime

from pydantic import BaseModel


class GlobalEventResponse(BaseModel):

    id: int

    source: str

    external_id: str | None

    event_type: str

    title: str

    description: str | None

    url: str | None

    country: str | None

    region: str | None

    severity: str

    source_published_at: datetime | None

    detected_at: datetime

    raw_data: dict | None

    class Config:
        from_attributes = True