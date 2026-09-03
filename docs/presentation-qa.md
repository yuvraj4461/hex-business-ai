# HEX — presentation Q&A (full)

Every component, the questions that will come at it, and honest answers. Part 2 is
the weaknesses — know them before a judge finds them.

**The anchor line — repeat it whenever numbers/AI come up:**
> The language model never does the maths. Every number in HEX comes from tested
> Python. The AI only turns the question into a structured request and explains the
> result.

---

# PART 1 — Component by component

## 1. The problem & the product

**Q: One sentence — what is HEX?**
HEX connects to a company's ERP, watches the outside world, and turns any global
event into concrete supplier, route, cost and revenue exposure for that specific
business — and lets anyone ask the data a plain-language question.

**Q: Who's the user?**
A finance or operations lead at a mid-market company that moves physical goods.
Today they wait days for an analyst to answer "how does X affect us."

**Q: What does a session look like?**
Connect the ERP → HEX ingests suppliers, orders, shipments, costs → the agent
graph produces findings → a global event (say a Red Sea closure) shows up in the
feed → Risk Center projects the exposure → Scenarios compares route options →
they approve a decision, which is logged.

---

## 2. Architecture

**Q: Draw the architecture.**
Next.js frontend on Vercel → FastAPI backend on Render → PostgreSQL. Inside the
backend: an integration layer (adapters → raw-record landing zone → normalizers →
canonical tables), a LangGraph 5-agent graph, a World Watch collector pipeline on
a 20-minute schedule, and two deterministic engines — `app/analytics` for
querying and `app/finance` for formulas. Gemini sits at the edge as a thin
translate-and-explain layer.

**Q: Why FastAPI / SQLAlchemy / LangGraph specifically?**
FastAPI: async, typed request/response, free OpenAPI docs. SQLAlchemy 2.0 +
Alembic: typed ORM and versioned migrations that run automatically on deploy.
LangGraph: a real state graph — explicit nodes, edges, shared state, and per-node
fault isolation — not a prompt chain.

**Q: Where's the AI in the request path, exactly?**
For a data question: the deterministic planner tries first; the LLM is only called
if the phrasing is ambiguous. For a Copilot reasoning question: agents compute
findings from verified data, then Gemini does **one** synthesis pass over those
findings. Never in the arithmetic.

---

## 3. Data model

**Q: What's the schema?**
32 PostgreSQL tables, every row scoped to an `organization_id`. Commercial
(customers, products, orders, order_items, transactions, expenses), supply chain
(suppliers, supply_routes, purchase_orders + lines, shipments, inventory,
locations, product_materials), intelligence (global_events, market_signals,
agriculture_signals, commodity_forecasts, business_exposures), platform
(connections, raw_records, data_threads, scenarios, recommendations, audit_logs).

**Q: How do you trace a number back to its source?**
A `SourceTrackedMixin` puts `source_connection_id`, `source_external_id` and
`synced_at` on every ingested row. Any figure traces to the connection and the
external record it came from.

---

## 4. Authentication & roles

**Q: How's auth done?**
JWT. Six roles — Super Admin, Data Admin, Analyst, Business User, Decision Maker,
External Partner — each with an explicit permission set (`manage_data`,
`run_analysis`, `approve_recommendations`, `view_audit_logs`, …). Every endpoint
declares the permission it needs.

**Q: Can a Business User run a simulation but not approve it?**
Yes — that's the Decision Maker's `approve_recommendations` permission. The
scenario approve/reject buttons are gated on it.

---

## 5. Integration layer

**Q: How does a company connect its ERP?**
Three source types: upload CSV/Excel, a SQL read-replica (one SELECT per entity,
`:since` bind for incremental), or the Merge.dev unified API for 50+ accounting
and commerce systems. It's source-agnostic — a new source is one adapter class
implementing `fetch`.

**Q: What happens on a sync?**
`fetch` → land every record verbatim in `raw_records` with a content hash →
normalize with a per-entity normalizer using the connection's column mapping →
upsert into the canonical table → advance the cursor. Per-record savepoints, an
audit-log row, and it never raises.

**Q: How are foreign keys resolved — a PO's supplier?**
By a synced external id if present, else by name match against already-synced
suppliers. That's why `supplier.csv` and `product.csv` sync before POs and
shipments (there's a fixed `SYNC_ORDER`).

**Q: Idempotent?**
Yes — the content hash means re-syncing the same file inserts nothing. Verified in
`test_ingestion.py` and `test_demo_data.py`.

**Q: How are credentials protected?**
Fernet-encrypted at rest in `connections.credentials_encrypted`. The API only ever
returns a `has_credentials` boolean. Never logged.

**Q: What about data quality — bad rows?**
Each record has its own savepoint, so one malformed row fails alone and the sync
continues. A failure count is in the sync result and the audit log.

---

## 6. The 5-agent graph

**Q: What are the five agents and why that order?**
finance → sales → operations → world-watch → risk. Finance sets the money
baseline, sales adds demand, operations reads supply against it, world-watch adds
live disruption, and risk runs last so it can weigh everything.

**Q: What does the Finance Agent actually do?**
Runs the deterministic finance engine — a battery of formulas against real data —
then raises threshold recommendations: thin operating margin (<10%), revenue
contraction (MoM ≤ −10%), volatile revenue (coefficient of variation ≥ 50%),
short runway (<6 months), weak LTV:CAC (<3), below break-even. It does no
arithmetic itself.

**Q: The Sales Agent?**
Order volume, average order value, completion and cancellation rates, revenue
trend, best/worst products — from orders and order_items.

**Q: The Operations Agent?**
Reads supply capacity (inventory, routes, open POs) against demand signals; flags
where supply won't meet forecast demand.

**Q: The World Watch Agent?**
Takes the last 48h of high-severity events and FX shocks, matches them to the
org's active corridors via the keyword matcher, and produces `world_watch`
findings plus `active_disruption` / `price_shock` recommendations.

**Q: The Risk Agent?**
Synthesises: affected routes, revenue at risk, cost impact, an overall risk
score. It reads the earlier agents' findings and the exposure engine's output.

**Q: What if one agent crashes?**
Each is wrapped in a node that catches the exception, records `FAILED` in
`agent_runs`, and lets the graph continue. Four agents' findings beat a 500.

**Q: Can the user control which agents run?**
Yes — the Copilot's "Consult" chips. The graph and the grounding both respect the
subset.

---

## 7. World Watch — real-time intelligence

**Q: What are the data sources?**
GDELT DOC 2.0 for geopolitical and disaster news (classified and severity-scored),
the Frankfurter API for FX (USD/EUR/CNY vs INR; a >2% move raises an FX_SHOCK),
and SerpApi/Tavily web search for tariffs, freight and price shocks.

**Q: How often does it run?**
Every 20 minutes — an APScheduler job in the app plus a GitHub Actions cron that
also keeps the free Render instance warm.

**Q: How is "severity" decided?**
A keyword scorer over the headline and event type — "blockade", "missile",
"strike" push it to HIGH/CRITICAL. It's deliberately simple and auditable, not an
ML model.

**Q: What feeds the exposure recompute?**
After each collection run, for every org, it recomputes exposure against any new
HIGH/CRITICAL event.

**Q: How do you keep the feed clean?**
Each run prunes stale GDELT noise (UNKNOWN severity, old GENERAL articles), the
feed endpoint filters out generic categories and dedupes by normalised title.

---

## 8. Exposure engine

**Q: How does a news event become a rupee figure?**
`geo_exposure.event_affects()` checks the event's region/title/type against
corridor keywords — Red Sea, Suez, Hormuz, Malacca, Panama, Taiwan, Black Sea,
Air — and against whether the event's country is an origin/destination of any org
route. If it matches, `recompute_exposure()` rebuilds `business_exposures` from
the open shipments on the affected lanes, with a route-level fallback for lanes
with no shipment yet.

**Q: What if the event doesn't touch the org?**
HEX says so explicitly — "no exposure to your supply chain" — instead of showing
empty ₹0 cards. That was a real fix after a Japan event showed ₹0 confusingly.

**Q: How is the corridor of a lane determined?**
`infer_corridors()` — origin and destination country map to a corridor
(China→India via sea ⇒ Red Sea / Cape). Heuristic, not a routing engine.

---

## 9. Scenarios

**Q: What does "run a scenario" do?**
`run_event_scenario(event_id)` calls the same core analysis as the Red Sea demo:
detected event, exposure, route alternatives, financial trade-off, an AI
recommendation, and a human approve/reject. Works for any event, not just the
seeded one.

**Q: Where do the route alternatives come from?**
The route optimizer offers the standard fallbacks for the affected corridor —
Cape of Good Hope, Air Freight — each with a transit time and freight cost, and
compares them against the current revenue at risk.

**Q: What does "approve" do?**
Writes a `recommendation` + an `audit_logs` row. HEX is decision *support* —
nothing is executed.

---

## 10. Shipments

**Q: Where do shipments come from?**
Two ways: ingested from a source, or **derived** — `project_shipments` creates one
shipment per open PO (route = supplier→destination lane, ETA = order date + lead
time). You saw this in the demo — uploading 4 shipments produced more.

---

## 11. Deterministic finance engine

**Q: What's in `app/finance`?**
48 pure formulas across 10 categories: time value of money (FV, PV, CAGR, NPV,
IRR, payback, loan payment), profitability, liquidity, cash flow, unit economics,
growth, risk statistics (stdev, coefficient of variation, Sharpe, Sortino, max
drawdown, beta), operations finance (break-even, EOQ, reorder point, turnover),
property (cap rate, cash-on-cash), market ratios (dividend yield, P/E, PEG).

**Q: How is it "trustable"?**
Every function raises a clean error on undefined input instead of returning NaN,
and `company_finance` returns each metric **with the formula string and the inputs
used**. The Finance page shows exactly that. There's a calculator exposing all 48.

**Q: The agent uses this?**
Yes — the Finance Agent calls `company_finance` and reads the numbers. It does no
arithmetic and the LLM never sees a raw calculation.

---

## 12. Ask Your Data

**Q: How does "revenue by month" work without SQL?**
A semantic layer defines 9 metrics × ~10 dimensions. The planner turns the
question into `{metric, dimension, filters}` — deterministically for clear
phrasing, via Gemini only for vague phrasing — validated against that vocabulary.
A safe executor builds parameterised SQLAlchemy, always filtered by
`organization_id`, with a hard row cap. Then a narrator writes the sentence
(deterministic by default).

**Q: How fast?**
~85 ms for a deterministic-path question — no LLM round-trip.

**Q: Follow-ups?**
The thread stores each turn; the next question gets the previous query spec, so
"break it down by category" patches it. Threads persist in the database.

**Q: Can it write arbitrary SQL?**
No — that's the point. The LLM can only pick from a fixed vocabulary; a
deterministic builder writes the query. No injection surface.

---

## 13. Analytics dashboard

**Q: What's on the Analytics page?**
Five tabbed sections — Financial, Sales, Customer, Product, Operations — each a row
of KPI tiles and themed charts, all from `GET /analytics/overview` which reuses
the Ask-Your-Data executor plus a few direct queries for cohort metrics.

**Q: Why only five sections?**
Those are what the ERP data supports. No marketing, HR or competitor section —
there's no data for them, and a fake dashboard is worse than none.

---

## 14. AI Copilot

**Q: How does it decide how to answer?**
It classifies the question. Off-topic ("who is X") → a short "here's what I can
help with". A clear financial fact on the first turn → a verified summary, no LLM.
Anything else → the agent graph + (if the question is outward-looking) live web
research + one Gemini synthesis pass.

**Q: Multi-turn memory?**
The last 8 turns are sent with each question so it resolves "why?" and "compare to
last quarter". Client-side for now.

**Q: Web research — when and how?**
Only when the question mentions something external (price, tariff, market,
country…). SerpApi Google results plus a Wikipedia summary for definitional
questions. Gated so an internal question doesn't pull a tangential article.

**Q: The "Consult" chips?**
Choose which specialist agents run. Pick Finance + Risk for a fast focused
answer; the grounding drops the other agents' data too.

---

## 15. Gemini integration & resilience

**Q: Which model?**
`gemini-3.6-flash` by default, with a fallback chain (flash-latest → 2.5 → 2.0) —
Google retired the 2.x models for new keys, so the client probes and caches
whichever works.

**Q: What happens on a 503 / rate limit?**
Retry the same model with backoff, then fall through to the next model, all under
a wall-clock budget. If everything fails, callers use a deterministic fallback —
a clean executive summary from the agent findings.

**Q: Why not OpenAI or Claude?**
Gemini's free tier let us build without a card. The client is abstracted — adding
another provider is contained. Single-provider dependency is a known weakness (see
Part 2).

---

## 16. Deployment

**Q: How's it deployed?**
Backend on Render (native Python 3.13) with PostgreSQL; it self-migrates on
startup (`alembic upgrade head` in the lifespan), so a deploy needs no manual DB
step. Frontend on Vercel, auto-deploys on push. World Watch on a GitHub Actions
cron. `render.yaml` recreates the whole environment.

---

## 17. Frontend & design system

**Q: What's the design language?**
A dark "command-center" instrument-panel theme. Violet accent. Severity is
meaningful — four tones mapped from any backend status string, never hand-picked.
`Panel` with a severity rail, `IntelCard` for bounded scrolling regions, mono
tabular numbers with Indian-format currency.

**Q: Charting?**
Themed Recharts wrappers — bar, area, stacked-severity — with colours from one
token file so light and dark stay consistent.

---

# PART 2 — Weaknesses (say these before a judge does)

## Data model gaps

- **No cost of goods sold in the schema.** So no true *gross* margin, and
  inventory turnover / GMROI are approximations. We compute *operating* margin and
  label it honestly.
- **No balance sheet.** "Cash position" is a proxy — cumulative (revenue −
  expenses). No working capital, current ratio, DSCR, or cash-conversion cycle
  from real data (they're in the calculator, not the company battery).
- **No AR/AP aging** → no DSO/DPO.
- **Multi-currency is not converted.** POs come in USD/EUR/INR and amounts are
  summed raw. A mixed-currency org would get a wrong total. FX conversion is
  unbuilt — this is a real bug, not just a limitation.
- **`sales_order` and `bom` uploads have no normalizer** — they land in
  `raw_records` but never reach the canonical tables. Only 8 of the 10 "supported"
  entities actually sync.
- **Uploaded files sit on Render's ephemeral disk** — they're lost on redeploy or
  restart. Re-sync needed. Should be object storage.

## Agents

- **Sequential execution → slow.** The independent agents could run in parallel;
  that's only partly done (shared context is cached, agents aren't parallelised).
- **The "later agents read earlier findings" design is mostly aspirational** —
  finance/sales/operations don't actually consume each other's output; only risk
  does.
- **No memory across runs** — every run starts cold.
- **Recommendations are threshold rules**, not learned. Fine and auditable, but
  not adaptive.
- **"Agentic" is generous** — it's a fixed pipeline, not agents that plan their
  own steps or use tools autonomously.

## World Watch

- **Severity scoring is keyword-based** — crude; a euphemistic headline scores low.
- **No cross-source dedup** — the same story from GDELT and web search becomes two
  events.
- **Web search needs a paid key.** Without SerpApi/Tavily there's no tariff/price
  intelligence.
- **Commodity data is a static World Bank workbook** (annual forecasts), not live
  prices.
- **GDELT times out from some networks** — handled gracefully, but means gaps.
- **FX covers only USD/EUR/CNY→INR.**
- The feed still shows occasional noise despite pruning.

## Exposure engine

- **Corridor matching is keyword-based.** "Strait of Hormuz" matches; a paraphrase
  might not.
- **`infer_corridors` is a country→corridor heuristic**, not a real routing model.
- **No quantitative delay/cost model** — it's largely presence/absence of exposure
  times a multiplier, not a simulation.
- Recompute only fires on 0 rows or an explicit call — exposure can be stale.

## Scenarios

- **Route alternatives are effectively hardcoded** (Cape, Air) with static transit
  and cost, per corridor.
- **The financial trade-off is arithmetic, not optimisation.**
- Recommendation quality depends on Gemini.

## Finance engine

- **`company_finance` wires ~20 of the 48 formulas to real data**; property and
  market ratios are calculator-only.
- **LTV/CAC use rough proxies** — marketing-category spend ÷ customers-in-90-days;
  LTV = AOV × orders-per-customer × operating-margin. Not a cohort model.
- **Break-even uses operating margin as the contribution-margin ratio** — an
  approximation (no variable/fixed cost split in the data).
- **Forecast is naive least-squares** — no seasonality.

## Ask Your Data

- **One dimension at a time** — no pivots ("revenue by product *and* month").
- **Fixed 9-metric vocabulary** — anything outside it can't be answered.
- **"Revenue by supplier country" silently falls back to a total** (no
  Transaction→Supplier link in the schema).
- **Only sum/avg/count** — no median, percentiles, distinct counts.
- The deterministic planner's keyword matching can mis-parse loose phrasing.

## Copilot

- **`is_business_query` and `looks_outward` are regex heuristics** — edge phrasing
  can be misclassified either way.
- **Multi-turn history is client-side**, capped, sent raw — no server-side thread
  like Ask Your Data has.
- **The Red Sea branch and the first-turn financial shortcut are hardcoded special
  cases** — a bit arbitrary.
- Web research quality varies; a tangential result can still slip through.

## AI / Gemini

- **Single provider.** A Google outage = deterministic-only mode. No OpenAI /
  Anthropic / SAP fallback (the abstraction is there; the second provider isn't).
- **Free tier** — rate limits and 503s; the retry logic adds latency when it's
  being throttled.
- **No streaming** — the user waits for the whole answer.
- **No token / cost tracking.**
- The model-fallback chain assumes those model names stay valid; the
  `_working_model` cache is process-global and only clears on restart.

## Security & multi-tenancy

- **No row-level security.** Org isolation is application-level — one buggy query
  without the `organization_id` filter would leak across tenants. RLS is the next
  step.
- **No API rate limiting.**
- **File upload has no virus scan or explicit size cap.**
- **CORS allows all `*.vercel.app`** — permissive for the demo.
- Prompt-injection via the question text is theoretically possible, though the
  LLM's output is constrained to a spec or a summary.

## Testing & ops

- **Smoke scripts, not a suite.** `test_*.py` are manual — not run in CI. Covered:
  finance formulas, analytics executor, ingestion, world-watch pipeline, exposure,
  demo data. **Barely covered:** the agents themselves, the Copilot branching, the
  whole API surface, the entire frontend.
- **No observability** — logging only, no error tracking or APM.
- **Backend auto-deploy is off** — every backend change is a manual Render deploy;
  easy to forget (and often was).
- **Render free tier** — cold starts, sleeping instance, expiring free Postgres.
- Single region, single instance.

## Product / scope

- **"Full business analytics" is overstated** — no marketing, HR, competitor or
  pricing-elasticity analysis, because there's no data for them.
- **Single-user** — no collaboration, comments, sharing, or export.
- **Demo data is synthetic.** Never run against a real company's ERP.
- **Recommendations are advisory only** — no execution (by design, but it caps the
  "agentic" claim).

---

# PART 3 — The hardest questions

**Q: This looks like a lot of surface area for one week. Is any of it real, or is
it all scaffolding?**
The engines are real and tested — the 48 finance formulas, the semantic query
layer, the ingestion pipeline, the exposure recompute all have smoke tests and
work end-to-end on uploaded data. The thin parts are honest: keyword severity
scoring, heuristic corridor matching, proxy metrics where the data is missing. I'd
rather show a working system with labelled approximations than a polished mockup.

**Q: If I connect my real SAP data tomorrow, what breaks?**
Multi-currency totals (no FX conversion), and any analysis that needs COGS or a
balance sheet degrades to a proxy. Ingestion, the agents, Ask Your Data and the
finance engine work — they only need the entities we already model. Mapping your
table names is an afternoon.

**Q: Why should I trust a number on the screen?**
Don't — check it. The Finance page shows the formula and inputs for every metric.
That's the design: auditable, not authoritative.

**Q: What's the one thing you'd fix first with more time?**
Row-level security for real multi-tenancy, then multi-currency conversion, then
parallelising the agents and moving uploads to object storage.

**Q: What are you proudest of?**
Keeping the LLM out of the arithmetic. The fast path would have been to prompt
Gemini with the data — and it would have been a demo that lies. Every figure here
is one you can audit.

---

## Demo-glitch recovery lines

- Slow first response → "Free-tier cold start — the instance was asleep."
- "Language model busy" → "Free Gemini tier 503-ing — notice it still answered
  from the deterministic engine."
- A number looks wrong → open the Finance page, show the formula and inputs.
- Web result looks off-topic → "Web grounding is best-effort; the business numbers
  next to it are exact."
