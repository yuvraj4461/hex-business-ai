from pprint import pprint

from app.agents.runner import (
    run_business_agents,
)
from app.database.connection import (
    SessionLocal,
)


db = SessionLocal()

try:

    result = run_business_agents(
        question="Analyze my business performance.",
        organization_id=10,
        db=db,
    )

    pprint(result)

finally:
    db.close()