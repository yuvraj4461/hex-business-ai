from pprint import pprint

from app.database.connection import (
    SessionLocal,
)

from app.models.global_event import (
    GlobalEvent,
)

from app.services.global_exposure import (
    analyze_global_event_exposure,
)


db = SessionLocal()

try:

    event = (
        db.query(GlobalEvent)
        .filter(
            GlobalEvent.source
            == "HEX_SIMULATION"
        )
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .first()
    )

    if not event:

        print(
            "No simulated global event found."
        )

        print(
            "Run test_red_sea.py first."
        )

    else:

        result = (
            analyze_global_event_exposure(
                db,
                organization_id=10,
                event=event,
            )
        )

        print(
            "Exposure count:",
            len(result),
        )

        pprint(result)

finally:

    db.close()