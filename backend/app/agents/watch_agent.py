"""World Watch Agent — analyses the intelligence the cron collector gathers.

Reads recent global events + market signals (it does not fetch — the
`app/intelligence` watcher owns collection) and turns them into findings
and recommendations the Risk Agent then folds into the exposure picture.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.global_event import GlobalEvent
from app.models.market_signal import MarketSignal
from app.models.supply_route import SupplyRoute
from app.services import geo_exposure

_HIGH = ("HIGH", "CRITICAL")
_WINDOW_HOURS = 48


def watch_agent(state: dict, db: Session) -> dict:
    organization_id = state["organization_id"]
    findings = list(state.get("findings") or [])
    recommendations = list(state.get("recommendations") or [])

    cutoff = datetime.utcnow() - timedelta(hours=_WINDOW_HOURS)

    events = db.execute(
        select(GlobalEvent)
        .where(
            GlobalEvent.detected_at >= cutoff,
            GlobalEvent.source.in_(("GDELT", "WEB_SEARCH", "HEX_SIMULATION")),
        )
        .order_by(desc(GlobalEvent.detected_at))
        .limit(60)
    ).scalars().all()

    high_events = [e for e in events if (e.severity or "").upper() in _HIGH]

    fx_shocks = db.execute(
        select(MarketSignal)
        .where(
            MarketSignal.signal_type == "FX_SHOCK",
            MarketSignal.observed_at >= cutoff,
        )
        .order_by(desc(MarketSignal.observed_at))
        .limit(10)
    ).scalars().all()

    routes = db.execute(
        select(SupplyRoute).where(
            SupplyRoute.organization_id == organization_id,
            SupplyRoute.status == "ACTIVE",
        )
    ).scalars().all()

    # Which recent HIGH events actually touch one of this org's lanes?
    matched: list[dict] = []
    for event in high_events:
        for route in routes:
            hit, reason = geo_exposure.event_affects(
                event,
                corridor=route.corridor,
                origin_country=route.origin_country,
                destination_country=route.destination_country,
            )
            if hit:
                matched.append(
                    {
                        "event_id": event.id,
                        "title": event.title,
                        "event_type": event.event_type,
                        "severity": event.severity,
                        "reason": reason,
                    }
                )
                break

    by_type: dict[str, int] = {}
    for e in events:
        by_type[e.event_type or "GENERAL"] = (
            by_type.get(e.event_type or "GENERAL", 0) + 1
        )

    findings.append(
        {
            "agent": "World Watch Agent",
            "type": "world_watch",
            "data": {
                "window_hours": _WINDOW_HOURS,
                "events_seen": len(events),
                "high_severity": len(high_events),
                "affecting_your_lanes": len(matched),
                "by_type": by_type,
                "top_headlines": [e.title for e in events[:5]],
            },
        }
    )

    for m in matched[:8]:
        recommendations.append(
            {
                "agent": "World Watch Agent",
                "type": "active_disruption",
                "reason": (
                    f"{m['severity']} event on one of your corridors: "
                    f"{m['reason']}"
                ),
                "event": m["title"],
                "severity": m["severity"],
            }
        )

    price_events = [
        e
        for e in events
        if e.event_type in ("PRICE_SHOCK", "TRADE", "ECONOMIC", "LOGISTICS")
    ]
    if price_events or fx_shocks:
        recommendations.append(
            {
                "agent": "World Watch Agent",
                "type": "price_shock",
                "reason": (
                    "Recent freight / tariff / commodity / FX moves may lift "
                    "landed cost — review supplier pricing and contracts."
                ),
                "signals": [e.title for e in price_events[:4]]
                + [
                    f"{s.symbol} {float(s.value):+.2f}% "
                    for s in fx_shocks[:3]
                ],
            }
        )

    return {
        **state,
        "findings": findings,
        "recommendations": recommendations,
    }
