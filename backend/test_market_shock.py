from pprint import pprint

from app.database.connection import SessionLocal

from app.services.market_shock import (
    analyze_market_shock,
)


db = SessionLocal()

try:

    result = analyze_market_shock(
        db,
        organization_id=10,
    )

    pprint(result)

finally:
    db.close()