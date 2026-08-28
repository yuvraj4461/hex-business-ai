"""FX collector — key currency pairs vs INR, flags sharp moves."""

from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.market_signal import MarketSignal
from app.services.fx import get_multiple_rates
from app.services.market_signals import analyze_fx_movement, store_fx_history

logger = logging.getLogger(__name__)

BASES = ["USD", "EUR", "CNY"]
QUOTE = "INR"
SHOCK_PCT = 2.0


def collect_fx(db: Session) -> dict:
    stored = 0
    shocks: list[dict] = []
    today = date.today().isoformat()

    for base in BASES:
        try:
            # frankfurter v2 /rates returns [{date, base, quote, rate}] —
            # exactly the shape store_fx_history wants.
            rows = get_multiple_rates(base, [QUOTE])
        except Exception as exc:  # noqa: BLE001
            logger.warning("FX fetch failed for %s: %s", base, exc)
            continue

        if not isinstance(rows, list) or not rows:
            continue

        for row in rows:
            row.setdefault("date", today)
        stored += store_fx_history(db, rows)

        move = analyze_fx_movement(db, f"{base}/{QUOTE}")
        if (
            move.get("status") == "OK"
            and abs(move.get("percentage_change", 0)) >= SHOCK_PCT
        ):
            pct = round(move["percentage_change"], 2)
            shocks.append(
                {
                    "symbol": f"{base}/{QUOTE}",
                    "percentage_change": pct,
                    "direction": move["direction"],
                }
            )
            # Marker signal the World Watch agent / feed can pick up.
            db.add(
                MarketSignal(
                    signal_type="FX_SHOCK",
                    symbol=f"{base}/{QUOTE}",
                    name=f"{base}/{QUOTE} moved {pct:+.2f}%",
                    source="FRANKFURTER",
                    observed_at=datetime.utcnow(),
                    value=pct,
                    unit="percent_change",
                    base_currency=base,
                    quote_currency=QUOTE,
                    metadata_json=move,
                )
            )
    db.commit()

    return {"stored": stored, "shocks": shocks}
