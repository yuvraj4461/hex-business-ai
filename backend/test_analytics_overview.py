"""Smoke test for GET /analytics/overview.

    DATABASE_URL=postgresql://... python test_analytics_overview.py

Calls the endpoint's builder directly against a seeded org and checks
every section has KPIs and chart rows and that the headline figures agree
with a direct recompute.
"""

import sys

import app.ai.gemini as gemini

gemini.is_configured = lambda: False  # type: ignore[assignment]

from app.api.analytics_overview import analytics_overview  # noqa: E402
from app.database.connection import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402

ORG_ID = 10


def main() -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.organization_id == ORG_ID).first()
        assert user is not None, "seeded org needs a user"

        out = analytics_overview(current_user=user, db=db)

        for name in ("financial", "sales", "customers", "products", "operations"):
            section = out[name]
            assert section["kpis"], f"{name} has no KPIs"
            assert all(
                {"label", "value", "unit"} <= k.keys() for k in section["kpis"]
            ), f"{name} KPI shape"
            charts = [v for k, v in section.items() if k != "kpis"]
            assert any(len(c) for c in charts), f"{name} has no chart rows"

        fin = {k["label"]: k["value"] for k in out["financial"]["kpis"]}
        assert abs(fin["Revenue"] - fin["Expenses"] - fin["Profit"]) < 1.0
        assert fin["Revenue"] > 0

        sales_kpis = {k["label"]: k["value"] for k in out["sales"]["kpis"]}
        assert 0 <= sales_kpis["Completion rate"] <= 100
        assert 0 <= sales_kpis["Cancellation rate"] <= 100

        ops = {k["label"]: k["value"] for k in out["operations"]["kpis"]}
        assert ops["Suppliers"] >= 1

        print("PASS: analytics overview smoke test")
        print(f"  revenue INR {fin['Revenue']:,.0f} | profit INR {fin['Profit']:,.0f}")
        print(
            f"  sections OK: financial/sales/customers/products/operations "
            f"({len(out['sales']['top_products'])} top products, "
            f"{len(out['customers']['top_customers'])} top customers)"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
