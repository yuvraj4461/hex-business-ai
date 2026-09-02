"""Finance Agent.

Every number it reports comes from the deterministic engine in
``app.finance`` — a tested formula library run against the org's real ERP
data. The agent's job is to select which metrics matter and raise
threshold-based recommendations; it never does arithmetic itself and the
LLM downstream only explains the figures it is handed.
"""

from sqlalchemy.orm import Session

from app.ai.agent_context import get_agent_context
from app.finance.engine import company_finance, flatten_for_agent
from app.models.global_event import GlobalEvent


def _value(battery: dict, section: str, label: str):
    for row in battery.get("sections", {}).get(section, []):
        if row["label"] == label:
            return row["value"]
    return None


def finance_agent(state: dict, db: Session) -> dict:
    organization_id = state["organization_id"]

    findings = list(state.get("findings", []))
    recommendations = list(state.get("recommendations", []))

    # -------------------------------------------------
    # 1. Deterministic financial battery
    # -------------------------------------------------
    battery = company_finance(db, organization_id)

    findings.append(
        {
            "agent": "Finance Agent",
            "type": "finance_metrics",
            "data": {
                **flatten_for_agent(battery),
                # keep the structured detail available for the UI / audit
                "sections": battery["sections"],
                "series": battery["series"],
            },
        }
    )

    # -------------------------------------------------
    # 2. Threshold-driven recommendations
    # -------------------------------------------------
    margin = battery["headline"]["operating_margin_pct"]
    if margin < 10:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "thin_operating_margin",
            "severity": "MEDIUM" if margin >= 0 else "HIGH",
            "reason": (
                f"Operating margin is {margin:.1f}% — below a healthy 10-15% "
                "band. Review pricing and the largest expense categories."
            ),
        })

    mom = _value(battery, "growth", "Revenue MoM growth")
    if mom is not None and mom <= -10:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "revenue_contraction",
            "severity": "HIGH",
            "reason": (
                f"Revenue fell {abs(mom):.1f}% month-over-month. Audit recent "
                "orders, churn and pipeline."
            ),
        })

    cov = _value(battery, "risk", "Revenue volatility (CoV)")
    if cov is not None and cov >= 50:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "volatile_revenue",
            "severity": "MEDIUM",
            "reason": (
                f"Monthly revenue varies by {cov:.0f}% of its mean — cash "
                "planning should assume a wide range."
            ),
        })

    runway = _value(battery, "cash", "Runway")
    if runway is not None and runway < 6:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "short_runway",
            "severity": "HIGH",
            "reason": (
                f"At the current burn there are about {runway:.1f} months of "
                "cash (proxy). Cut discretionary spend or raise capital."
            ),
        })

    ltv_cac = _value(battery, "unit_economics", "LTV : CAC")
    if ltv_cac is not None and ltv_cac < 3:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "weak_unit_economics",
            "severity": "MEDIUM",
            "reason": (
                f"LTV:CAC is {ltv_cac:.1f} (target > 3). Acquisition is not "
                "paying back fast enough — rework channels or retention."
            ),
        })

    vs_be = _value(battery, "break_even", "Current monthly revenue vs break-even")
    if vs_be is not None and vs_be < 0:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "below_break_even",
            "severity": "HIGH",
            "reason": (
                f"Average monthly revenue is about ₹{abs(vs_be):,.0f} short of "
                "the monthly break-even point."
            ),
        })

    # -------------------------------------------------
    # 3. External financial context (unchanged)
    # -------------------------------------------------
    latest_event = (
        db.query(GlobalEvent)
        .order_by(GlobalEvent.detected_at.desc())
        .first()
    )
    global_context = get_agent_context(
        db=db, organization_id=organization_id, event=latest_event
    )

    market_context = global_context.get("market", {}) or {}
    exposure_context = global_context.get("exposure")
    agriculture_context = global_context.get("agriculture", []) or []
    demand_context = (
        global_context.get("business", {}).get("demand_forecast", []) or []
    )
    global_event_context = global_context.get("global_event")

    findings.append({
        "agent": "Finance Agent",
        "type": "global_financial_context",
        "data": {
            "global_event": global_event_context,
            "market": market_context,
            "agriculture": agriculture_context,
            "demand_forecast": demand_context,
            "business_exposure": exposure_context,
        },
    })

    if exposure_context:
        financial = exposure_context.get("financial", {}) or {}
        revenue_at_risk = float(financial.get("total_revenue_at_risk", 0) or 0)
        if revenue_at_risk > 0:
            recommendations.append({
                "agent": "Finance Agent",
                "type": "global_event_financial_risk",
                "reason": "A global event has created financial exposure.",
                "revenue_at_risk": revenue_at_risk,
                "cost_impact": float(financial.get("total_cost_impact", 0) or 0),
            })

    if global_event_context and global_event_context.get("severity") in {
        "HIGH", "CRITICAL",
    }:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "high_risk_global_event",
            "reason": "A high-severity global event may affect financial performance.",
            "event": global_event_context.get("title"),
            "severity": global_event_context.get("severity"),
        })

    for name, analysis in (market_context.get("commodities", {}) or {}).items():
        if not isinstance(analysis, dict) or analysis.get("status") != "OK":
            continue
        change = float(analysis.get("percentage_change", 0) or 0)
        if change >= 5:
            recommendations.append({
                "agent": "Finance Agent",
                "type": "commodity_cost_risk",
                "commodity": name,
                "percentage_change": change,
                "reason": f"{name} rose materially in the forecast data.",
            })

    high_ag = [s for s in agriculture_context
               if s.get("severity") in {"HIGH", "CRITICAL"}]
    if high_ag:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "agriculture_cost_risk",
            "reason": "High-severity agriculture signals may raise input costs.",
            "risk_count": len(high_ag),
        })

    high_growth = [i for i in demand_context
                   if float(i.get("growth_rate", 0) or 0) >= 0.20]
    if high_growth:
        recommendations.append({
            "agent": "Finance Agent",
            "type": "high_demand_growth",
            "reason": (
                "Strong forecast demand growth may need extra working capital "
                "or inventory."
            ),
            "product_count": len(high_growth),
        })

    return {
        **state,
        "findings": findings,
        "recommendations": recommendations,
    }
