from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):

    name: str = Field(
        min_length=3,
        max_length=200,
    )

    scenario_type: str = Field(
        min_length=3,
        max_length=100,
    )

    route_id: int


class ScenarioResponse(BaseModel):

    id: int

    name: str

    scenario_type: str

    status: str

    result: dict