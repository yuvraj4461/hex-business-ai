from typing import Any

from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):

    question: str = Field(
        min_length=3,
        max_length=1000,
    )


class CopilotResponse(BaseModel):

    question: str

    answer: str

    data: dict[str, Any]