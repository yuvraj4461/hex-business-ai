from pprint import pprint

from app.database.connection import SessionLocal

from app.services.demand import (
    forecast_product_demand,
)


db = SessionLocal()

try:

    result = forecast_product_demand(
        db,
        organization_id=10,
    )

    pprint(result)

finally:
    db.close()