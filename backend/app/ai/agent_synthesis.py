import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


SYSTEM_PROMPT = """
You are HEX, an enterprise business intelligence and
decision-support system.

You receive findings from specialized business agents.

Your job is to combine those findings into one accurate,
clear executive-level answer.

Rules:

1. Use only the supplied agent findings.
2. Never invent numbers.
3. Never invent events or causes.
4. Clearly distinguish facts from interpretation.
5. Mention which specialist findings support the conclusion.
6. If agents disagree or data is insufficient, say so.
7. Do not claim that an action has been executed.
8. Recommendations must be presented as recommendations,
   not completed actions.
9. Keep the answer useful and concise.
10. Do not expose internal implementation details unless
    the user asks about them.
"""


def synthesize_agent_findings(
    question: str,
    findings: list[dict],
    recommendations: list[dict],
) -> str:

    prompt = f"""
{SYSTEM_PROMPT}

USER QUESTION:

{question}

SPECIALIST AGENT FINDINGS:

{findings}

CURRENT RECOMMENDATIONS:

{recommendations}

Create a single business answer that:

- directly answers the user's question,
- summarizes the strongest evidence,
- identifies important risks,
- explains uncertainty where applicable,
- and provides useful recommendations when supported.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    if not response.text:
        return "HEX could not generate an answer."

    return response.text