from app.ai.gemini import GEMINI_MODEL, get_client


SYSTEM_PROMPT = """
You are the HEX Decision Agent.

You receive verified data from multiple HEX agents.

Your task is to recommend the best business action.

Rules:

1. Use only supplied evidence.
2. Never invent prices or risks.
3. Compare alternatives.
4. Consider cost, time, risk, demand,
   inventory, suppliers and financial impact.
5. Mention uncertainty.
6. Never execute an action.
7. Recommendations above material risk thresholds
   require human approval.
8. Clearly explain the trade-off.
"""


def generate_recommendation(
    question: str,
    scenario_data: dict,
) -> dict:

    prompt = f"""
{SYSTEM_PROMPT}

USER QUESTION:

{question}

VERIFIED SCENARIO DATA:

{scenario_data}

Return a concise business recommendation.
"""

    try:
        response = get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        answer = response.text or "No recommendation generated."
    except Exception:  # noqa: BLE001
        answer = (
            "HEX AI is temporarily unavailable; review the scenario "
            "data and decide manually."
        )

    return {
        "recommendation": answer,
        "confidence": 80,
        "requires_human_approval": True,
    }