"""Decide whether a global event touches a given route / shipment.

Replaces the hard-coded ``corridor == "RED_SEA"`` checks that used to live
in exposure_engine / route_optimizer. Matching is keyword-based against the
event's region, country and title, plus the corridor name and the two
endpoint countries of the lane.
"""

from __future__ import annotations

from app.models.global_event import GlobalEvent

# phrase (lower-case) -> corridors it disrupts, countries it disrupts,
# whether it is a chokepoint (amplifies delay).
CORRIDOR_KEYWORDS: dict[str, dict] = {
    "red sea": {"corridors": {"RED_SEA", "SUEZ"}, "countries": set(), "chokepoint": True},
    "suez": {"corridors": {"RED_SEA", "SUEZ"}, "countries": {"egypt"}, "chokepoint": True},
    "bab el-mandeb": {"corridors": {"RED_SEA"}, "countries": set(), "chokepoint": True},
    "bab-el-mandeb": {"corridors": {"RED_SEA"}, "countries": set(), "chokepoint": True},
    "gulf of aden": {"corridors": {"RED_SEA"}, "countries": {"yemen"}, "chokepoint": True},
    "houthi": {"corridors": {"RED_SEA"}, "countries": {"yemen"}, "chokepoint": True},
    "strait of hormuz": {"corridors": {"HORMUZ", "PERSIAN_GULF"}, "countries": {"iran", "uae", "qatar"}, "chokepoint": True},
    "persian gulf": {"corridors": {"HORMUZ", "PERSIAN_GULF"}, "countries": {"iran", "uae", "qatar", "saudi arabia"}, "chokepoint": True},
    "panama canal": {"corridors": {"PANAMA"}, "countries": {"panama"}, "chokepoint": True},
    "panama": {"corridors": {"PANAMA"}, "countries": {"panama"}, "chokepoint": True},
    "taiwan strait": {"corridors": {"SOUTH_CHINA_SEA", "TRANS_PACIFIC"}, "countries": {"taiwan", "china"}, "chokepoint": True},
    "south china sea": {"corridors": {"SOUTH_CHINA_SEA", "TRANS_PACIFIC"}, "countries": {"china", "vietnam", "philippines"}, "chokepoint": False},
    "strait of malacca": {"corridors": {"MALACCA", "TRANS_PACIFIC"}, "countries": {"singapore", "malaysia", "indonesia"}, "chokepoint": True},
    "malacca": {"corridors": {"MALACCA"}, "countries": {"singapore", "malaysia"}, "chokepoint": True},
    "black sea": {"corridors": {"BLACK_SEA"}, "countries": {"ukraine", "russia", "turkey", "romania"}, "chokepoint": False},
    "ukraine": {"corridors": {"BLACK_SEA"}, "countries": {"ukraine", "russia"}, "chokepoint": False},
    "russia": {"corridors": {"BLACK_SEA", "BALTIC"}, "countries": {"russia", "ukraine"}, "chokepoint": False},
    "bosphorus": {"corridors": {"BLACK_SEA"}, "countries": {"turkey"}, "chokepoint": True},
    "cape of good hope": {"corridors": {"CAPE_OF_GOOD_HOPE"}, "countries": {"south africa"}, "chokepoint": False},
    "gibraltar": {"corridors": {"MEDITERRANEAN"}, "countries": {"spain", "morocco"}, "chokepoint": True},
    "english channel": {"corridors": {"NORTH_EUROPE"}, "countries": {"france", "united kingdom"}, "chokepoint": False},
}

_SEVERITY_DELAY = {"HIGH": 14, "CRITICAL": 18, "MEDIUM": 7, "LOW": 2}

# Rough region buckets for lane -> corridor inference when a shipment has
# no explicit corridor / route.
_ASIA = {
    "china", "india", "vietnam", "bangladesh", "thailand", "indonesia",
    "malaysia", "singapore", "taiwan", "south korea", "japan", "pakistan",
    "sri lanka", "cambodia",
}
_EUROPE = {
    "netherlands", "germany", "belgium", "france", "united kingdom", "italy",
    "spain", "poland", "sweden", "denmark", "ireland", "portugal", "greece",
}
_MIDEAST = {"uae", "saudi arabia", "qatar", "kuwait", "oman", "bahrain", "iran"}
_US_EAST = {"united states", "usa", "canada"}


def infer_corridors(origin: str | None, destination: str | None) -> set[str]:
    o = (origin or "").strip().lower()
    d = (destination or "").strip().lower()
    if not o or not d:
        return set()

    pair = {o, d}
    # Asia/Mideast <-> Europe ocean freight transits Suez / Red Sea.
    if (pair & (_ASIA | _MIDEAST)) and (pair & _EUROPE):
        return {"RED_SEA", "SUEZ"}
    # Asia <-> US East Coast: Panama or a Suez all-water route.
    if (pair & _ASIA) and (pair & _US_EAST):
        return {"PANAMA", "TRANS_PACIFIC"}
    # Intra-Asia via the South China Sea / Malacca.
    if o in _ASIA and d in _ASIA:
        return {"SOUTH_CHINA_SEA", "MALACCA"}
    return set()


def _event_text(event: GlobalEvent) -> str:
    return " ".join(
        str(x or "")
        for x in (event.region, event.country, event.title)
    ).lower()


def matched_profiles(event: GlobalEvent) -> list[dict]:
    text = _event_text(event)
    return [
        profile
        for phrase, profile in CORRIDOR_KEYWORDS.items()
        if phrase in text
    ]


def event_affects(
    event: GlobalEvent,
    *,
    corridor: str | None = None,
    origin_country: str | None = None,
    destination_country: str | None = None,
) -> tuple[bool, str]:
    """Does this event disrupt a lane described by (corridor, endpoints)?"""

    corridor_u = (corridor or "").upper()
    endpoints = {
        (origin_country or "").strip().lower(),
        (destination_country or "").strip().lower(),
    }
    endpoints.discard("")

    lane_corridors = infer_corridors(origin_country, destination_country)
    candidate_corridors = {corridor_u} if corridor_u else set()
    candidate_corridors |= lane_corridors

    for profile in matched_profiles(event):
        overlap = candidate_corridors & profile["corridors"]
        if overlap:
            which = corridor_u if corridor_u in overlap else next(iter(overlap))
            return (
                True,
                f"{event.region or event.title}: {which} corridor",
            )
        if endpoints & profile["countries"]:
            hit = ", ".join(sorted(endpoints & profile["countries"]))
            return True, f"{event.region or event.title}: affects {hit}"

    # Direct country match against the event's own country field.
    ev_country = (event.country or "").strip().lower()
    if ev_country and ev_country in endpoints:
        return True, f"{event.title}: shipment endpoint in {event.country}"

    return False, ""


def disruption_delay_days(event: GlobalEvent, chokepoint: bool = False) -> int:
    base = _SEVERITY_DELAY.get((event.severity or "").upper(), 3)
    return int(round(base * 1.5)) if chokepoint else base


def is_chokepoint(event: GlobalEvent) -> bool:
    return any(p["chokepoint"] for p in matched_profiles(event))
