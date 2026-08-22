from pprint import pprint

from app.database.connection import (
    SessionLocal,
)

from app.services.global_intelligence import (
    get_global_intelligence,
)


db = SessionLocal()

try:

    result = get_global_intelligence(
        db=db,
        organization_id=10,
        latitude=30.7333,
        longitude=76.7794,
    )

    pprint(result)

finally:
    db.close()