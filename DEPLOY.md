# Deploying HEX

Backend + Postgres on **Render**, frontend on **Vercel**. Both free tier.

---

## 1. Backend + database — Render

### Option A: Blueprint (recommended)

1. Render dashboard → **New → Blueprint** → connect `yuvraj4461/hex-business-ai`.
2. Render reads [`render.yaml`](render.yaml) and creates:
   - `hex-db` — free Postgres
   - `hex-api` — Docker web service built from [`backend/Dockerfile`](backend/Dockerfile)
   - `DATABASE_URL`, `JWT_SECRET_KEY`, `HEX_SECRET_KEY` are wired automatically.
3. First deploy runs `python bootstrap.py` (creates the schema on the fresh DB)
   then `uvicorn`.
4. Once it's live, in the `hex-api` service → **Environment**:
   - `GEMINI_API_KEY` = your Google AI Studio key (AI features need it; the app
     still runs without it and degrades gracefully).
   - `FRONTEND_URL` = your Vercel URL (fill in after step 2). Comma-separate
     multiple.
5. Health check: `https://hex-api-XXXX.onrender.com/health` → `{"status":"ok"}`.

### Option B: existing Render Postgres

If your earlier Render database (`hex_postgres_9wqp`) still exists, skip the
blueprint's DB: create just the web service, set `DATABASE_URL` to that DB's
**Internal Connection String**. `bootstrap.py` detects the existing tables and
runs only the new migrations.

### Seed data (fresh DB only)

A fresh DB has no users. From the Render service **Shell**:

```bash
python demo_data/generate_demo_data.py     # demo orgs + transactions/orders/etc.
python demo_data/generate_routes.py
python demo_data/seed_business_exposure.py
# create a login:
python -c "from app.database.connection import SessionLocal; from app.models.user import User; from app.models.organization import Organization; from app.security.auth import hash_password; d=SessionLocal(); o=d.query(Organization).first(); d.add(User(organization_id=o.id, name='Admin', email='admin@hex.com', password_hash=hash_password('changeme'), role='SUPER_ADMIN')); d.commit()"
```

Or just hit `POST /auth/register` from the deployed `/docs` to make a new org.

---

## 2. Frontend — Vercel

1. Vercel → **Add New → Project** → import `yuvraj4461/hex-business-ai`.
2. **Root Directory:** `frontend`  (important — it's a monorepo).
3. Framework preset: **Next.js** (auto-detected).
4. **Environment Variables:**
   - `NEXT_PUBLIC_API_URL` = `https://hex-api-XXXX.onrender.com` (your Render URL,
     no trailing slash). This is baked in at build time.
5. Deploy. Then go back to Render and set `FRONTEND_URL` to the Vercel URL, so
   CORS allows it. (`*.vercel.app` preview URLs are already allowed by regex.)

---

## 3. Known limitations of this deploy

| Area | Behaviour | Fix for production |
|---|---|---|
| Render free web service | Sleeps after 15 min idle; first request after is slow. Background auto-sync doesn't run while asleep. | Paid instance, or an external cron pinging `/health`. |
| Render free Postgres | Expires ~90 days after creation. | Paid Postgres or another provider (Neon, Supabase). |
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
