"""Pure financial formulas. No I/O, no LLM — just math.

Every function raises ``FinanceError`` on undefined input (e.g. a zero
denominator) so callers can surface a clean message instead of a crash or
a silent NaN. Percentages are returned as percentages (e.g. 12.5, not
0.125) unless the name says ``_ratio``.
"""

from __future__ import annotations

import math
from statistics import mean, pstdev, stdev


class FinanceError(ValueError):
    """A formula could not be evaluated with the given inputs."""


def _nonzero(value: float, what: str) -> float:
    if value == 0:
        raise FinanceError(f"{what} must not be zero")
    return value


def _series(values) -> list[float]:
    out = [float(v) for v in values if v is not None]
    if not out:
        raise FinanceError("series is empty")
    return out


# ======================================================================
# 1. Time value of money
# ======================================================================

def future_value(present_value: float, rate: float, periods: float) -> float:
    """FV = PV x (1 + r)^n."""
    return float(present_value) * (1 + float(rate)) ** float(periods)


def present_value(future_value: float, rate: float, periods: float) -> float:
    """PV = FV / (1 + r)^n."""
    return float(future_value) / (1 + float(rate)) ** float(periods)


def cagr(beginning_value: float, ending_value: float, years: float) -> float:
    """Compound annual growth rate, as a percent.

    CAGR = (Ending / Beginning)^(1/n) - 1
    """
    b = _nonzero(float(beginning_value), "beginning value")
    n = _nonzero(float(years), "years")
    if b < 0 or float(ending_value) < 0:
        raise FinanceError("CAGR needs non-negative values")
    return ((float(ending_value) / b) ** (1 / n) - 1) * 100


def npv(rate: float, cash_flows: list[float]) -> float:
    """Net present value. cash_flows[0] is the period-0 flow (usually
    the negative initial outlay).

    NPV = sum( CF_t / (1 + r)^t )
    """
    r = float(rate)
    return sum(float(cf) / (1 + r) ** t for t, cf in enumerate(_series(cash_flows)))


def irr(cash_flows: list[float], guess: float = 0.1) -> float:
    """Internal rate of return, as a percent — the rate where NPV = 0.

    Solved by bisection on [-99%, +1000%]; raises if no sign change.
    """
    flows = _series(cash_flows)
    if len(flows) < 2:
        raise FinanceError("IRR needs at least two cash flows")

    def f(r: float) -> float:
        return sum(cf / (1 + r) ** t for t, cf in enumerate(flows))

    lo, hi = -0.9999, 10.0
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0:
        raise FinanceError("no IRR in range — cash flows may not change sign")
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = f(mid)
        if abs(f_mid) < 1e-9:
            return mid * 100
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return ((lo + hi) / 2) * 100


def payback_period(initial_investment: float, cash_flows: list[float]) -> float:
    """Years to recover the initial investment from a stream of equal-period
    inflows (linear interpolation within the final year)."""
    remaining = abs(float(initial_investment))
    for i, cf in enumerate(_series(cash_flows), start=1):
        cf = float(cf)
        if cf >= remaining:
            return (i - 1) + remaining / _nonzero(cf, "cash flow")
        remaining -= cf
    raise FinanceError("investment is not recovered by the given cash flows")


def loan_payment(principal: float, annual_rate: float, months: float) -> float:
    """Level monthly payment on an amortising loan.

    A = P x r / (1 - (1 + r)^-n),  r = monthly rate
    """
    p = float(principal)
    n = _nonzero(float(months), "months")
    r = float(annual_rate) / 12
    if r == 0:
        return p / n
    return p * r / (1 - (1 + r) ** -n)


def rule_of_72(rate_percent: float) -> float:
    """Approximate years to double: 72 / rate(%)."""
    return 72 / _nonzero(float(rate_percent), "rate")


# ======================================================================
# 2. Profitability & margins
# ======================================================================

def gross_margin(revenue: float, cogs: float) -> float:
    """(Revenue - COGS) / Revenue, percent."""
    rev = _nonzero(float(revenue), "revenue")
    return (rev - float(cogs)) / rev * 100


def operating_margin(operating_income: float, revenue: float) -> float:
    """Operating income / Revenue, percent."""
    return float(operating_income) / _nonzero(float(revenue), "revenue") * 100


def net_margin(net_income: float, revenue: float) -> float:
    """Net income / Revenue, percent."""
    return float(net_income) / _nonzero(float(revenue), "revenue") * 100


def markup(price: float, cost: float) -> float:
    """(Price - Cost) / Cost, percent."""
    return (float(price) - float(cost)) / _nonzero(float(cost), "cost") * 100


def contribution_margin(price: float, variable_cost: float) -> float:
    """Price - variable cost, per unit (currency)."""
    return float(price) - float(variable_cost)


def contribution_margin_ratio(price: float, variable_cost: float) -> float:
    """(Price - variable cost) / Price, percent."""
    p = _nonzero(float(price), "price")
    return (p - float(variable_cost)) / p * 100


def roi(gain: float, cost: float) -> float:
    """(Current value - Cost) / Cost, percent.  Pass gain = current value."""
    c = _nonzero(float(cost), "cost")
    return (float(gain) - c) / c * 100


def roas(revenue: float, ad_spend: float) -> float:
    """Revenue / Ad spend — a ratio (e.g. 4.0 = ₹4 back per ₹1)."""
    return float(revenue) / _nonzero(float(ad_spend), "ad spend")


def return_on_assets(net_income: float, total_assets: float) -> float:
    """Net income / Total assets, percent."""
    return float(net_income) / _nonzero(float(total_assets), "total assets") * 100


def return_on_equity(net_income: float, shareholders_equity: float) -> float:
    """Net income / Shareholders' equity, percent."""
    return float(net_income) / _nonzero(float(shareholders_equity), "equity") * 100


# ======================================================================
# 3. Liquidity & solvency
# ======================================================================

def current_ratio(current_assets: float, current_liabilities: float) -> float:
    return float(current_assets) / _nonzero(
        float(current_liabilities), "current liabilities"
    )


def quick_ratio(
    current_assets: float, inventory: float, current_liabilities: float
) -> float:
    """(Current assets - Inventory) / Current liabilities."""
    return (float(current_assets) - float(inventory)) / _nonzero(
        float(current_liabilities), "current liabilities"
    )


def working_capital(current_assets: float, current_liabilities: float) -> float:
    """Current assets - Current liabilities (currency)."""
    return float(current_assets) - float(current_liabilities)


def debt_to_equity(total_debt: float, shareholders_equity: float) -> float:
    return float(total_debt) / _nonzero(float(shareholders_equity), "equity")


def debt_service_coverage_ratio(
    net_operating_income: float, total_debt_service: float
) -> float:
    """NOI / Total debt service.  Below 1.0 means income can't cover debt."""
    return float(net_operating_income) / _nonzero(
        float(total_debt_service), "debt service"
    )


def interest_coverage_ratio(ebit: float, interest_expense: float) -> float:
    return float(ebit) / _nonzero(float(interest_expense), "interest expense")


# ======================================================================
# 4. Cash flow
# ======================================================================

def free_cash_flow(operating_cash_flow: float, capital_expenditure: float) -> float:
    """Operating cash flow - CapEx (currency)."""
    return float(operating_cash_flow) - float(capital_expenditure)


def burn_rate(starting_cash: float, ending_cash: float, months: float) -> float:
    """Average monthly net cash consumed (currency/month, positive = burning).

    Burn = (Starting cash - Ending cash) / months
    """
    return (float(starting_cash) - float(ending_cash)) / _nonzero(
        float(months), "months"
    )


def runway_months(cash_balance: float, monthly_burn: float) -> float:
    """Months of cash left = balance / monthly burn.  Infinite if not burning."""
    b = float(monthly_burn)
    if b <= 0:
        return math.inf
    return float(cash_balance) / b


def cash_conversion_cycle(dio: float, dso: float, dpo: float) -> float:
    """Days inventory outstanding + days sales outstanding - days payables
    outstanding."""
    return float(dio) + float(dso) - float(dpo)


# ======================================================================
# 5. Unit economics
# ======================================================================

def cac(sales_and_marketing_spend: float, customers_acquired: float) -> float:
    """Customer acquisition cost = S&M spend / new customers (currency)."""
    return float(sales_and_marketing_spend) / _nonzero(
        float(customers_acquired), "customers acquired"
    )


def customer_lifetime_value(
    avg_order_value: float,
    purchase_frequency: float,
    gross_margin_pct: float,
    lifespan_periods: float,
) -> float:
    """LTV = AOV x purchase frequency x gross margin x lifespan (currency)."""
    return (
        float(avg_order_value)
        * float(purchase_frequency)
        * (float(gross_margin_pct) / 100)
        * float(lifespan_periods)
    )


def ltv_cac_ratio(ltv: float, cac: float) -> float:
    """LTV : CAC.  Target is usually > 3."""
    return float(ltv) / _nonzero(float(cac), "CAC")


def cac_payback_months(cac: float, monthly_gross_margin_per_customer: float) -> float:
    """Months to recover CAC from per-customer margin."""
    return float(cac) / _nonzero(
        float(monthly_gross_margin_per_customer), "monthly margin per customer"
    )


def churn_rate(customers_lost: float, customers_at_start: float) -> float:
    """Customers lost / customers at start, percent."""
    return float(customers_lost) / _nonzero(
        float(customers_at_start), "customers at start"
    ) * 100


def retention_rate(
    customers_at_end: float, new_customers: float, customers_at_start: float
) -> float:
    """((End - New) / Start) x 100, percent."""
    return (float(customers_at_end) - float(new_customers)) / _nonzero(
        float(customers_at_start), "customers at start"
    ) * 100


# ======================================================================
# 6. Growth & trend
# ======================================================================

def growth_rate(previous: float, current: float) -> float:
    """(Current - Previous) / |Previous|, percent.  Works for MoM / YoY."""
    p = _nonzero(float(previous), "previous value")
    return (float(current) - p) / abs(p) * 100


def average_growth(series: list[float]) -> float:
    """Geometric mean of period-over-period growth, percent."""
    s = _series(series)
    if len(s) < 2 or s[0] <= 0:
        raise FinanceError("need >= 2 positive values")
    ratios = [s[i] / s[i - 1] for i in range(1, len(s)) if s[i - 1] > 0]
    if not ratios:
        raise FinanceError("cannot compute growth")
    geo = math.prod(ratios) ** (1 / len(ratios))
    return (geo - 1) * 100


def moving_average(series: list[float], window: int) -> list[float]:
    s = _series(series)
    w = int(window)
    if w < 1 or w > len(s):
        raise FinanceError("window out of range")
    return [sum(s[i - w + 1 : i + 1]) / w for i in range(w - 1, len(s))]


def linear_forecast(series: list[float], periods_ahead: int = 1) -> float:
    """Least-squares trend value ``periods_ahead`` steps past the series end."""
    s = _series(series)
    n = len(s)
    if n < 2:
        raise FinanceError("need >= 2 points")
    xs = list(range(n))
    x_mean, y_mean = mean(xs), mean(s)
    denom = sum((x - x_mean) ** 2 for x in xs)
    slope = 0.0 if denom == 0 else sum(
        (x - x_mean) * (y - y_mean) for x, y in zip(xs, s)
    ) / denom
    intercept = y_mean - slope * x_mean
    return slope * (n - 1 + int(periods_ahead)) + intercept


# ======================================================================
# 7. Risk & statistics
# ======================================================================

def average(series: list[float]) -> float:
    return mean(_series(series))


def standard_deviation(series: list[float], sample: bool = True) -> float:
    s = _series(series)
    if sample and len(s) < 2:
        raise FinanceError("sample stdev needs >= 2 values")
    return stdev(s) if sample else pstdev(s)


def coefficient_of_variation(series: list[float]) -> float:
    """Stdev / mean, percent — dispersion normalised by level."""
    s = _series(series)
    m = _nonzero(mean(s), "mean")
    return standard_deviation(s) / abs(m) * 100


def returns_series(values: list[float]) -> list[float]:
    """Period-over-period simple returns (ratios) from a level series."""
    s = _series(values)
    return [s[i] / s[i - 1] - 1 for i in range(1, len(s)) if s[i - 1] != 0]


def volatility(returns: list[float]) -> float:
    """Standard deviation of returns, percent."""
    return standard_deviation(returns) * 100


def sharpe_ratio(returns: list[float], risk_free_rate: float = 0.0) -> float:
    """(mean return - risk-free) / stdev of returns."""
    r = _series(returns)
    sd = _nonzero(standard_deviation(r), "return stdev")
    return (mean(r) - float(risk_free_rate)) / sd


def sortino_ratio(returns: list[float], risk_free_rate: float = 0.0) -> float:
    """Like Sharpe but only penalises downside deviation."""
    r = _series(returns)
    downside = [x for x in r if x < float(risk_free_rate)]
    if len(downside) < 2:
        raise FinanceError("not enough downside observations")
    dd = _nonzero(pstdev(downside), "downside deviation")
    return (mean(r) - float(risk_free_rate)) / dd


def max_drawdown(series: list[float]) -> float:
    """Largest peak-to-trough decline, percent (returned as a negative number)."""
    s = _series(series)
    peak = s[0]
    worst = 0.0
    for v in s:
        peak = max(peak, v)
        if peak > 0:
            worst = min(worst, (v - peak) / peak)
    return worst * 100


def z_score(value: float, mean_: float, stdev_: float) -> float:
    return (float(value) - float(mean_)) / _nonzero(float(stdev_), "stdev")


def beta(asset_returns: list[float], market_returns: list[float]) -> float:
    """Cov(asset, market) / Var(market)."""
    a, m = _series(asset_returns), _series(market_returns)
    if len(a) != len(m) or len(a) < 2:
        raise FinanceError("need equal-length series of >= 2")
    a_mean, m_mean = mean(a), mean(m)
    cov = sum((x - a_mean) * (y - m_mean) for x, y in zip(a, m)) / (len(a) - 1)
    var = sum((y - m_mean) ** 2 for y in m) / (len(m) - 1)
    return cov / _nonzero(var, "market variance")


# ======================================================================
# 8. Operations finance
# ======================================================================

def break_even_units(
    fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float
) -> float:
    cm = _nonzero(
        float(price_per_unit) - float(variable_cost_per_unit),
        "contribution margin",
    )
    return float(fixed_costs) / cm


def break_even_revenue(
    fixed_costs: float, contribution_margin_ratio_pct: float
) -> float:
    return float(fixed_costs) / _nonzero(
        float(contribution_margin_ratio_pct) / 100, "contribution margin ratio"
    )


def inventory_turnover(cogs: float, average_inventory: float) -> float:
    return float(cogs) / _nonzero(float(average_inventory), "average inventory")


def days_inventory_outstanding(
    average_inventory: float, cogs: float, days: int = 365
) -> float:
    return float(average_inventory) / _nonzero(float(cogs), "COGS") * int(days)


def days_sales_outstanding(
    average_receivables: float, revenue: float, days: int = 365
) -> float:
    return float(average_receivables) / _nonzero(float(revenue), "revenue") * int(days)


def days_payables_outstanding(
    average_payables: float, cogs: float, days: int = 365
) -> float:
    return float(average_payables) / _nonzero(float(cogs), "COGS") * int(days)


def economic_order_quantity(
    annual_demand: float, order_cost: float, holding_cost_per_unit: float
) -> float:
    """EOQ = sqrt(2 D S / H)."""
    return math.sqrt(
        2 * float(annual_demand) * float(order_cost)
        / _nonzero(float(holding_cost_per_unit), "holding cost")
    )


def reorder_point(
    average_daily_usage: float, lead_time_days: float, safety_stock: float = 0.0
) -> float:
    return float(average_daily_usage) * float(lead_time_days) + float(safety_stock)


def gmroi(gross_margin_amount: float, average_inventory_cost: float) -> float:
    """Gross margin return on inventory investment."""
    return float(gross_margin_amount) / _nonzero(
        float(average_inventory_cost), "average inventory cost"
    )


# ======================================================================
# 9. Property
# ======================================================================

def cap_rate(net_operating_income: float, market_value: float) -> float:
    """NOI / Market value, percent."""
    return float(net_operating_income) / _nonzero(
        float(market_value), "market value"
    ) * 100


def cash_on_cash_return(
    annual_pre_tax_cash_flow: float, total_cash_invested: float
) -> float:
    """Annual pre-tax cash flow / total cash invested, percent."""
    return float(annual_pre_tax_cash_flow) / _nonzero(
        float(total_cash_invested), "cash invested"
    ) * 100


# ======================================================================
# 10. Market ratios
# ======================================================================

def dividend_yield(annual_dividends_per_share: float, price_per_share: float) -> float:
    return float(annual_dividends_per_share) / _nonzero(
        float(price_per_share), "price"
    ) * 100


def pe_ratio(price_per_share: float, earnings_per_share: float) -> float:
    return float(price_per_share) / _nonzero(float(earnings_per_share), "EPS")


def earnings_yield(earnings_per_share: float, price_per_share: float) -> float:
    return float(earnings_per_share) / _nonzero(float(price_per_share), "price") * 100


def peg_ratio(pe_ratio_value: float, earnings_growth_pct: float) -> float:
    return float(pe_ratio_value) / _nonzero(
        float(earnings_growth_pct), "earnings growth"
    )
