"""GDELT collector — real-time global events (war, sanctions, disasters, ports).

Uses the GDELT DOC 2.0 article API (faster + more reliable than the v1
gkg_geojson endpoint). Best-effort: GDELT is slow and occasionally
unreachable, so a failure here never blocks the rest of World Watch —
the Tavily web-search collector also covers disruption news.
"""

from __future__ import annotations

import logging
from datetime import datetime

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.global_event import GlobalEvent
from app.services.event_scoring import calculate_severity

logger = logging.getLogger(__name__)

DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
QUERY = (
    "(war OR sanctions OR tariff OR blockade OR embargo OR "
    '"port strike" OR "supply chain" OR earthquake OR flood OR cyclone OR '
    '"shipping disruption" OR "trade restriction")'
)


def _classify(title: str) -> str:
    t = (title or "").lower()
    if any(w in t for w in ("earthquake", "flood", "cyclone", "hurricane", "storm", "wildfire")):
        return "NATURAL_DISASTER"
    if any(w in t for w in ("tariff", "sanction", "embargo", "trade restriction")):
        return "TRADE"
    if any(w in t for w in ("war", "conflict", "missile", "invasion", "military")):
        return "GEOPOLITICAL"
    if any(w in t for w in ("port", "strike", "blockade", "shipping", "freight", "container")):
        return "LOGISTICS"
    return "GENERAL"


def _parse_seendate(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ")
    except ValueError:
        return datetime.utcnow()


def collect_gdelt(db: Session, timespan: str = "3h") -> dict:
    try:
        resp = requests.get(
            DOC_URL,
            params={
                "query": QUERY,
                "mode": "artlist",
                "format": "json",
                "maxrecords": 50,
                "timespan": timespan,
                "sort": "datedesc",
            },
            timeout=45,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("GDELT fetch failed: %s", exc)
        return {"fetched": 0, "stored": 0, "error": str(exc)[:200]}

    seen_urls = {
        u
        for (u,) in db.execute(
            select(GlobalEvent.url).where(GlobalEvent.source == "GDELT")
        ).all()
        if u
    }

    stored = 0
    for art in articles:
        url = art.get("url")
        if not url or url in seen_urls:
            continue
        title = (art.get("title") or "Untitled").strip()
        event_type = _classify(title)
        # Skip unclassified articles — GDELT's broad query pulls a lot
        # of tangential coverage. We only want real incidents.
        if event_type == "GENERAL":
            continue
        db.add(
            GlobalEvent(
                source="GDELT",
                external_id=None,
                event_type=event_type,
                title=title[:500],
                description=None,
                url=url,
                country=art.get("sourcecountry") or None,
                region=None,
                severity=calculate_severity(title, event_type),
                detected_at=_parse_seendate(art.get("seendate")),
                raw_data={
                    "domain": art.get("domain"),
                    "language": art.get("language"),
                },
            )
        )
        seen_urls.add(url)
        stored += 1

    db.commit()
    return {"fetched": len(articles), "stored": stored}
