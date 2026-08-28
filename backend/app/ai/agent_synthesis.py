import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


logger = logging.getLogger(__name__)

load_dotenv()

# Bound how long the copilot will wait on Gemini. When the model is slow
# or overloaded the request falls back to a deterministic summary rather
# than hanging the HTTP request (and the frontend spinner) indefinitely.
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "25000"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
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

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
    except Exception as exc:  # noqa: BLE001
        # The LLM is a synthesis layer, not the source of truth: the
        # agent findings and recommendations are already computed. If
        # Gemini is unavailable (503), rate-limited or times out, fall
        # back to a deterministic summary rather than 500-ing the request.
        return _fallback_answer(
            question, findings, recommendations, reason=str(exc)
        )

    if not response.text:
        return _fallback_answer(question, findings, recommendations)

    return response.text


def _fallback_answer(
    question: str,
    findings: list[dict],
    recommendations: list[dict],
    reason: str | None = None,
) -> str:
    """Readable summary built directly from agent output, no LLM."""

    if reason:
        logger.warning("Gemini synthesis unavailable, using fallback: %s", reason)

    def humanize(value: str) -> str:
        return value.replace("_", " ").strip().capitalize()

    def scalars(data: dict) -> str:
        """One-line view of a finding's simple (non-nested) fields."""

        parts = [
            f"{humanize(str(k))}: {v}"
            for k, v in (data or {}).items()
            if not isinstance(v, (dict, list))
        ]
        return "; ".join(parts[:6])

    lines = [
        "HEX could not reach its language model, so this is a direct "
        "summary of the specialist agent output (no AI synthesis).",
        "",
        f"Question: {question}",
        "",
        "Findings",
    ]

    for item in findings or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue

        label = (
            item.get("agent")
            or item.get("source")
            or humanize(str(item.get("type", "finding")))
        )
        detail = scalars(item.get("data", {}))
        lines.append(f"- {label}" + (f" — {detail}" if detail else ""))

    if recommendations:
        lines.append("")
        lines.append("Recommendations")
        for rec in recommendations:
            if not isinstance(rec, dict):
                lines.append(f"- {rec}")
                continue

            text = (
                rec.get("message")
                or rec.get("note")
                or rec.get("recommendation")
                or humanize(str(rec.get("type", "recommendation")))
            )
            severity = rec.get("severity")
            lines.append(
                f"- {text}" + (f" [{severity}]" if severity else "")
            )

    return "\n".join(lines)