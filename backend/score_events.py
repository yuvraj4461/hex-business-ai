from app.database.connection import SessionLocal
from app.models.global_event import GlobalEvent
from app.services.event_scoring import (
    calculate_severity,
)


db = SessionLocal()

try:

    events = (
        db.query(GlobalEvent)
        .filter(
            GlobalEvent.source == "GDELT"
        )
        .all()
    )

    updated = 0

    for event in events:

        event.severity = calculate_severity(
            event.title,
            event.event_type,
        )

        updated += 1

    db.commit()

    print(
        f"Updated severity for {updated} events."
    )

finally:
    db.close()