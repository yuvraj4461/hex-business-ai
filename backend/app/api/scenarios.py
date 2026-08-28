from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.decision_agent import (
    generate_recommendation,
)
from app.database.connection import get_db
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.scenario import (
    ScenarioRequest,
    ScenarioResponse,
)
from app.security.dependencies import (
    get_current_user,
    require_permission,
)
from app.services.scenario_engine import (
    evaluate_route_scenario,
)
from app.services.red_sea_orchestrator import (
    run_event_scenario,
)
from app.models.recommendation import (
    Recommendation,
)


router = APIRouter(
    prefix="/scenarios",
    tags=["Scenarios"],
)


@router.get("/{event_id}")
def event_scenario(
    event_id: int,
    current_user: User = Depends(
        require_permission("view_analytics")
    ),
    db: Session = Depends(get_db),
):
    """Full scenario analysis for any detected global event.

    Same shape as ``GET /demo/red-sea`` but for an arbitrary event.
    ``status`` is ``NOT_FOUND`` when the event id does not exist and
    ``OK`` with zeroed exposure when the event does not touch the
    org's supply chain.
    """

    result = run_event_scenario(
        db=db,
        organization_id=current_user.organization_id,
        event_id=event_id,
    )

    if result.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=result["message"])

    return result


@router.post(
    "/route",
    response_model=ScenarioResponse,
)
def create_route_scenario(
    request: ScenarioRequest,
    current_user: User = Depends(
        require_permission(
            "run_simulations"
        )
    ),
    db: Session = Depends(get_db),
):

    scenario_data = evaluate_route_scenario(
        db,
        current_user.organization_id,
        request.route_id,
    )

    if scenario_data["status"] != "OK":
        raise HTTPException(
            status_code=404,
            detail=scenario_data[
                "message"
            ],
        )

    scenario = Scenario(
        organization_id=(
            current_user.organization_id
        ),
        name=request.name,
        scenario_type=request.scenario_type,
        description=(
            "Route disruption scenario"
        ),
        status="ANALYZED",
        input_data={
            "route_id": request.route_id,
        },
        result_data=scenario_data,
        completed_at=datetime.utcnow(),
    )

    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    recommendation = generate_recommendation(
        request.name,
        scenario_data,
    )
    recommendation_record = Recommendation(
        organization_id=(
        current_user.organization_id
        ),
        scenario_id=scenario.id,
        title=request.name,
        recommendation_type="ROUTE_CHANGE",
        priority="HIGH",
        reasoning=recommendation["recommendation"],
        estimated_cost=None,
        estimated_benefit=None,
        confidence=float(recommendation.get("confidence", 80)),
        status="PENDING_APPROVAL",
        metadata=scenario_data,
    )

    db.add(
    recommendation_record
    )

    db.commit()

    scenario.result_data = {
        **scenario_data,
        "ai_recommendation": recommendation,
    }

    db.commit()

    return {
        "id": scenario.id,
        "name": scenario.name,
        "scenario_type": scenario.scenario_type,
        "status": scenario.status,
        "result": scenario.result_data,
    }