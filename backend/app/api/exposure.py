from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.business_exposure import (
    BusinessExposure,
)
from app.models.user import User
from app.security.dependencies import (
    get_current_user,
    require_permission,
)


router = APIRouter(
    prefix="/exposure",
    tags=["Business Exposure"],
)


@router.get("/")
def get_exposures(
    current_user: User = Depends(
        require_permission(
            "view_analytics"
        )
    ),
    db: Session = Depends(get_db),
):

    exposures = (
        db.query(BusinessExposure)
        .filter(
            BusinessExposure.organization_id
            == current_user.organization_id
        )
        .order_by(
            BusinessExposure.detected_at.desc()
        )
        .all()
    )

    return [
        {
            "id": exposure.id,
            "event_id": (
                exposure.global_event_id
            ),
            "route_id": exposure.route_id,
            "supplier_id": (
                exposure.supplier_id
            ),
            "product_id": (
                exposure.product_id
            ),
            "exposure_type": (
                exposure.exposure_type
            ),
            "severity": (
                exposure.severity
            ),
            "delay_days": (
                exposure.estimated_delay_days
            ),
            "cost_impact": float(
                exposure.estimated_cost_impact
            ),
            "revenue_at_risk": float(
                exposure
                .estimated_revenue_at_risk
            ),
            "explanation": (
                exposure.explanation
            ),
            "detected_at": (
                exposure.detected_at
            ),
        }
        for exposure in exposures
    ]