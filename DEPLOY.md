# Deploying HEX

Backend + Postgres on **Render**, frontend on **Vercel**. Both free tier.

---

## 1. Backend — update the existing Render service

You already have **`hex-business-ai backend`** (native Python 3, free) and
**`hex-postgres`** (free, expires ~Sept 22). Update in place — don't run the
blueprint (it would make a duplicate).

### `hex-business-ai backend` → Settings

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python bootstrap.py && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Auto-Deploy | **re-enable it** (currently off) so pushes to `main` deploy |

### → Environment  (add these; keep the ones you have)

| Key | Value |
|---|---|
| `HEX_SECRET_KEY` | a Fernet key — `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"` |
| `FRONTEND_URL` | `https://hex-business-ai.vercel.app` (your Vercel **production** URL, no slash) |
| `GEMINI_MODEL` | `gemini-3.6-flash` (or a model your key has quota for) |
| `HEX_SCHEDULER_ENABLED` | `true` |
| `WEB_CONCURRENCY` | `1` |

Then **Manual Deploy → Deploy latest commit**.

`bootstrap.py` runs first: your DB has the 26 base tables but no Alembic
history, so it runs every migration (all additive — adds the `connections`,
`raw_records`, `purchase_orders`, `shipments` tables and provenance columns
to the existing ones). Your existing data is kept.

### `render.yaml`

[`render.yaml`](render.yaml) documents these same settings and can recreate the
services from scratch if the free DB expires. [`backend/Dockerfile`](backend/Dockerfile)
also works if you switch the service runtime to Docker.

### Seed / reset a login

From the Render service **Shell**:

```bash
# reset the admin password if you don't know it
python -c "from app.database.connection import SessionLocal; from app.models.user import User; from app.security.auth import hash_password; d=SessionLocal(); u=d.query(User).filter(User.email=='admin@hex.com').first(); u.password_hash=hash_password('hexdemo123'); d.commit(); print('done')"
```

For a fresh DB with no data, from the **Shell**:

```bash
python demo_data/generate_demo_data.py     # demo orgs + transactions/orders/etc.
python demo_data/generate_routes.py
python demo_data/seed_business_exposure.py
# create a login:
python -c "from app.database.connection import SessionLocal; from app.models.user import User; from app.models.organization import Organization; from app.security.auth import hash_password; d=SessionLocal(); o=d.query(Organization).first(); d.add(User(organization_id=o.id, name='Admin', email='admin@hex.com', password_hash=hash_password('changeme'), role='SUPER_ADMIN')); d.commit()"
```

Or just hit `POST /auth/register` from the deployed `/docs` to make a new org.

---

## 1b. World Watch — real-time intelligence cron

The backend collects GDELT events + FX + web-search news on a schedule.
On the free tier it only runs while the instance is awake, so an external
cron covers the gaps (and keeps it warm).

1. Render `hex-api` **Environment**: set `HEX_CRON_TOKEN` (any long random
   string) and — for the web-search agent — `TAVILY_API_KEY`
   ([tavily.com](https://tavily.com), free ~1000 searches/mo). Without the
   Tavily key the price/tariff/inflation search is skipped; GDELT + FX still run.
2. GitHub repo → **Settings → Secrets and variables → Actions**:
   - `HEX_API_URL` = `https://hex-business-ai-backend.onrender.com`
   - `HEX_CRON_TOKEN` = the same value you set on Render
3. The [`.github/workflows/world-watch.yml`](.github/workflows/world-watch.yml)
   workflow then POSTs `/intelligence/refresh` every 20 min. Run it once
   manually (**Actions → World Watch → Run workflow**) to verify.
4. Check `GET /intelligence/status` and the **Global Intelligence → Live Feed**
   page.

(cron-job.org works too — POST to `/intelligence/refresh` with header
`X-HEX-Cron-Token: <token>`.)

## 2. Frontend — Vercel (already set up)

The `hex-business-ai` Vercel project auto-deploys from `main` and is live at
`hex-business-ai.vercel.app`. It has one env var, `NEXT_PUBLIC_API_URL` —
confirm it is exactly `https://hex-business-ai-backend.onrender.com` (no
trailing slash). If you change it, **redeploy** (it's baked in at build time).

Preview URLs (`*.vercel.app`) are already allowed by the backend's CORS regex,
so the "Failed to fetch" on login goes away once the backend is redeployed
with the new code.

---

## 3. Known limitations of this deploy

| Area | Behaviour | Fix for production |
|---|---|---|
| Render free web service | Sleeps after 15 min idle; first request after is a ~50s cold start. Background auto-sync doesn't run while asleep. | Paid instance, or an external cron pinging `/health`. |
| Render free Postgres | Expires 30 days after creation (yours: ~Sept 22). | Paid Postgres or another provider (Neon, Supabase). |
| Uploaded files | Stored on the container's ephemeral disk — lost on every redeploy. Normalised data survives in Postgres; raw payloads survive in `raw_records`. | Object storage (S3/R2) behind the file-upload adapter. |
| Gemini | Rate-limited on free quota; copilot/scenario answers fall back to a non-AI summary. | A key with quota. |
| Auth | JWT in `localStorage`, no rate limiting. | Add rate limiting (`slowapi`), consider httpOnly cookies. |
| SQL connector | Dials arbitrary user-supplied DB hosts. | Egress allowlist before exposing to untrusted users. |
| `bcrypt`/`passlib` | Harmless "error reading bcrypt version" log line on startup. | Cosmetic; passlib 1.7.4 vs bcrypt 4.x. |

---

## Local development

```bash
# DB
docker compose up -d                       # Postgres on :5432

# backend
cd backend
python -m venv venv && venv/Scripts/pip install -r requirements.txt
cp .env.example .env                        # fill DATABASE_URL etc.
python bootstrap.py
venv/Scripts/uvicorn main:app --reload

# frontend
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
