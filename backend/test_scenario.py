from pprint import pprint

from app.database.connection import SessionLocal
from app.services.scenario_engine import (
    evaluate_route_scenario,
)


db = SessionLocal()

try:

    organization_id = 10

    affected_route_id = 1

    result = evaluate_route_scenario(
        db,
        organization_id,
        affected_route_id,
    )

    pprint(result)

finally:
    db.close()