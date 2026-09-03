# HEX — demo questions & flow

Questions that show HEX off well. Anything about the business's finances, sales,
customers, suppliers, inventory, routes or global risk works; below are the ones
that land cleanly.

---

## Ask Your Data  (`/ask`)

Plain-language questions answered with a number, a chart and the rows. These map
exactly to the semantic layer, so they're instant and never wrong.

**Openers**
- `revenue by month`
- `top 5 products by revenue`
- `expenses by category`
- `which suppliers have the longest lead times?`
- `units sold by product category`
- `profit over time`
- `average order value by month`
- `how many orders in 2026?`
- `inventory on hand by category`
- `revenue by supplier country`

**Follow-ups** (type after any answer — it refines the previous query)
- `break it down by category`
- `only completed orders`
- `just the last 6 months`
- `top 3 instead`
- `for 2026 only`

---

## AI Copilot  (`/copilot`)

Reasoned answers. Runs the specialist agents, grounds numbers in the deterministic
engines, adds live web research only when the question is about the outside world.

**About the business**
- `what is the biggest risk to my business right now?`
- `is my revenue trend healthy?`
- `how much cash runway do I have?`
- `are my margins okay?`
- `what's driving my expenses this quarter?`
- `summarise my current supplier exposure`
- `which of my suppliers is most concerning?`
- `what should I do about the revenue decline?`

**Multi-turn** (ask one, then a follow-up)
- `what is my operating margin?`  →  `why is it that level?`  →  `what should I do?`
- `how are we doing this quarter?`  →  `how does that compare to last quarter?`

**Agent selection** — toggle the *Consult* chips
- Pick **Finance + Risk** only, ask `give me a quick health assessment`
- Pick **World Watch** only, ask `any disruptions on my routes?`

**Outside-world (shows live web grounding + sources)**
- `how would a Red Sea disruption affect my costs?`
- `what are current steel tariffs?`
- `what's the price of cotton right now?`

**Off-topic (shows the guard)**
- `who is akshay kumar` → HEX politely declines and says what it *can* help with

---

## Finance  (`/finance`)

**Company metrics tab** — every figure shows the formula and inputs used.

**Calculator tab** — pick a formula, plug numbers, exact result:
- `CAGR` — 1,00,000 → 2,50,000 over 3 years
- `NPV` — rate 0.1, cash flows `-1000000 400000 400000 400000 400000`
- `Break-even (Revenue)` — fixed costs 5,00,000, contribution margin ratio 40
- `LTV : CAC` — 9000 / 3000
- `Sharpe Ratio` — returns `0.05 0.15 0.10 0.20 0.00`, risk-free 0
- `Cap Rate` — NOI 50,00,000, market value 10,00,00,000

---

## Risk Center & Scenarios

1. **Risk Center** → pick **"Simulated Red Sea shipping disruption"** → *Analyze business impact*.
2. See revenue at risk, affected routes, exposed suppliers/products.
3. **View full scenario** → route alternatives (Cape of Good Hope, Air), financial
   trade-off, AI recommendation → **Approve / Reject** (writes to the Audit Log).

---

## Suggested 4-minute demo flow

| # | Screen | Say / do |
|---|---|---|
| 1 | **Integrations** | "HEX connects to your ERP." Upload the Aurora Foods CSVs, hit Sync, show Data Readiness. |
| 2 | **Analytics** | Tab through Financial → Sales → Operations. "All computed from that data." |
| 3 | **Ask Your Data** | Type `top 5 products by revenue`, then `break it down by category`. "No SQL, no analyst." |
| 4 | **Global Intelligence** | Show the live feed / incident chart. "Real-time GDELT, FX and web search." |
| 5 | **Risk Center** | Analyze the Red Sea event → exposure appears. |
| 6 | **Scenarios** | View full scenario → route alternatives + recommendation → Approve. |
| 7 | **AI Copilot** | `what is the biggest risk to my business right now?` — show it cites the finance engine + agents. Toggle to Finance-only, ask again. |
| 8 | **Finance** | Calculator: run a CAGR or break-even. "The finance agent uses this — no LLM does the maths." |

**One-liner:** *HEX turns any global event into supplier, route, cost and revenue
exposure for your specific business — and lets anyone ask the data a question.*
