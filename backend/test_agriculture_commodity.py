from pprint import pprint

from app.database.connection import SessionLocal

from app.services.agriculture_commodity import (
    calculate_agriculture_commodity_risk,
)


db = SessionLocal()

try:

    result = (
        calculate_agriculture_commodity_risk(
            db
        )
    )

    pprint(result)

finally:
    db.close()