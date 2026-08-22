from sqlalchemy.orm import Session

from app.services.commodity_analysis import (
    compare_commodity_forecasts,
)
from app.services.demand import (
    forecast_product_demand,
)


def analyze_market_shock(
    db: Session,
    organization_id: int,
) -> dict:

    demand = forecast_product_demand(
        db,
        organization_id,
    )

    copper = (
        compare_commodity_forecasts(
            db,
            "Copper",
        )
    )

    wheat = (
        compare_commodity_forecasts(
            db,
            "Wheat, U.S., HRW",
        )
    )

    return {
        "demand_forecast":
            demand,

        "commodity_shocks": {
            "copper":
                copper,

            "wheat":
                wheat,
        },
    }