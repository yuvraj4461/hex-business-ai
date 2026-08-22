from pprint import pprint

from app.database.connection import (
    SessionLocal,
)

from app.services.material_impact import (
    calculate_forecast_material_impact,
)


db = SessionLocal()

try:

    result = (
        calculate_forecast_material_impact(
            db,
            organization_id=10,
            forecast_year=2026,
        )
    )

    pprint(result)

finally:

    db.close()