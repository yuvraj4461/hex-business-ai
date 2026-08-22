from app.database.connection import SessionLocal
from app.services.fx import (
    get_monthly_fx_history,
)
from app.services.market_signals import (
    store_fx_history,
)


db = SessionLocal()

try:

    history = get_monthly_fx_history(
        "USD",
        "INR",
        months=12,
    )

    stored = store_fx_history(
        db,
        history,
    )

    print(
        "Stored FX signals:",
        stored,
    )

finally:
    db.close()
    