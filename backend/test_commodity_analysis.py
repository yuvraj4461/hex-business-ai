from pprint import pprint

from app.database.connection import (
    SessionLocal,
)

from app.services.commodity_analysis import (
    compare_commodity_forecasts,
)


db = SessionLocal()

try:

    commodities = [
        "Wheat, U.S., HRW",
        "Cotton",
        "Aluminum",
        "Copper",
    ]

    for commodity in commodities:

        print(
            f"\n===== {commodity} ====="
        )

        pprint(
            compare_commodity_forecasts(
                db,
                commodity,
            )
        )

finally:

    db.close()