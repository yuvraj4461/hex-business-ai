"""Smoke test for "Ask Your Data" conversational analytics.

    DATABASE_URL=postgresql://... python test_analytics_ask.py

Runs against a seeded org. The LLM is forced off so this exercises the
deterministic planner + executor + narrator fallback and the thread
persistence path. No network needed.
"""

import sys

import app.ai.gemini as gemini

# Force the deterministic path everywhere.
gemini.is_configured = lambda: False  # type: ignore[assignment]

from app.analytics.planner import plan_query  # noqa: E402
from app.analytics.executor import run_spec  # noqa: E402
from app.analytics.semantic import QuerySpec  # noqa: E402
from app.analytics.service import answer_data_question  # noqa: E402
from app.api.analytics_ask import _run_turn  # noqa: E402
from app.database.connection import SessionLocal  # noqa: E402
from app.models.data_thread import DataThread  # noqa: E402
from app.models.user import User  # noqa: E402

ORG_ID = 10


def main() -> int:
    db = SessionLocal()
    try:
        # 1. deterministic planner ------------------------------------------------
        # "revenue by month" is unambiguous -> planner answers without the LLM
        spec, degraded = plan_query("revenue by month")
        assert degraded is False
        assert spec.metric == "revenue" and spec.dimension == "month"
        assert spec.sort == "chrono"

        spec2, _ = plan_query("top 5 products by revenue")
        assert spec2.metric == "product_revenue", spec2.metric
        assert spec2.dimension == "product" and spec2.limit == 5

        spec3, _ = plan_query("expenses by category in 2026")
        assert spec3.metric == "expenses" and spec3.dimension == "expense_category"
        assert spec3.year == 2026

        # refinement carries the prior metric
        spec4, _ = plan_query("break it down by product", spec.to_dict())
        assert spec4.dimension == "product"

        # 2. executor ------------------------------------------------------------
        r1 = run_spec(db, ORG_ID, spec)
        assert r1["chart"]["type"] == "line"
        assert r1["row_count"] >= 1, "seeded org should have monthly revenue"
        assert all("label" in row and "value" in row for row in r1["rows"])

        r2 = run_spec(db, ORG_ID, spec2)
        assert r2["chart"]["type"] == "bar"
        assert r2["row_count"] <= 5

        r_total = run_spec(db, ORG_ID, QuerySpec(metric="revenue"))
        assert r_total["chart"]["type"] == "stat"
        total = r_total["rows"][0]["value"]
        assert total > 0

        # org scoping — a nonexistent org yields nothing, never an error
        r_empty = run_spec(db, 999_999, QuerySpec(metric="revenue"))
        assert r_empty["rows"][0]["value"] == 0

        # 3. service shape ----------------------------------------------------
        # "revenue by month" is unambiguous, so even with Gemini off the
        # planner is confident and the answer is NOT flagged degraded.
        out = answer_data_question(db, ORG_ID, "revenue by month")
        assert out["degraded"] is False
        assert out["answer"] and isinstance(out["answer"], str)
        assert out["spec_label"].startswith("Revenue")
        assert out["result"]["row_count"] >= 1

        # a vague question with Gemini off -> keyword fallback -> degraded
        vague = answer_data_question(db, ORG_ID, "how is the shop doing lately")
        assert vague["degraded"] is True
        assert vague["result"]["chart"] is not None

        # 4. thread persistence + follow-up ----------------------------------
        user = db.query(User).filter(User.organization_id == ORG_ID).first()
        assert user is not None, "seeded org needs a user"

        thread = DataThread(
            organization_id=ORG_ID, user_id=user.id, title="smoke test"
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)

        _run_turn(db, thread, user, "revenue by month")
        _run_turn(db, thread, user, "now break it down by product")
        db.refresh(thread)

        assert len(thread.messages) == 4
        last_hex = [m for m in thread.messages if m.role == "hex"][-1]
        assert last_hex.spec["dimension"] == "product", last_hex.spec
        assert last_hex.result["chart"]["type"] == "bar"

        db.delete(thread)
        db.commit()

        print("PASS: analytics ask smoke test")
        print(f"  monthly revenue buckets: {r1['row_count']}, total INR {total:,.0f}")
        print(f"  top products returned:   {r2['row_count']}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
