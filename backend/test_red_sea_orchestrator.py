from pprint import pprint

from app.database.connection import (
    SessionLocal,
)

from app.services.red_sea_orchestrator import (
    run_red_sea_analysis,
)


db = SessionLocal()

try:

    result = run_red_sea_analysis(
        db=db,
        organization_id=10,
    )

    pprint(result)

finally:
    db.close()