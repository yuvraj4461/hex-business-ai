from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.user import User

from app.security.dependencies import (
    require_permission,
)

from app.services.red_sea_orchestrator import (
    run_red_sea_analysis,
)


router = APIRouter(
    prefix="/demo",
    tags=["Demo"],
)


@router.get(
    "/red-sea"
)
def red_sea_demo(
    current_user: User = Depends(
        require_permission(
            "view_analytics"
        )
    ),

    db: Session = Depends(
        get_db
    ),
):

    return run_red_sea_analysis(
        db=db,
        organization_id=(
            current_user.organization_id
        ),
    )