import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)


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

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    answer = (
        response.text
        if response.text
        else "No recommendation generated."
    )

    return {
        "recommendation": answer,
        "confidence": 80,
        "requires_human_approval": True,
    }