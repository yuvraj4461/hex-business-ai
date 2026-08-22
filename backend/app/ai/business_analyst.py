import os
import json

from dotenv import load_dotenv
from google import genai

from app.ai.serialization import (
    make_json_safe,
)


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
You are HEX Business Intelligence AI.

You analyze verified business and global-event
data supplied by the HEX platform.

Rules:

1. Use only supplied data.
2. Never invent values.
3. Clearly separate facts from inference.
4. Mention uncertainty when data is incomplete.
5. Compare alternatives when available.
6. Do not claim that any action was executed.
7. High-impact recommendations require human approval.
8. Be concise but useful for a business decision maker.
"""


def ask_business_ai(
    question: str,
    context: dict,
) -> str:

    safe_context = make_json_safe(
        context
    )

    prompt = f"""
{SYSTEM_PROMPT}

BUSINESS CONTEXT:

{json.dumps(
    safe_context,
    indent=2,
)}

USER QUESTION:

{question}

Answer the user's question using only
the supplied HEX context.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        if response.text:
            return response.text

        return (
            "HEX AI did not return a textual "
            "recommendation."
        )

    except Exception as exc:

        error_text = str(exc)

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED"
            in error_text
            or "quota" in error_text.lower()
        ):

            return (
                "Gemini AI is temporarily "
                "unavailable because the current "
                "API quota has been exhausted. "
                "HEX completed the business, "
                "route and financial analysis "
                "without AI generation. "
                "Human review is recommended "
                "before taking action."
            )

        raise