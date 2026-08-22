from app.database.connection import SessionLocal

from app.services.global_events import (
    fetch_gdelt_events,
    store_gdelt_events,
)


db = SessionLocal()

try:

    print(
        "Fetching GDELT events..."
    )

    data = fetch_gdelt_events(
        timespan_minutes=60,
    )

    print(
        "Received:",
        len(
            data.get(
                "features",
                [],
            )
        ),
        "events",
    )

    stored = store_gdelt_events(
        db,
        data,
    )

    print(
        "Stored:",
        stored,
        "new events",
    )

finally:

    db.close()