from pprint import pprint

from app.database.connection import (
    SessionLocal,
)

from app.models.global_event import (
    GlobalEvent,
)

from app.ai.context_builder import (
    build_ai_context,
)


db = SessionLocal()

try:

    event = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .first()
    )

    context = build_ai_context(
        db=db,
        organization_id=10,
        event=event,
    )

    pprint(context)

finally:
    db.close()