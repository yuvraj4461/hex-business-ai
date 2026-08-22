from fastapi import APIRouter, Depends

from app.models.user import User
from app.security.dependencies import (
    require_permission,
)


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get("/status")
def agent_status(
    current_user: User = Depends(
        require_permission("run_analysis")
    ),
):

    return {
        "organization_id": current_user.organization_id,
        "agents": [
            {
                "name": "Finance Agent",
                "status": "READY",
            },
            {
                "name": "Sales Agent",
                "status": "READY",
            },
            {
                "name": "Operations Agent",
                "status": "READY",
            },
            {
                "name": "Risk Agent",
                "status": "READY",
            },
        ],
    }