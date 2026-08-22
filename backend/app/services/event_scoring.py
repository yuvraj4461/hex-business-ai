from datetime import datetime, timezone


HIGH_RISK_TERMS = [
    "war",
    "attack",
    "blockade",
    "sanction",
    "missile",
    "invasion",
    "closure",
    "earthquake",
    "cyclone",
    "hurricane",
    "tsunami",
]

MEDIUM_RISK_TERMS = [
    "conflict",
    "tariff",
    "strike",
    "port",
    "shipping",
    "flood",
    "storm",
    "protest",
    "border",
]


def calculate_severity(
    title: str,
    event_type: str,
) -> str:

    text = (
        f"{title} {event_type}"
    ).lower()

    high_matches = sum(
        1
        for term in HIGH_RISK_TERMS
        if term in text
    )

    medium_matches = sum(
        1
        for term in MEDIUM_RISK_TERMS
        if term in text
    )

    if high_matches >= 2:
        return "CRITICAL"

    if high_matches == 1:
        return "HIGH"

    if medium_matches >= 2:
        return "MEDIUM"

    if medium_matches == 1:
        return "LOW"

    return "INFO"


def freshness_score(
    detected_at: datetime,
) -> str:

    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(
            tzinfo=timezone.utc
        )

    now = datetime.now(timezone.utc)

    age_minutes = (
        now - detected_at
    ).total_seconds() / 60

    if age_minutes <= 30:
        return "VERY_FRESH"

    if age_minutes <= 120:
        return "FRESH"

    if age_minutes <= 360:
        return "RECENT"

    return "STALE"