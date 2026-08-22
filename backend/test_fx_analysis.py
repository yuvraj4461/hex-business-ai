from pprint import pprint

from app.database.connection import SessionLocal
from app.services.market_signals import (
    analyze_fx_movement,
)


db = SessionLocal()

try:

    result = analyze_fx_movement(
        db,
        "USD/INR",
    )

    pprint(result)

finally:
    db.close()