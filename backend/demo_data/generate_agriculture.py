from datetime import datetime, timedelta

from app.database.connection import SessionLocal
from app.models.agriculture_signal import (
    AgricultureSignal,
)


SIGNALS = [
    {
        "region": "Punjab, India",
        "crop": "Wheat",
        "signal_type": "DROUGHT_RISK",
        "signal_value": 72,
        "unit": "risk_score",
        "severity": "HIGH",
    },
    {
        "region": "Punjab, India",
        "crop": "Wheat",
        "signal_type": "YIELD_OUTLOOK",
        "signal_value": -14,
        "unit": "percent_change",
        "severity": "HIGH",
    },
    {
        "region": "India",
        "crop": "Rice",
        "signal_type": "DEMAND_OUTLOOK",
        "signal_value": 18,
        "unit": "percent_change",
        "severity": "MEDIUM",
    },
    {
        "region": "Maharashtra, India",
        "crop": "Sugar",
        "signal_type": "WEATHER_RISK",
        "signal_value": 58,
        "unit": "risk_score",
        "severity": "MEDIUM",
    },
]


db = SessionLocal()

try:

    created = 0

    for signal in SIGNALS:

        existing = (
            db.query(AgricultureSignal)
            .filter(
                AgricultureSignal.region
                == signal["region"],
                AgricultureSignal.crop
                == signal["crop"],
                AgricultureSignal.signal_type
                == signal["signal_type"],
            )
            .first()
        )

        if existing:
            continue

        db.add(
            AgricultureSignal(
                **signal,
                source="HEX_SIMULATION",
                observed_at=(
                    datetime.utcnow()
                ),
            )
        )

        created += 1

    db.commit()

    print(
        f"Created {created} agriculture signals."
    )

finally:
    db.close()