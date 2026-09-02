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
8. This is a continuing conversation. Use CONVERSATION SO FAR to
   resolve references ("that", "it", "the second one", "why?") and to
   avoid repeating yourself. Answer the CURRENT question, not an
   earlier one.
"""


def _format_history(history: list[dict] | None) -> str:
    if not history:
        return ""
    lines = []
    for turn in history[-10:]:
        if not isinstance(turn, dict):
            continue
        who = "User" if turn.get("role") == "user" else "HEX"
        content = str(turn.get("content", "")).strip()[:800]
        if content:
            lines.append(f"{who}: {content}")
    if not lines:
        return ""
    return "CONVERSATION SO FAR:\n\n" + "\n\n".join(lines) + "\n\n"


def synthesize_agent_findings(
    question: str,
    findings: list[dict],
    recommendations: list[dict],
    history: list[dict] | None = None,
) -> str:

    prompt = f"""
{SYSTEM_PROMPT}

{_format_history(history)}CURRENT USER QUESTION:

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


_MONEY_KEYS = ("Revenue", "Expenses", "Profit", "Operating margin pct",
               "revenue", "expenses", "profit")


def _fallback_answer(
    question: str,
    findings: list[dict],
    recommendations: list[dict],
    reason: str | None = None,
) -> str:
    """Clean executive read-out built straight from the deterministic agent
    output — used when the LLM synthesis layer is unavailable."""

    if reason:
        logger.warning("Gemini synthesis unavailable, using fallback: %s", reason)

    def humanize(value: str) -> str:
        return value.replace("_", " ").strip().capitalize()

    lines = [
        "*HEX's language model is busy right now, so this is a direct "
        "read-out from the specialist agents — the figures are exact.*",
        "",
    ]

    # --- headline figures from the finance / verified findings ----------
    money: dict[str, object] = {}
    for f in findings or []:
        if not isinstance(f, dict):
            continue
        if f.get("type") == "finance_metrics" or f.get("source") in (
            "VERIFIED_HEX_DATABASE", "finance_metrics",
        ):
            for k, v in (f.get("data") or {}).items():
                if k in _MONEY_KEYS and not isinstance(v, (dict, list)):
                    money.setdefault(humanize(str(k)), v)

    if money:
        lines.append("**Key figures**")
        for k, v in list(money.items())[:6]:
            lines.append(f"- {k}: {v}")
        lines.append("")

    # --- what the agents flagged --------------------------------------
    if recommendations:
        lines.append("**What the agents flagged**")
        seen: set[str] = set()
        for rec in recommendations:
            if isinstance(rec, str):
                text = rec
            elif isinstance(rec, dict):
                text = (
                    rec.get("reason")
                    or rec.get("message")
                    or rec.get("note")
                    or rec.get("recommendation")
                    or humanize(str(rec.get("type", "recommendation")))
                )
                sev = rec.get("severity")
                if sev:
                    text = f"{text} [{sev}]"
            else:
                continue
            # skip the internal "instruction" recommendations meant for the LLM
            if text.lower().startswith(("use the relevant", "treat verified",
                                        "ground external")):
                continue
            if text not in seen:
                seen.add(text)
                lines.append(f"- {text}")
        lines.append("")

    # --- outside context, only if we actually have web results --------
    web = next(
        (f.get("data", {}) for f in (findings or [])
         if isinstance(f, dict) and f.get("source") == "WEB_RESEARCH"),
        None,
    )
    results = (web or {}).get("results") or []
    wiki = (web or {}).get("wikipedia") or {}
    if results or wiki.get("summary"):
        lines.append("**Outside context**")
        if wiki.get("summary"):
            lines.append(f"- {wiki.get('title')}: {wiki['summary'][:280]}")
        for r in results[:3]:
            lines.append(
                f"- {r.get('title')}: {(r.get('snippet') or '')[:160]}"
            )
        lines.append("")

    if len(lines) <= 2:
        lines.append(
            "No specialist findings were produced for this question. Try "
            "rephrasing, or check the Agents page."
        )

    return "\n".join(lines).strip()