from app.services.global_signals import (
    collect_global_signals,
)

from app.services.commodity_analysis import (
    compare_commodity_forecasts,
)

from app.services.demand import (
    forecast_product_demand,
)

from app.services.agriculture import (
    get_agriculture_risks,
)


def get_global_intelligence(
    db,
    organization_id: int,
    latitude: float,
    longitude: float,
) -> dict:

    global_signals = (
        collect_global_signals(
            latitude=latitude,
            longitude=longitude,
        )
    )

    demand = forecast_product_demand(
        db,
        organization_id,
    )

    agriculture = get_agriculture_risks(
        db,
    )

    commodities = {}

    for commodity in [
        "Wheat, U.S., HRW",
        "Cotton",
        "Aluminum",
        "Copper",
    ]:

        commodities[commodity] = (
            compare_commodity_forecasts(
                db,
                commodity,
            )
        )

    return {
        "organization_id":
            organization_id,

        "global_signals":
            global_signals,

        "commodities":
            commodities,

        "demand":
            demand,

        "agriculture":
            agriculture,
    }