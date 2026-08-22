from app.database.connection import (
    SessionLocal,
)

from app.models.global_event import (
    GlobalEvent,
)

from app.ai.context_builder import (
    build_ai_context,
)

from app.ai.business_analyst import (
    ask_business_ai,
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

    answer = ask_business_ai(
        question=(
            "What is the most important "
            "business risk right now?"
        ),
        context=context,
    )

    print(
        "\nHEX AI ANSWER:\n"
    )

    print(answer)

finally:
    db.close()