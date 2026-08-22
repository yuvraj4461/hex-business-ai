from pprint import pprint

from app.database.connection import SessionLocal
from app.services.route_optimizer import (
    find_alternative_routes,
)


db = SessionLocal()

try:

    organization_id = 10

    affected_route_id = (
        1
    )

    alternatives = (
        find_alternative_routes(
            db,
            organization_id,
            affected_route_id,
        )
    )

    pprint(alternatives)

finally:
    db.close()