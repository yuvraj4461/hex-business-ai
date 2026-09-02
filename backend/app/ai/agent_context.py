import logging

from app.ai.context_builder import (
    build_ai_context,
)

logger = logging.getLogger(__name__)


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


def resolve_context(state: dict, db, organization_id: int, event=None) -> dict:
    """Return the run-scoped context if the runner seeded it, otherwise
    build it. Avoids rebuilding the same market/exposure/agriculture
    context in every agent."""

    cached = state.get("shared_context")
    if isinstance(cached, dict) and cached:
        return cached

    return build_ai_context(
        db=db, organization_id=organization_id, event=event
    )
