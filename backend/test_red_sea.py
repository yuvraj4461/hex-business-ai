from pprint import pprint

from app.database.connection import SessionLocal
from app.services.exposure_engine import (
    analyze_event_exposure,
)
from app.services.scenarios import (
    create_red_sea_simulation,
)


db = SessionLocal()

try:

    organization_id = 10

    event = create_red_sea_simulation(
        db
    )

    exposures = analyze_event_exposure(
        db,
        event,
        organization_id,
    )

    print(
        "\nSIMULATED EVENT:"
    )

    pprint(
        {
            "id": event.id,
            "title": event.title,
            "severity": event.severity,
            "region": event.region,
        }
    )

    print(
        "\nEXPOSURES:"
    )

    for exposure in exposures:

        pprint(
            {
                "route_id": exposure.route_id,
                "supplier_id": exposure.supplier_id,
                "product_id": exposure.product_id,
                "severity": exposure.severity,
                "delay_days":
                    exposure.estimated_delay_days,
                "cost_impact":
                    float(
                        exposure.estimated_cost_impact
                    ),
                "revenue_at_risk":
                    float(
                        exposure
                        .estimated_revenue_at_risk
                    ),
            }
        )

finally:
    db.close()