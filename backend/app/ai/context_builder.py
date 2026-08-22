from sqlalchemy.orm import Session

from app.models.global_event import GlobalEvent
from app.services.demand import (
    forecast_product_demand,
)
from app.services.agriculture import (
    get_agriculture_risks,
)
from app.services.commodity_analysis import (
    compare_commodity_forecasts,
)
from app.services.global_exposure import (
    build_global_exposure_summary,
)


def build_ai_context(
    db: Session,
    organization_id: int,
    event: GlobalEvent | None = None,
) -> dict:

    context = {
        "organization_id":
            organization_id,

        "business": {
            "demand_forecast":
                forecast_product_demand(
                    db,
                    organization_id,
                ),
        },

        "market": {
            "commodities": {},
        },

        "agriculture": (
            get_agriculture_risks(db)
        ),

        "global_event": None,

        "exposure": None,
    }

    for commodity in [
        "Wheat, U.S., HRW",
        "Cotton",
        "Aluminum",
        "Copper",
    ]:

        context[
            "market"
        ][
            "commodities"
        ][commodity] = (
            compare_commodity_forecasts(
                db,
                commodity,
            )
        )

    if event:

        context[
            "global_event"
        ] = {
            "id": event.id,
            "source": event.source,
            "type": event.event_type,
            "title": event.title,
            "severity": event.severity,
            "region": event.region,
            "detected_at": (
                event.detected_at
            ),
        }

        context[
            "exposure"
        ] = build_global_exposure_summary(
            db,
            organization_id,
            event,
        )

    return context