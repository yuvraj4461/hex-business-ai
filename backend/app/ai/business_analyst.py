import logging
import json

from app.ai.gemini import GEMINI_MODEL, get_client
from app.ai.serialization import (
    make_json_safe,
)


logger = logging.getLogger(__name__)


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

        response = get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        if response.text:
            return response.text

        return (
            "HEX AI did not return a textual "
            "recommendation."
        )

    except Exception as exc:  # noqa: BLE001

        # Gemini is a synthesis layer on top of already-computed HEX
        # analysis. Quota (429), overload (503), deadline (504) and
        # client timeouts should all degrade to a non-AI answer rather
        # than 500-ing the caller.
        logger.warning("Gemini business analysis unavailable: %s", exc)

        return (
            "Gemini AI is temporarily unavailable "
            f"({str(exc).splitlines()[0][:200]}). "
            "HEX completed the business, route and financial "
            "analysis without AI generation. Human review is "
            "recommended before taking action."
        )