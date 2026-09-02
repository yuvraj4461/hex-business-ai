"""Deterministic financial calculation engine.

`formulas.py` is a library of pure functions — every standard formula for
time value of money, profitability, liquidity, cash flow, unit economics,
growth, risk/statistics, operations finance, property and market ratios.
Nothing here calls an LLM: the model's job is only to extract inputs and
explain results, never to do the arithmetic.

`engine.py` runs a battery of these against an organization's real ERP
data. `registry.py` describes the formulas for the calculator API.
"""

from app.finance.engine import company_finance

__all__ = ["company_finance"]
