# HEX — presentation Q&A prep

Likely judge / audience questions, with tight answers you can say out loud.
The single strongest line to keep coming back to:

> **"The language model never does the maths. Every number in HEX comes from
> tested Python. The AI only translates the question and explains the result."**

---

## Problem & value

**Q: Who is this for?**
Any company that moves physical goods — a manufacturer, a distributor, a retailer,
a food brand. Anyone whose costs and revenue are exposed to shipping lanes,
tariffs, FX and commodity prices.

**Q: What's the actual pain you're solving?**
Two disconnected worlds. Your operational data is locked in an ERP. External risk
lands in the news. Connecting the two — "how does *this event* hit *my* suppliers
and margins" — needs a data analyst and days of work, every single time. Most
people in the business never get an answer.

**Q: Why now?**
ERP integration APIs (Merge, etc.) made the data reachable, and LLMs made the
natural-language layer possible. But you can't trust an LLM with numbers, so the
interesting engineering is keeping it *out* of the calculation path.

**Q: How big is the market?**
Every mid-market company with a supply chain — that's the SAP customer base. It
overlaps supply-chain risk (Everstream, Interos), FP&A (Pigment, Cube) and
self-serve analytics (ThoughtSpot, Hex.tech), but none of those tie a live global
event to your specific P&L.

---

## "Isn't this just ChatGPT on a database?"

**Q: What stops this from being ChatGPT + a SQL connection?**
Three things. (1) The LLM can't touch the numbers — it emits a validated query
spec or reads a pre-computed result; a deterministic engine does the arithmetic.
(2) A 5-agent pipeline computes finance, sales, operations, world-watch and risk
findings from verified data before the LLM ever sees the question. (3) A corridor
model maps a news event to your actual shipping lanes. ChatGPT-on-a-DB gives you
confident wrong answers; HEX gives you an auditable one.

**Q: What if the LLM hallucinates?**
It structurally can't hallucinate a figure. For "revenue by month" it produces
`{metric: revenue, dimension: month}` — validated against a fixed vocabulary — and
SQLAlchemy runs the query. For the finance agent, 48 tested formulas run in
Python. If the LLM returns something off-vocabulary, we fall back to a
deterministic keyword parser. The *prose* can be imperfect; the *numbers* can't.

**Q: What happens when Gemini is down / rate-limited?**
Every AI call has retry-on-503, model fallback and a wall-clock budget. If it
still fails, the answer degrades to a deterministic executive summary built from
the same agent findings — slower and plainer, never an error. We demoed on a free
key that 503s constantly; the product stays up.

---

## Technical / architecture

**Q: Walk me through what happens when I ask a question.**
The API classifies it. If it's clearly about your data ("revenue by month"), a
deterministic planner builds the query — no LLM — and it answers in ~85 ms. If
it's a reasoning question, the agent graph runs (each agent pulls verified data
and its own context), live web research runs in parallel, then Gemini does *one*
synthesis pass over the computed findings.

**Q: Why a multi-agent graph and not one prompt?**
Separation of concerns and fault isolation. Each agent owns one lens and its own
data. If the world-watch agent fails, the finance answer still lands. And the user
can choose which agents to consult.

**Q: What's the stack?**
FastAPI + PostgreSQL + SQLAlchemy/Alembic + LangGraph on the backend, Next.js 16 /
React 19 / Tailwind on the frontend, Google Gemini for language. Deployed on
Render + Vercel with a GitHub Actions cron for the real-time intelligence.

**Q: The finance engine — what's in it?**
48 pure formulas: time value of money, margins, liquidity, cash flow, unit
economics, growth, risk statistics, operations finance, property and market
ratios. Each returns the value *plus the formula and inputs used*, so any number
is auditable. There's a calculator page exposing all 48.

---

## Data & trust

**Q: How do I know the numbers are right?**
Open the Finance page — every metric shows its formula and inputs. The finance
agent's findings carry the same. It's designed to be checked, not trusted
blindly.

**Q: Your dashboard shows "operating margin" not "gross margin" — why?**
Honesty about the data. The ERP schema has selling prices, not cost of goods, and
no balance sheet. So we compute operating margin and label the cash figure as a
proxy, rather than invent a gross margin. We only show what the data actually
supports — no fake marketing or HR dashboards.

**Q: Where does the "global event" data come from?**
GDELT for geopolitical and disaster news (severity-scored), the Frankfurter API
for FX (a >2% move raises an alert), and Google/SerpApi for tariffs and prices.
Refreshed every 20 minutes.

---

## Integration reality

**Q: How would a real company connect their ERP?**
Three ways today: upload CSV/Excel exports, point HEX at a read-replica database
with one SELECT per entity, or the Merge.dev unified API which covers 50+
accounting and commerce systems. The layer is source-agnostic — a new source is
one adapter class.

**Q: Does it work with SAP?**
The integration layer is built exactly for that — SAP HANA or S/4 would be another
adapter. We had an SAP HANA Cloud instance in the Hackfest practice tenant but
couldn't get usable credentials out of it in time, so the demo runs on uploaded
data. The architecture doesn't care about the source.

**Q: How long to onboard a real customer?**
With a Merge connection, minutes. With a database connection, an afternoon to map
their table names — the normalizers already handle the column differences.

---

## Scale, security, production

**Q: Is this multi-tenant?**
Every query is scoped to an `organization_id`, credentials are Fernet-encrypted at
rest, and there's an append-only audit log. Full row-level-security isolation is
the next step for true SaaS.

**Q: What breaks at scale?**
The agent pipeline is sequential per request — we'd parallelise the independent
agents and cache context (partly done). The real-time collectors are already
scheduled and idempotent. Postgres is fine to a few thousand orgs; beyond that,
read replicas.

**Q: Security review — anything sensitive?**
Connection credentials encrypted, never logged or returned. JWT auth, six roles
with explicit permissions. The LLM only ever receives computed aggregates and the
question, never raw customer records.

---

## Differentiation

**Q: SAP Analytics Cloud already does dashboards.**
SAC shows you *what* happened. HEX tells you *what a specific external event will
do to you* and *what to do about it* — with a route-decision recommendation and a
human approval step. Different job.

**Q: Palantir does supply-chain risk.**
At six-figure implementations. HEX is a self-serve product a mid-market finance or
ops lead can run themselves.

---

## The project

**Q: How long did this take / team size?**
Solo, about a week. ~45 commits.

**Q: What would you build next?**
Live Merge onboarding, an agentic analytics notebook (SQL/Python cells an agent
writes and runs), a governance layer for business definitions, and RLS tenant
isolation.

**Q: What are you most proud of?**
The discipline of keeping the LLM out of the numbers. It would have been faster to
just prompt Gemini with the data — and it would have been a demo that lies. Every
figure here is one you can audit.

---

## If the demo glitches

- **Slow first response:** "Free-tier cold start — the instance was asleep."
- **"Language model busy":** "That's the free Gemini tier 503-ing — notice it still
  answered from the deterministic engine."
- **A number looks odd:** open the Finance page and show the formula + inputs.
