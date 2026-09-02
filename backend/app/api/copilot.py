import re
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.runner import run_business_agents
from app.ai.agent_synthesis import synthesize_agent_findings
from app.ai.context_builder import build_ai_context
from app.ai.web_research import (
    looks_outward,
    research as web_research,
    sources_from,
)
from app.database.connection import get_db

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.global_event import GlobalEvent
from app.models.order import Order
from app.models.transaction import Transaction
from app.models.user import User

from app.schemas.copilot import (
    CopilotRequest,
    CopilotResponse,
)

from app.security.dependencies import require_permission

from app.ai import gemini


router = APIRouter(
    prefix="/copilot",
    tags=["AI Copilot"],
)


@router.get("/ai-status")
def ai_status(
    current_user: User = Depends(
        require_permission("view_analytics")
    ),
):
    """Live probe of the Gemini connection — diagnostic for deploys."""

    if not gemini.is_configured():
        return {
            "configured": False,
            "ok": False,
            "error": "GEMINI_API_KEY is not set on the server.",
        }

    try:
        text = gemini.generate_text("Reply with the single word: ok")
        return {
            "configured": True,
            "ok": True,
            "model": gemini._working_model or gemini.GEMINI_MODEL,
            "sample": (text or "").strip()[:80],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "configured": True,
            "ok": False,
            "model_tried": gemini.GEMINI_MODEL,
            "error": str(exc).splitlines()[0][:300],
        }


def is_financial_fact_question(
    question: str,
) -> bool:

    text = question.lower()

    keywords = [
        "revenue",
        "expense",
        "expenses",
        "profit",
        "orders",
        "order count",
        "number of orders",
        "customers",
        "customer count",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


_BUSINESS_TERMS = re.compile(
    r"\b(revenue|sales|profit|margin|cost|costs|expense|expenses|cash|runway|"
    r"burn|budget|forecast|order|orders|customer|customers|churn|retention|"
    r"supplier|suppliers|vendor|inventory|stock|warehouse|route|routes|lane|"
    r"shipment|shipments|freight|logistic|corridor|risk|exposure|disruption|"
    r"agent|agents|scenario|kpi|performance|growth|demand|pricing|valuation|"
    r"working capital|break.?even|ltv|cac|roi|ebitda|p&l|balance sheet|"
    r"business|company|operations?|finance|financial|market|economy|"
    r"strategy|invest\w*)\b",
    re.I,
)


_QUESTION_WORD = re.compile(
    r"\b(my|our|we|us|help|how|what|why|which|should|can|will|is|are|do|does)\b",
    re.I,
)


def is_business_query(question: str) -> bool:
    """Does the question plausibly relate to what HEX knows about — this
    business, its operations, markets, or risk? A bare person/place name
    ("akshay kumar") should not trigger a full agent analysis."""

    q = (question or "").strip()
    if len(q) < 3:
        return False
    if _BUSINESS_TERMS.search(q) or looks_outward(q):
        return True
    # a phrased question of a few words gets the benefit of the doubt
    return bool(_QUESTION_WORD.search(q)) and len(q.split()) >= 4


def find_relevant_event(
    db: Session,
    question: str,
) -> GlobalEvent | None:

    text = question.lower()

    events = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .all()
    )

    # Prefer an event explicitly mentioned
    # in the user's question.
    for event in events:

        title = (
            event.title or ""
        ).lower()

        region = (
            event.region or ""
        ).lower()

        event_type = (
            event.event_type or ""
        ).lower()

        if (
            "red sea" in text
            and "red sea" in title
        ):
            return event

        if (
            "turkey" in text
            and (
                "turkey" in title
                or "turkey" in region
            )
        ):
            return event

        if (
            "france" in text
            and (
                "france" in title
                or "france" in region
            )
        ):
            return event

        if (
            event_type
            and event_type in text
        ):
            return event

    return events[0] if events else None


def is_red_sea_question(
    question: str,
) -> bool:

    text = question.lower()

    return (
        "red sea" in text
        or "shipping disruption" in text
        or "shipping route" in text
    )


def get_verified_financials(
    db: Session,
    organization_id: int,
) -> dict:

    revenue_result = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
                0,
            )
        )
        .filter(
            Transaction.organization_id
            == organization_id,

            Transaction.transaction_type
            == "REVENUE",
        )
        .scalar()
    )

    expense_result = (
        db.query(
            func.coalesce(
                func.sum(
                    Expense.amount
                ),
                0,
            )
        )
        .filter(
            Expense.organization_id
            == organization_id
        )
        .scalar()
    )

    order_count = (
        db.query(
            func.count(Order.id)
        )
        .filter(
            Order.organization_id
            == organization_id
        )
        .scalar()
    )

    customer_count = (
        db.query(
            func.count(Customer.id)
        )
        .filter(
            Customer.organization_id
            == organization_id
        )
        .scalar()
    )

    revenue = float(
        revenue_result or 0
    )

    expenses = float(
        expense_result or 0
    )

    profit = (
        revenue - expenses
    )

    return {
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
        "orders": int(
            order_count or 0
        ),
        "customers": int(
            customer_count or 0
        ),
    }


@router.post(
    "/ask",
    response_model=CopilotResponse,
)
def ask_copilot(
    request: CopilotRequest,
    current_user: User = Depends(
        require_permission("run_analysis")
    ),
    db: Session = Depends(get_db),
):

    organization_id = (
        current_user.organization_id
    )

    # ---------------------------------------------
    # Select the event relevant to the question
    # ---------------------------------------------

    relevant_event = (
        find_relevant_event(
            db,
            request.question,
        )
    )

    # ---------------------------------------------
    # Build complete HEX context
    # ---------------------------------------------

    context = build_ai_context(
        db=db,
        organization_id=organization_id,
        event=relevant_event,
    )

    # ---------------------------------------------
    # Get verified production financial facts
    # directly from the database.
    # ---------------------------------------------

    financials = (
        get_verified_financials(
            db,
            organization_id,
        )
    )

    # Add verified facts into the returned context
    # so the frontend and AI layers can see them.
    context[
        "verified_facts"
    ] = financials

    # ---------------------------------------------
    # Direct verified financial answer
    #
    # Only as a conversation opener — once there's history, a
    # follow-up deserves a reasoned answer, so fall through to the
    # synthesis path (which still has the verified figures).
    # ---------------------------------------------

    if (
        not request.history
        and not request.agents
        and is_financial_fact_question(request.question)
    ):

        answer = (
            "## Verified HEX Financial Summary\n\n"

            f"- **Revenue:** "
            f"₹{financials['revenue']:,.2f}\n"

            f"- **Expenses:** "
            f"₹{financials['expenses']:,.2f}\n"

            f"- **Profit:** "
            f"₹{financials['profit']:,.2f}\n"

            f"- **Number of Orders:** "
            f"{financials['orders']}\n"

            f"- **Customers:** "
            f"{financials['customers']}\n\n"

            "These values are calculated directly "
            "from the organization's production "
            "database."
        )

        return {
            "question":
                request.question,

            "answer":
                answer,

            "data":
                context,
        }

    # ---------------------------------------------
    # Direct Red Sea answer
    # ---------------------------------------------

    if is_red_sea_question(
        request.question
    ):

        event = (
            context.get(
                "global_event"
            )
            or {}
        )

        exposure = (
            context.get(
                "exposure"
            )
            or {}
        )

        financial = (
            exposure.get(
                "financial"
            )
            or {}
        )

        business_risk = (
            exposure.get(
                "business_risk"
            )
            or {}
        )

        revenue_at_risk = float(
            financial.get(
                "total_revenue_at_risk",
                0,
            )
            or 0
        )

        affected_routes = int(
            financial.get(
                "affected_routes",
                0,
            )
            or 0
        )

        total_cost_impact = float(
            financial.get(
                "total_cost_impact",
                0,
            )
            or 0
        )

        risk_level = (
            business_risk.get(
                "level"
            )
            or event.get(
                "severity"
            )
            or "UNKNOWN"
        )

        risk_score = (
            business_risk.get(
                "score"
            )
        )

        exposure_count = (
            business_risk.get(
                "exposure_count",
                affected_routes,
            )
        )

        answer = (
            "## Red Sea Disruption Assessment\n\n"

            f"- **Event:** "
            f"{event.get('title', 'Simulated Red Sea shipping disruption')}\n"

            f"- **Severity:** "
            f"{event.get('severity', 'HIGH')}\n"

            f"- **Revenue at Risk:** "
            f"₹{revenue_at_risk:,.2f}\n"

            f"- **Affected Routes:** "
            f"{affected_routes}\n"

            f"- **Cost Impact:** "
            f"₹{total_cost_impact:,.2f}\n"

            f"- **Business Risk:** "
            f"{risk_level}\n"

            f"- **Exposure Count:** "
            f"{exposure_count}\n"
        )

        if risk_score is not None:
            answer += (
                f"- **Risk Score:** "
                f"{risk_score}/100\n"
            )

        answer += (
            "\n## Recommended Actions\n\n"

            "1. **Activate alternative supply routes** "
            "for shipments exposed to the Red Sea.\n"

            "2. **Review supplier and inventory exposure** "
            "for products dependent on affected routes.\n"

            "3. **Compare the financial trade-off** "
            "between rerouting costs and the current "
            "revenue at risk.\n"

            "4. **Evaluate alternative routes** such as "
            "the Cape of Good Hope or Air Freight where "
            "commercially justified.\n"

            "5. **Escalate the decision for human approval** "
            "before implementing a material route change."
        )

        return {
            "question":
                request.question,

            "answer":
                answer,

            "data":
                context,
        }

    # ---------------------------------------------
    # General AI questions
    # ---------------------------------------------

    # An off-topic query (a bare name, "akshay kumar") shouldn't spin up a
    # full agent analysis and present it as if it were an answer.
    if not is_business_query(request.question):
        return {
            "question": request.question,
            "answer": (
                "That doesn't look like a question I can help with. HEX "
                "answers questions about **your business** — its finances, "
                "sales, customers, suppliers and inventory — and about "
                "**markets and global risk** that could affect it.\n\n"
                "Try, for example: *\"what's driving my expenses this "
                "quarter?\"*, *\"which suppliers have the longest lead "
                "times?\"*, or *\"how would a Red Sea disruption affect my "
                "costs?\"*"
            ),
            "data": {"organization_id": organization_id},
            "sources": [],
        }

    # Web research (network-bound) runs alongside the agent graph
    # (DB-bound) instead of after it. Only for questions about the
    # outside world - an internal question gets a spurious Wikipedia hit.
    _empty_web = {"provider": "none", "results": [], "wikipedia": None}
    if looks_outward(request.question):
        _web_pool = ThreadPoolExecutor(max_workers=1)
        _web_future = _web_pool.submit(web_research, request.question)
    else:
        _web_pool = None
        _web_future = None

    agent_result = run_business_agents(
        question=request.question,
        organization_id=organization_id,
        db=db,
        agents=request.agents or None,
    )

    if _web_future is not None:
        try:
            web = _web_future.result(timeout=20)
        except Exception:  # noqa: BLE001
            web = _empty_web
        finally:
            _web_pool.shutdown(wait=False)
    else:
        web = _empty_web
    web_sources = sources_from(web)

    findings = []
    if web.get("results") or web.get("wikipedia"):
        findings.append({
            "source": "WEB_RESEARCH",
            "data": {
                "provider": web.get("provider"),
                "results": web.get("results", []),
                "wikipedia": web.get("wikipedia"),
            },
        })

    findings += list(
        agent_result.get(
            "findings",
            [],
        )
        or []
    )

    recommendations = list(
        agent_result.get(
            "recommendations",
            [],
        )
        or []
    )

    # Verified financials are grounding for the finance/risk lens. If the
    # user narrowed "Consult" to agents that don't include finance, don't
    # inject them — a World-Watch-only question shouldn't lead with revenue.
    finance_in_scope = (not request.agents) or ("finance" in request.agents)
    if finance_in_scope:
        findings.append(
            {
                "source": "VERIFIED_HEX_DATABASE",
                "data": financials,
            }
        )

    findings.append(
        {
            "source":
                "RELEVANT_GLOBAL_EVENT",

            "data":
                context.get(
                    "global_event"
                ),
        }
    )

    context_for_findings = context
    if not finance_in_scope:
        context_for_findings = {
            k: v for k, v in context.items() if k != "verified_facts"
        }
        biz = context_for_findings.get("business")
        if isinstance(biz, dict):
            context_for_findings["business"] = {
                k: v for k, v in biz.items()
                if k != "verified_financial_metrics"
            }

    findings.append(
        {
            "source":
                "GLOBAL_CONTEXT",

            "data":
                context_for_findings,
        }
    )

    recommendations.append(
        (
            "Use the relevant global event selected "
            "from the user's question. Do not substitute "
            "an unrelated event merely because it is the "
            "latest event in the database."
        )
    )

    if finance_in_scope:
        recommendations.append(
            (
                "Treat VERIFIED_HEX_DATABASE as authoritative "
                "for revenue, expenses, profit, order count, "
                "customer count, and verified business exposure."
            )
        )

    recommendations.append(
        (
            "Ground external facts (prices, events, tariffs, definitions) "
            "in WEB_RESEARCH and cite the source URLs. Use the specialist "
            "agent findings to explain what it means for this business."
        )
    )

    answer = synthesize_agent_findings(
        question=request.question,
        findings=findings,
        recommendations=recommendations,
        history=[
            turn.model_dump()
            for turn in request.history
        ][-10:],
    )

    return {
        "question":
            request.question,

        "answer":
            answer,

        "data":
            context,

        "sources":
            web_sources,
    }