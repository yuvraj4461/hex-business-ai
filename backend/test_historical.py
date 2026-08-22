from pprint import pprint

from app.database.connection import SessionLocal
from app.services.historical_analytics import (
    get_historical_snapshot,
)


db = SessionLocal()

try:
    result = get_historical_snapshot(
        db,
        organization_id=10,
    )

    pprint(result)

finally:
    db.close()