from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models.global_event import GlobalEvent


GDELT_URL = (
    "https://api.gdeltproject.org/api/v1/"
    "gkg_geojson"
)


GDELT_QUERY = (
    "(geopolitical OR conflict OR war OR "
    "sanctions OR tariff OR blockade OR "
    "shipping OR port OR earthquake OR flood)"
)


def fetch_gdelt_events(
    timespan_minutes: int = 60,
) -> dict:

    params = {
        "QUERY": GDELT_QUERY,
        "TIMESPAN": str(timespan_minutes),
        "OUTPUTFIELDS": (
            "url,name,domain,geores,lang,tone,"
            "themes,names"
        ),
        "MAXROWS": "100",
    }

    response = httpx.get(
        GDELT_URL,
        params=params,
        timeout=30.0,
    )

    response.raise_for_status()

    # GDELT can occasionally return malformed
    # or non-standard UTF-8 bytes. Decode explicitly
    # so one problematic character does not crash
    # the entire ingestion pipeline.
    text = response.content.decode(
        "utf-8",
        errors="replace",
    )

    import json

    return json.loads(text)


def classify_gdelt_event(
    feature: dict,
) -> str:

    properties = feature.get(
        "properties",
        {},
    )

    text = (
        str(
            properties.get("name", "")
        )
        .lower()
    )

    if any(
        word in text
        for word in [
            "earthquake",
            "flood",
            "cyclone",
            "hurricane",
            "storm",
        ]
    ):
        return "NATURAL_DISASTER"

    if any(
        word in text
        for word in [
            "tariff",
            "sanction",
            "trade",
        ]
    ):
        return "TRADE"

    if any(
        word in text
        for word in [
            "war",
            "conflict",
            "geopolitical",
        ]
    ):
        return "GEOPOLITICAL"

    if any(
        word in text
        for word in [
            "shipping",
            "port",
            "blockade",
        ]
    ):
        return "LOGISTICS"

    return "GENERAL"


def store_gdelt_events(
    db: Session,
    data: dict,
) -> int:

    features = data.get(
        "features",
        [],
    )

    stored = 0

    for feature in features:

        properties = feature.get(
            "properties",
            {},
        )

        url = properties.get("url")

        title = properties.get(
            "name",
            "Untitled event",
        )

        event_type = classify_gdelt_event(
            feature
        )

        existing = None

        if url:
            existing = (
                db.query(GlobalEvent)
                .filter(
                    GlobalEvent.url == url,
                )
                .first()
            )

        if existing:
            continue

        event = GlobalEvent(
            source="GDELT",
            external_id=None,
            event_type=event_type,
            title=title[:500],
            description=None,
            url=url,
            country=None,
            region=properties.get(
                "geores"
            ),
            severity="UNKNOWN",
            source_published_at=None,
            detected_at=datetime.utcnow(),
            raw_data=properties,
        )

        db.add(event)

        stored += 1

    db.commit()

    return stored