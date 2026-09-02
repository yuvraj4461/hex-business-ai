# SAP BTP integration plan for HEX

**Context.** HEX is FastAPI + PostgreSQL + Next.js + Gemini, on Render/Vercel. The
Hackfest 2026 practice system (SAP BTP, Cloud Foundry) is available **until 15 Sep
2026** and includes HANA Cloud, AI Launchpad / Generative AI Hub, Business
Application Studio, Build Work Zone and Build Lobby. Goal: fold real SAP tech into
HEX for the Hackfest without a rewrite, and keep Render/Vercel as the fallback so a
demo never depends on the practice system being up.

Three integrations, in the order they should be built.

---

## Phase 1 — Route AI through SAP Generative AI Hub

**Why first:** best effort-to-impact. Every AI call already goes through one function
(`app.ai.gemini.generate_text`), so this is a contained change, and it fixes the
503 / rate-limit problem we keep hitting — the Gen AI Hub proxies Anthropic Claude,
OpenAI and Google behind SAP's orchestration with its own capacity.

**Changes**
- Rename `app/ai/gemini.py` → `app/ai/llm.py`; keep `generate_text(prompt)` as the
  public contract and all the resilience logic (retries, model fallback, wall-clock
  budget, deterministic fallback in callers).
- Add a provider layer: `HEX_LLM_PROVIDER = "gemini" | "sap"` (env).
  - `sap` path: OAuth2 client-credentials against the AI Core key's `url`, then
    POST to the orchestration / chat-completion deployment. Use the
    `generative-ai-hub-sdk` (`pip install generative-ai-hub-sdk`) if it installs
    cleanly, otherwise ~40 lines of `requests`.
  - `gemini` path: unchanged.
- No changes at any call site (`copilot`, `agent_synthesis`, `analytics.narrator`,
  `finance` narrator, `decision_agent`) — they all call `generate_text`.
- `/copilot/ai-status` reports which provider answered.

**What I need from you (BTP cockpit)**
1. Subaccount → **Instances and Subscriptions** → create an **SAP AI Core** instance
   (plan usually `sap-internal` or `standard` in the practice tenant) → create a
   **service key** → send me its JSON (`clientid`, `clientsecret`, `url`,
   `AI_API_URL` / `serviceurls.AI_API_URL`).
2. In **AI Launchpad** (or via the API), confirm there is a **deployment** of a chat
   model in the `default` resource group — tell me the `deployment-id` and model
   name (e.g. `anthropic--claude-3.5-sonnet`, `gpt-4o`, `gemini-1.5-pro`). If none
   exists, AI Launchpad → *Generative AI Hub → Deployments → Create*.

**Effort:** ~half a day once the key + deployment id are in hand.

---

## Phase 2 — HANA Cloud as an ERP data source

**Why:** HEX's core pitch is "connect to a company's ERP and extract its data." The
practice HANA instance is pre-filled with sample data. A `HanaCloudAdapter` in the
integration layer lets HEX ingest that data through the existing
land → normalize → canonical-tables pipeline — demonstrating the integration layer
on genuine SAP data instead of seeded Postgres.

**Changes**
- `pip install hdbcli` (SAP's official driver; binary wheels exist for Windows/Linux).
- `app/sources/hana_adapter.py` — a `SourceAdapter` subclass modelled on
  `sql_source.py`: opens an `hdbcli` connection from `connection.credentials`
  (`host`, `port`, `user`, `password`), runs one parameterised `SELECT` per entity
  from `connection.config["queries"]`, yields rows into `raw_records`.
- Register `"hana_cloud"` in `app/sources/registry.py`.
- The existing per-entity **normalizers** + `connection.config["mapping"]` already
  handle column-name differences — no new normalizer code, just a mapping per entity
  once we see the schema.
- Frontend Integrations page: add "SAP HANA Cloud" as a source type (reuse the SQL
  config form; add fields for the 4 connection values + a per-entity query box).
- `backend/test_hana_adapter.py` — smoke test against the live instance.

**Discovery step (before coding the mapping):** connect to the instance, list
schemas/tables, and see what the sample data actually is (sales orders? procurement?
SFLIGHT?). That determines which HEX entities we can populate (suppliers, products,
orders, purchase_orders, materials…) and the `SELECT`s.

**What I need from you (BTP cockpit)**
1. Subaccount → **SAP HANA Cloud** → the running instance → **Actions → Open in SAP
   HANA Database Explorer** (to browse the schema), and **SQL Endpoint** (host:port)
   from the instance overview.
2. A database user with read access — either the `DBADMIN` credentials you set when
   the instance was created, or a new restricted user. Send me host, port (usually
   `443`), user, password.
3. Confirm the instance **allow-lists** connections from outside BTP (HANA Cloud →
   instance → *Connections* → allowed IPs — set to `0.0.0.0/0` for the demo, or add
   the Render egress range).

**Effort:** ~1 day, most of it schema discovery + writing the per-entity `SELECT`s
and mappings.

---

## Phase 3 — Deploy the backend to Cloud Foundry (optional, do last)

**Why:** removes the Render free-tier cold-start 503s and the "Postgres expires
~22 Sep" problem for the duration of the Hackfest. **Temporary** — the practice CF
space also dies on 15 Sep, so Render stays the permanent home and the fallback.

**Changes**
- `backend/manifest.yml` — `python_buildpack`, `command: python bootstrap.py &&
  uvicorn main:app --host 0.0.0.0 --port $PORT`, memory `512M`.
- `backend/runtime.txt` — `python-3.13.x` (match `.python-version`).
- Bind a database: either the Phase-2 HANA instance (add a SQLAlchemy-HANA dialect —
  more work) **or** a BTP **PostgreSQL, hyperscaler option** instance (keeps the
  current SQLAlchemy code, just a new `DATABASE_URL`). Recommend Postgres to avoid a
  dialect port.
- Env vars → CF env (`cf set-env`) or a user-provided service; `GEMINI_API_KEY` /
  SAP AI key, `JWT_SECRET_KEY`, `HEX_CRON_TOKEN`, `FRONTEND_URL`.
- `db_bootstrap` self-migration already works unchanged.
- Point Vercel's `NEXT_PUBLIC_API_URL` at the CF route (or keep Render and treat CF
  as a second environment).
- Add the CF route to the CORS regex in `main.py`.

**What I need from you**
1. `cf login` details: **API endpoint** (subaccount → overview → *Cloud Foundry
   Environment → API Endpoint*), org, space.
2. A **PostgreSQL, hyperscaler option** service instance created in the space (or
   tell me to bind HANA and I'll do the dialect work).
3. Whether you want CF to *replace* Render or run *alongside* it (recommend
   alongside — CF for the SAP-story demo, Render as the stable link).

**Effort:** ~1 day, mostly BTP console + `cf` CLI on your side; I write the manifest
and wire the bindings.

---

## Suggested schedule (13 days)

| Days | Work |
|---|---|
| 1–2 | Phase 1 (AI provider) — needs the AI Core key + deployment id |
| 3–5 | Phase 2 (HANA adapter) — schema discovery, then the adapter + UI |
| 6–7 | Phase 3 (Cloud Foundry) — if time; otherwise skip, Render is fine |
| rest | polish, the demo script, screenshots for the deck |

## Fallback guarantee

Every phase is behind a flag or an additive adapter. `HEX_LLM_PROVIDER=gemini`,
no HANA connection configured, and the Render deploy all keep working exactly as
today if any SAP service is down during judging.
