from typing import Any

from pydantic import BaseModel, Field


class CopilotTurn(BaseModel):

    role: str  # "user" | "hex"

    content: str = Field(max_length=4000)


class CopilotRequest(BaseModel):

    question: str = Field(
        min_length=3,
        max_length=1000,
    )

    # Prior turns of this chat, oldest first. Lets HEX resolve
    # follow-ups ("why?", "what about last year?").
    history: list[CopilotTurn] = Field(
        default_factory=list,
        max_length=20,
    )


class CopilotSource(BaseModel):

    title: str

    url: str


class CopilotResponse(BaseModel):

    question: str

    answer: str

    data: dict[str, Any]

    sources: list[CopilotSource] = []