from pprint import pprint

from app.database.connection import SessionLocal
from app.services.agriculture import (
    get_agriculture_risks,
)


db = SessionLocal()

try:

    result = get_agriculture_risks(
        db,
        region="Punjab, India",
    )

    pprint(result)

finally:
    db.close()