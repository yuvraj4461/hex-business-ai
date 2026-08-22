from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.security.dependencies import (
    require_permission,
)
from app.services.agriculture import (
    get_agriculture_risks,
)
from app.services.agriculture_commodity import (
    calculate_agriculture_commodity_risk,
)


router = APIRouter(
    prefix="/agriculture",
    tags=["Agriculture"],
)


@router.get("/overview")
def agriculture_overview(
    current_user: User = Depends(
        require_permission(
            "view_analytics"
        )
    ),
    db: Session = Depends(get_db),
):

    return {
        "organization_id":
            current_user.organization_id,

        "risks":
            get_agriculture_risks(
                db
            ),

        "commodity_impact":
            calculate_agriculture_commodity_risk(
                db
            ),
    }