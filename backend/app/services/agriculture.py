from sqlalchemy.orm import Session

from app.models.agriculture_signal import (
    AgricultureSignal,
)


def get_agriculture_risks(
    db: Session,
    region: str | None = None,
) -> list[dict]:

    query = db.query(
        AgricultureSignal
    )

    if region:
        query = query.filter(
            AgricultureSignal.region
            == region
        )

    signals = (
        query
        .order_by(
            AgricultureSignal.observed_at.desc()
        )
        .all()
    )

    return [
        {
            "id": signal.id,
            "region": signal.region,
            "crop": signal.crop,
            "signal_type": signal.signal_type,
            "value": float(
                signal.signal_value
            ),
            "unit": signal.unit,
            "severity": signal.severity,
            "source": signal.source,
            "observed_at": (
                signal.observed_at
            ),
        }
        for signal in signals
    ]