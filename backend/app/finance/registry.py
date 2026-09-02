"""Describes the formula library for the calculator API — which formulas
exist, their inputs, and how to render the answer."""

from __future__ import annotations

from dataclasses import dataclass

from app.finance import formulas as F


@dataclass(frozen=True)
class Param:
    name: str
    label: str
    kind: str = "number"  # "number" | "percent" | "currency" | "series"


@dataclass(frozen=True)
class Formula:
    key: str
    label: str
    category: str
    unit: str  # "percent" | "ratio" | "currency" | "number" | "months" | "years"
    description: str
    fn: callable
    params: tuple[Param, ...]


def _p(*args) -> tuple[Param, ...]:
    return tuple(args)


FORMULAS: dict[str, Formula] = {}


def _add(f: Formula) -> None:
    FORMULAS[f.key] = f


# --- Time value of money -------------------------------------------------
_add(Formula("future_value", "Future Value", "Time Value of Money", "currency",
             "What money today is worth after n periods at rate r.",
             F.future_value,
             _p(Param("present_value", "Present value", "currency"),
                Param("rate", "Rate per period", "percent"),
                Param("periods", "Periods"))))
_add(Formula("present_value", "Present Value", "Time Value of Money", "currency",
             "What future money is worth today.",
             F.present_value,
             _p(Param("future_value", "Future value", "currency"),
                Param("rate", "Rate per period", "percent"),
                Param("periods", "Periods"))))
_add(Formula("cagr", "CAGR", "Time Value of Money", "percent",
             "Compound annual growth rate between two values.",
             F.cagr,
             _p(Param("beginning_value", "Beginning value", "currency"),
                Param("ending_value", "Ending value", "currency"),
                Param("years", "Years"))))
_add(Formula("npv", "Net Present Value", "Time Value of Money", "currency",
             "Discounted value of a cash-flow stream (index 0 = initial outlay).",
             F.npv,
             _p(Param("rate", "Discount rate", "percent"),
                Param("cash_flows", "Cash flows", "series"))))
_add(Formula("irr", "Internal Rate of Return", "Time Value of Money", "percent",
             "The discount rate at which NPV = 0.",
             F.irr,
             _p(Param("cash_flows", "Cash flows", "series"))))
_add(Formula("payback_period", "Payback Period", "Time Value of Money", "years",
             "Time to recover an initial investment.",
             F.payback_period,
             _p(Param("initial_investment", "Initial investment", "currency"),
                Param("cash_flows", "Inflows per period", "series"))))
_add(Formula("loan_payment", "Loan Payment", "Time Value of Money", "currency",
             "Level monthly payment on an amortising loan.",
             F.loan_payment,
             _p(Param("principal", "Principal", "currency"),
                Param("annual_rate", "Annual rate", "percent"),
                Param("months", "Months"))))

# --- Profitability -----------------------------------------------------
_add(Formula("gross_margin", "Gross Margin", "Profitability", "percent",
             "(Revenue - COGS) / Revenue.",
             F.gross_margin,
             _p(Param("revenue", "Revenue", "currency"),
                Param("cogs", "Cost of goods sold", "currency"))))
_add(Formula("operating_margin", "Operating Margin", "Profitability", "percent",
             "Operating income / Revenue.",
             F.operating_margin,
             _p(Param("operating_income", "Operating income", "currency"),
                Param("revenue", "Revenue", "currency"))))
_add(Formula("net_margin", "Net Margin", "Profitability", "percent",
             "Net income / Revenue.",
             F.net_margin,
             _p(Param("net_income", "Net income", "currency"),
                Param("revenue", "Revenue", "currency"))))
_add(Formula("roi", "Return on Investment", "Profitability", "percent",
             "(Current value - Cost) / Cost.",
             F.roi,
             _p(Param("gain", "Current value", "currency"),
                Param("cost", "Cost", "currency"))))
_add(Formula("roas", "Return on Ad Spend", "Profitability", "ratio",
             "Revenue generated per unit of ad spend.",
             F.roas,
             _p(Param("revenue", "Attributed revenue", "currency"),
                Param("ad_spend", "Ad spend", "currency"))))
_add(Formula("markup", "Markup", "Profitability", "percent",
             "(Price - Cost) / Cost.",
             F.markup,
             _p(Param("price", "Price", "currency"),
                Param("cost", "Cost", "currency"))))
_add(Formula("contribution_margin_ratio", "Contribution Margin Ratio",
             "Profitability", "percent",
             "(Price - Variable cost) / Price.",
             F.contribution_margin_ratio,
             _p(Param("price", "Price", "currency"),
                Param("variable_cost", "Variable cost", "currency"))))

# --- Liquidity & solvency --------------------------------------------
_add(Formula("current_ratio", "Current Ratio", "Liquidity & Solvency", "ratio",
             "Current assets / Current liabilities.",
             F.current_ratio,
             _p(Param("current_assets", "Current assets", "currency"),
                Param("current_liabilities", "Current liabilities", "currency"))))
_add(Formula("quick_ratio", "Quick Ratio", "Liquidity & Solvency", "ratio",
             "(Current assets - Inventory) / Current liabilities.",
             F.quick_ratio,
             _p(Param("current_assets", "Current assets", "currency"),
                Param("inventory", "Inventory", "currency"),
                Param("current_liabilities", "Current liabilities", "currency"))))
_add(Formula("working_capital", "Working Capital", "Liquidity & Solvency",
             "currency", "Current assets - Current liabilities.",
             F.working_capital,
             _p(Param("current_assets", "Current assets", "currency"),
                Param("current_liabilities", "Current liabilities", "currency"))))
_add(Formula("debt_to_equity", "Debt-to-Equity", "Liquidity & Solvency", "ratio",
             "Total debt / Shareholders' equity.",
             F.debt_to_equity,
             _p(Param("total_debt", "Total debt", "currency"),
                Param("shareholders_equity", "Equity", "currency"))))
_add(Formula("debt_service_coverage_ratio", "DSCR", "Liquidity & Solvency", "ratio",
             "Net operating income / Total debt service. < 1 can't cover debt.",
             F.debt_service_coverage_ratio,
             _p(Param("net_operating_income", "Net operating income", "currency"),
                Param("total_debt_service", "Total debt service", "currency"))))
_add(Formula("interest_coverage_ratio", "Interest Coverage",
             "Liquidity & Solvency", "ratio",
             "EBIT / Interest expense.",
             F.interest_coverage_ratio,
             _p(Param("ebit", "EBIT", "currency"),
                Param("interest_expense", "Interest expense", "currency"))))

# --- Cash flow -------------------------------------------------------
_add(Formula("free_cash_flow", "Free Cash Flow", "Cash Flow", "currency",
             "Operating cash flow - CapEx.",
             F.free_cash_flow,
             _p(Param("operating_cash_flow", "Operating cash flow", "currency"),
                Param("capital_expenditure", "CapEx", "currency"))))
_add(Formula("burn_rate", "Burn Rate", "Cash Flow", "currency",
             "Average monthly net cash consumed.",
             F.burn_rate,
             _p(Param("starting_cash", "Starting cash", "currency"),
                Param("ending_cash", "Ending cash", "currency"),
                Param("months", "Months"))))
_add(Formula("runway_months", "Runway", "Cash Flow", "months",
             "Months of cash left at the current burn.",
             F.runway_months,
             _p(Param("cash_balance", "Cash balance", "currency"),
                Param("monthly_burn", "Monthly burn", "currency"))))
_add(Formula("cash_conversion_cycle", "Cash Conversion Cycle", "Cash Flow",
             "number", "DIO + DSO - DPO, in days.",
             F.cash_conversion_cycle,
             _p(Param("dio", "Days inventory outstanding"),
                Param("dso", "Days sales outstanding"),
                Param("dpo", "Days payables outstanding"))))

# --- Unit economics -------------------------------------------------
_add(Formula("cac", "Customer Acquisition Cost", "Unit Economics", "currency",
             "Sales & marketing spend / new customers.",
             F.cac,
             _p(Param("sales_and_marketing_spend", "S&M spend", "currency"),
                Param("customers_acquired", "Customers acquired"))))
_add(Formula("customer_lifetime_value", "Customer Lifetime Value",
             "Unit Economics", "currency",
             "AOV x purchase frequency x gross margin x lifespan.",
             F.customer_lifetime_value,
             _p(Param("avg_order_value", "Average order value", "currency"),
                Param("purchase_frequency", "Purchases per period"),
                Param("gross_margin_pct", "Gross margin", "percent"),
                Param("lifespan_periods", "Lifespan (periods)"))))
_add(Formula("ltv_cac_ratio", "LTV : CAC", "Unit Economics", "ratio",
             "Lifetime value divided by acquisition cost. Target > 3.",
             F.ltv_cac_ratio,
             _p(Param("ltv", "Lifetime value", "currency"),
                Param("cac", "Acquisition cost", "currency"))))
_add(Formula("cac_payback_months", "CAC Payback", "Unit Economics", "months",
             "Months to recover CAC from per-customer margin.",
             F.cac_payback_months,
             _p(Param("cac", "CAC", "currency"),
                Param("monthly_gross_margin_per_customer",
                      "Monthly margin / customer", "currency"))))
_add(Formula("churn_rate", "Churn Rate", "Unit Economics", "percent",
             "Customers lost / customers at start.",
             F.churn_rate,
             _p(Param("customers_lost", "Customers lost"),
                Param("customers_at_start", "Customers at start"))))

# --- Growth & trend ------------------------------------------------
_add(Formula("growth_rate", "Growth Rate", "Growth & Trend", "percent",
             "(Current - Previous) / |Previous|. Use for MoM or YoY.",
             F.growth_rate,
             _p(Param("previous", "Previous", "currency"),
                Param("current", "Current", "currency"))))
_add(Formula("average_growth", "Average Growth", "Growth & Trend", "percent",
             "Geometric mean of period-over-period growth.",
             F.average_growth,
             _p(Param("series", "Value series", "series"))))
_add(Formula("linear_forecast", "Linear Forecast", "Growth & Trend", "number",
             "Least-squares trend value n periods ahead.",
             F.linear_forecast,
             _p(Param("series", "Value series", "series"),
                Param("periods_ahead", "Periods ahead"))))

# --- Risk & statistics -------------------------------------------
_add(Formula("standard_deviation", "Standard Deviation", "Risk & Statistics",
             "number", "Sample standard deviation of a series.",
             F.standard_deviation,
             _p(Param("series", "Value series", "series"))))
_add(Formula("coefficient_of_variation", "Coefficient of Variation",
             "Risk & Statistics", "percent",
             "Stdev / mean — dispersion normalised by level.",
             F.coefficient_of_variation,
             _p(Param("series", "Value series", "series"))))
_add(Formula("volatility", "Volatility", "Risk & Statistics", "percent",
             "Standard deviation of period returns.",
             F.volatility,
             _p(Param("returns", "Return series (ratios)", "series"))))
_add(Formula("sharpe_ratio", "Sharpe Ratio", "Risk & Statistics", "ratio",
             "(Mean return - risk-free) / stdev of returns.",
             F.sharpe_ratio,
             _p(Param("returns", "Return series (ratios)", "series"),
                Param("risk_free_rate", "Risk-free rate (ratio)"))))
_add(Formula("max_drawdown", "Max Drawdown", "Risk & Statistics", "percent",
             "Largest peak-to-trough decline in a series.",
             F.max_drawdown,
             _p(Param("series", "Value series", "series"))))
_add(Formula("beta", "Beta", "Risk & Statistics", "ratio",
             "Cov(asset, market) / Var(market).",
             F.beta,
             _p(Param("asset_returns", "Asset returns", "series"),
                Param("market_returns", "Market returns", "series"))))

# --- Operations finance -----------------------------------------
_add(Formula("break_even_units", "Break-even (Units)", "Operations Finance",
             "number", "Fixed costs / (Price - Variable cost).",
             F.break_even_units,
             _p(Param("fixed_costs", "Fixed costs", "currency"),
                Param("price_per_unit", "Price per unit", "currency"),
                Param("variable_cost_per_unit", "Variable cost per unit",
                      "currency"))))
_add(Formula("break_even_revenue", "Break-even (Revenue)", "Operations Finance",
             "currency", "Fixed costs / Contribution margin ratio.",
             F.break_even_revenue,
             _p(Param("fixed_costs", "Fixed costs", "currency"),
                Param("contribution_margin_ratio_pct", "Contribution margin ratio",
                      "percent"))))
_add(Formula("inventory_turnover", "Inventory Turnover", "Operations Finance",
             "ratio", "COGS / Average inventory.",
             F.inventory_turnover,
             _p(Param("cogs", "COGS", "currency"),
                Param("average_inventory", "Average inventory", "currency"))))
_add(Formula("economic_order_quantity", "Economic Order Quantity",
             "Operations Finance", "number", "sqrt(2 D S / H).",
             F.economic_order_quantity,
             _p(Param("annual_demand", "Annual demand"),
                Param("order_cost", "Cost per order", "currency"),
                Param("holding_cost_per_unit", "Holding cost per unit",
                      "currency"))))
_add(Formula("reorder_point", "Reorder Point", "Operations Finance", "number",
             "Daily usage x lead time + safety stock.",
             F.reorder_point,
             _p(Param("average_daily_usage", "Average daily usage"),
                Param("lead_time_days", "Lead time (days)"),
                Param("safety_stock", "Safety stock"))))

# --- Property --------------------------------------------------
_add(Formula("cap_rate", "Capitalization Rate", "Property", "percent",
             "Net operating income / Market value.",
             F.cap_rate,
             _p(Param("net_operating_income", "Net operating income", "currency"),
                Param("market_value", "Market value", "currency"))))
_add(Formula("cash_on_cash_return", "Cash-on-Cash Return", "Property", "percent",
             "Annual pre-tax cash flow / Total cash invested.",
             F.cash_on_cash_return,
             _p(Param("annual_pre_tax_cash_flow", "Annual pre-tax cash flow",
                      "currency"),
                Param("total_cash_invested", "Total cash invested", "currency"))))

# --- Market ratios --------------------------------------------
_add(Formula("dividend_yield", "Dividend Yield", "Market Ratios", "percent",
             "Annual dividends per share / Price.",
             F.dividend_yield,
             _p(Param("annual_dividends_per_share", "Annual dividend / share",
                      "currency"),
                Param("price_per_share", "Price / share", "currency"))))
_add(Formula("pe_ratio", "P/E Ratio", "Market Ratios", "ratio",
             "Price per share / Earnings per share.",
             F.pe_ratio,
             _p(Param("price_per_share", "Price / share", "currency"),
                Param("earnings_per_share", "EPS", "currency"))))
_add(Formula("peg_ratio", "PEG Ratio", "Market Ratios", "ratio",
             "P/E divided by earnings growth rate.",
             F.peg_ratio,
             _p(Param("pe_ratio_value", "P/E ratio"),
                Param("earnings_growth_pct", "Earnings growth", "percent"))))


CATEGORIES: list[str] = []
for _f in FORMULAS.values():
    if _f.category not in CATEGORIES:
        CATEGORIES.append(_f.category)


def describe() -> list[dict]:
    """Serialisable listing for the frontend calculator."""
    return [
        {
            "key": f.key,
            "label": f.label,
            "category": f.category,
            "unit": f.unit,
            "description": f.description,
            "params": [
                {"name": p.name, "label": p.label, "kind": p.kind}
                for p in f.params
            ],
        }
        for f in FORMULAS.values()
    ]


def evaluate(key: str, inputs: dict) -> float:
    formula = FORMULAS.get(key)
    if formula is None:
        raise F.FinanceError(f"unknown formula {key!r}")

    kwargs: dict = {}
    for p in formula.params:
        if p.name not in inputs or inputs[p.name] in (None, ""):
            # optional-looking trailing params (safety_stock, risk_free_rate,
            # periods_ahead) default in the function signature
            continue
        raw = inputs[p.name]
        if p.kind == "series":
            if isinstance(raw, str):
                raw = [x for x in raw.replace(",", " ").split() if x]
            kwargs[p.name] = [float(x) for x in raw]
        else:
            kwargs[p.name] = float(raw)

    return formula.fn(**kwargs)
