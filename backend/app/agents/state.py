from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    question: str

    organization_id: int

    business_data: dict[str, Any]

    findings: list[dict[str, Any]]

    recommendations: list[dict[str, Any]]

    errors: list[str]

    final_answer: str