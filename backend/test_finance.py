"""Smoke + correctness test for the deterministic finance engine.

    DATABASE_URL=postgresql://... python test_finance.py

Checks formula outputs against hand-computed values, the calculator
registry (incl. series parsing), the company-metrics engine on a seeded
org, and that the finance agent emits a metrics finding.
"""

import math
import sys

import app.ai.gemini as gemini

gemini.is_configured = lambda: False  # type: ignore[assignment]

from app.finance import formulas as F  # noqa: E402
from app.finance.engine import company_finance  # noqa: E402
from app.finance.registry import FORMULAS, evaluate  # noqa: E402
from app.agents.finance_agent import finance_agent  # noqa: E402
from app.database.connection import SessionLocal  # noqa: E402

ORG_ID = 10


def approx(a, b, tol=1e-4):
    return abs(a - b) <= tol * max(1, abs(b))


def test_formulas():
    assert approx(F.future_value(1000, 0.10, 3), 1331.0)
    assert approx(F.present_value(1331, 0.10, 3), 1000.0)
    assert approx(F.cagr(100, 200, 2), 41.42135, 1e-3)
    assert approx(F.npv(0.10, [-1000, 500, 500, 500]), 243.42600, 1e-2)
    assert approx(F.irr([-1000, 500, 500, 500]), 23.375, 1e-1)
    assert approx(F.roi(150, 100), 50.0)
    assert approx(F.gross_margin(1000, 600), 40.0)
    assert approx(F.operating_margin(200, 1000), 20.0)
    assert approx(F.break_even_units(1000, 25, 15), 100.0)
    assert approx(F.cap_rate(50000, 1000000), 5.0)
    assert approx(F.pe_ratio(150, 5), 30.0)
    assert approx(F.growth_rate(100, 90), -10.0)
    assert approx(F.cash_on_cash_return(12000, 100000), 12.0)
    assert approx(F.ltv_cac_ratio(900, 300), 3.0)
    assert approx(F.max_drawdown([100, 120, 60, 90]), -50.0)
    assert F.runway_months(100000, 0) == math.inf
    assert approx(F.rule_of_72(8), 9.0)
    assert approx(F.sharpe_ratio([0.05, 0.15, 0.10, 0.20, 0.00]), 1.264911, 1e-4)
    try:
        F.sharpe_ratio([0.1, 0.1, 0.1])  # zero variance -> undefined
        assert False, "expected FinanceError on constant returns"
    except F.FinanceError:
        pass
    try:
        F.gross_margin(0, 10)
        assert False, "expected FinanceError on zero revenue"
    except F.FinanceError:
        pass
    print("  formulas: OK")


def test_registry():
    out = evaluate("future_value",
                   {"present_value": 1000, "rate": 0.1, "periods": 3})
    assert approx(out, 1331.0)
    # series parsing from a string
    cov = evaluate("coefficient_of_variation", {"series": "10 12 8 14 11"})
    assert cov > 0
    irr = evaluate("irr", {"cash_flows": "-1000, 500, 500, 500"})
    assert approx(irr, 23.375, 1e-1)
    assert len(FORMULAS) >= 30
    print(f"  registry: OK ({len(FORMULAS)} formulas)")


def test_engine(db):
    battery = company_finance(db, ORG_ID)
    h = battery["headline"]
    assert h["revenue"] > 0 and h["months_of_data"] >= 1
    assert abs(h["revenue"] - h["expenses"] - h["profit"]) < 1.0
    for sec in ("profitability", "growth", "cash", "risk",
                "unit_economics", "break_even"):
        assert sec in battery["sections"]
    # every produced metric carries its formula + inputs
    for rows in battery["sections"].values():
        for m in rows:
            assert "formula" in m and "inputs" in m
    assert battery["series"]["revenue_by_month"]
    print(f"  engine: OK (revenue INR {h['revenue']:,.0f}, "
          f"op margin {h['operating_margin_pct']:.1f}%)")


def test_agent(db):
    state = {"organization_id": ORG_ID, "findings": [], "recommendations": []}
    out = finance_agent(state, db)
    types = [f.get("type") for f in out["findings"]]
    assert "finance_metrics" in types
    metrics_finding = next(f for f in out["findings"]
                           if f.get("type") == "finance_metrics")
    assert "sections" in metrics_finding["data"]
    assert isinstance(out["recommendations"], list)
    print(f"  agent: OK ({len(out['findings'])} findings, "
          f"{len(out['recommendations'])} recs)")


def main() -> int:
    test_formulas()
    test_registry()
    db = SessionLocal()
    try:
        test_engine(db)
        test_agent(db)
    finally:
        db.close()
    print("PASS: finance engine test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
