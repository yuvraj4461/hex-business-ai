from app.database.connection import SessionLocal
from app.services.analytics import get_revenue_analysis


db = SessionLocal()

try:
    result = get_revenue_analysis(
        db,
        organization_id=10,
    )

    print(result)

finally:
    db.close()