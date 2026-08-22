from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.user import User

from app.security.dependencies import (
    require_permission,
)

from app.services.commodity_analysis import (
    compare_commodity_forecasts,
)

from app.services.fx import (
    get_fx_rate,
)

from app.services.market_signals import (
    analyze_fx_movement,
)

from app.services.material_impact import (
    calculate_forecast_material_impact,
)


router = APIRouter(
    prefix="/market",
    tags=["Market Intelligence"],
)


@router.get(
    "/overview"
)
def market_overview(
    current_user: User = Depends(
        require_permission(
            "view_analytics"
        )
    ),

    db: Session = Depends(
        get_db
    ),
):

    commodities = {}

    for commodity in [
        "Wheat, U.S., HRW",
        "Cotton",
        "Aluminum",
        "Copper",
    ]:

        commodities[
            commodity
        ] = compare_commodity_forecasts(
            db,
            commodity,
        )

    return {
        "organization_id":
            current_user.organization_id,

        "fx": (
            analyze_fx_movement(
                db,
                "USD/INR",
            )
        ),

        "commodities":
            commodities,

        "material_impact":
            calculate_forecast_material_impact(
                db,
                current_user.organization_id,
                2026,
            ),
    }