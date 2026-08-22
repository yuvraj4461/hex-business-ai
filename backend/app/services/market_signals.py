from datetime import datetime

from sqlalchemy.orm import Session

from app.models.market_signal import MarketSignal


def store_fx_history(
    db: Session,
    history: list[dict],
) -> int:

    stored = 0

    for item in history:

        observed_at = datetime.fromisoformat(
            item["date"]
        )

        existing = (
            db.query(MarketSignal)
            .filter(
                MarketSignal.signal_type
                == "FX",
                MarketSignal.symbol
                == f'{item["base"]}/{item["quote"]}',
                MarketSignal.observed_at
                == observed_at,
            )
            .first()
        )

        if existing:
            continue

        signal = MarketSignal(
            signal_type="FX",
            symbol=(
                f'{item["base"]}/'
                f'{item["quote"]}'
            ),
            name=(
                f'{item["base"]} to '
                f'{item["quote"]}'
            ),
            source="FRANKFURTER",
            observed_at=observed_at,
            value=float(item["rate"]),
            unit="exchange_rate",
            base_currency=item["base"],
            quote_currency=item["quote"],
            metadata_json={
                "provider_data": item,
            },
        )

        db.add(signal)
        stored += 1

    db.commit()

    return stored

def analyze_fx_movement(
    db: Session,
    symbol: str,
) -> dict:

    signals = (
        db.query(MarketSignal)
        .filter(
            MarketSignal.signal_type == "FX",
            MarketSignal.symbol == symbol,
        )
        .order_by(
            MarketSignal.observed_at.asc()
        )
        .all()
    )

    if len(signals) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": (
                "At least two FX observations "
                "are required."
            ),
        }

    previous = float(
        signals[-2].value
    )

    latest = float(
        signals[-1].value
    )

    difference = latest - previous

    percentage_change = (
        (difference / previous) * 100
        if previous != 0
        else 0
    )

    if percentage_change > 0:
        direction = "INCREASED"
    elif percentage_change < 0:
        direction = "DECREASED"
    else:
        direction = "UNCHANGED"

    return {
        "status": "OK",
        "symbol": symbol,
        "previous_value": previous,
        "latest_value": latest,
        "difference": difference,
        "percentage_change": percentage_change,
        "direction": direction,
        "previous_date": (
            signals[-2].observed_at.isoformat()
        ),
        "latest_date": (
            signals[-1].observed_at.isoformat()
        ),
    }