from app.ai.decision_agent import (
    generate_recommendation,
)


scenario = {
    "affected_route": {
        "route_name": "Shanghai → Mundra via Red Sea",
        "transit_days": 18,
        "freight_cost": 250000,
        "risk_level": "HIGH",
    },
    "alternatives": [
        {
            "route_name": "Cape of Good Hope",
            "transit_days": 28,
            "freight_cost": 340000,
            "risk_level": "LOW",
        },
        {
            "route_name": "Air Freight",
            "transit_days": 3,
            "freight_cost": 1200000,
            "risk_level": "LOW",
        },
    ],
}


answer = generate_recommendation(
    "A Red Sea disruption has occurred. "
    "Which route should the company use?",
    scenario,
)

print(answer)