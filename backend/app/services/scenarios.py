from datetime import datetime

from sqlalchemy.orm import Session

from app.models.global_event import GlobalEvent


def create_red_sea_simulation(
    db: Session,
) -> GlobalEvent:

    event = GlobalEvent(
        source="HEX_SIMULATION",
        external_id=(
            f"RED-SEA-{datetime.utcnow():%Y%m%d%H%M%S}"
        ),
        event_type="LOGISTICS",
        title=(
            "Simulated Red Sea shipping "
            "disruption"
        ),
        description=(
            "Hackathon scenario simulating "
            "a severe disruption to Red Sea "
            "maritime traffic."
        ),
        url=None,
        country=None,
        region="Red Sea",
        severity="HIGH",
        source_published_at=None,
        detected_at=datetime.utcnow(),
        raw_data={
            "simulation": True,
            "scenario": "RED_SEA_DISRUPTION",
        },
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event