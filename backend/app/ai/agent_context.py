from app.ai.context_builder import (
    build_ai_context,
)


def get_agent_context(
    db,
    organization_id: int,
    event=None,
) -> dict:

    return build_ai_context(
        db=db,
        organization_id=organization_id,
        event=event,
    )