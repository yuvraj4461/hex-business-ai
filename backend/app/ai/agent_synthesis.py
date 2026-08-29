import logging

from app.ai.gemini import generate_text


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are HEX, an enterprise supply-chain risk and
decision-support system.

You are given two kinds of evidence:

A. WEB_RESEARCH — live results from Google and Wikipedia. This is
   your source for outside-world facts: prices, tariffs, events,
   shipping conditions, definitions.
B. Specialist agent findings — HEX's own agents (finance, sales,
   operations, world-watch, risk) computed from THIS business's
   verified internal data (VERIFIED_HEX_DATABASE, GLOBAL_CONTEXT).

Your job: answer the user's question by grounding the external facts
in WEB_RESEARCH, then using the specialist findings to explain what
those facts mean for this specific business's finances, operations
and risk exposure.

Rules:

1. For any external fact, cite the source: put the URL in
   parentheses right after the claim.
2. Never invent numbers, events, sources or URLs.
3. Keep external facts (from WEB_RESEARCH) clearly separate from
   HEX's internal data (from the agents).
4. Treat VERIFIED_HEX_DATABASE as authoritative for this business's
   revenue, expenses, profit, orders and exposure.
5. If the web research is thin or the agents disagree, say so.
6. Do not claim any action has been executed; recommendations are
   recommendations.
7. Be concise and executive-level. End with 2-4 concrete next steps
   when the evidence supports them.
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
        text = generate_text(prompt)
    except Exception as exc:  # noqa: BLE001
        # The LLM is a synthesis layer, not the source of truth: the
        # agent findings and recommendations are already computed. If
        # Gemini is unavailable (503), rate-limited or times out, fall
        # back to a deterministic summary rather than 500-ing the request.
        return _fallback_answer(
            question, findings, recommendations, reason=str(exc)
        )

    if not text:
        return _fallback_answer(question, findings, recommendations)

    return text


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

    reason_line = (
        f" (reason: {reason.splitlines()[0][:200]})" if reason else ""
    )
    lines = [
        "HEX could not reach its language model, so this is a direct "
        "summary of the research and specialist agent output (no AI "
        "synthesis)." + reason_line,
        "",
        f"Question: {question}",
    ]

    # Web research, if any, first — it's the outside-world context.
    web = next(
        (
            f.get("data", {})
            for f in (findings or [])
            if isinstance(f, dict) and f.get("source") == "WEB_RESEARCH"
        ),
        None,
    )
    if web:
        wiki = web.get("wikipedia") or {}
        if wiki.get("summary"):
            lines += ["", f"Wikipedia — {wiki.get('title')}", wiki["summary"][:600]]
        results = web.get("results") or []
        if results:
            lines += ["", "Web results"]
            for r in results[:5]:
                lines.append(
                    f"- {r.get('title')}: {(r.get('snippet') or '')[:180]} "
                    f"({r.get('url')})"
                )

    lines += ["", "Specialist findings"]

    for item in findings or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue
        if item.get("source") == "WEB_RESEARCH":
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