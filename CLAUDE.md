# QueryOptimizer — Project Context

Self-hosted SQL performance workbench for PostgreSQL and SQL Server. Sold at $149 via Lemon Squeezy.

## Stack
- **Backend:** Python FastAPI, port 8000, venv at `backend/.venv`
- **Frontend:** React + Vite + Tailwind, port 5173 dev / 3000 Docker
- **Database:** SQLite at `data/queryoptimizer.db`

## CRITICAL: `redirect_slashes=False` must stay in `backend/main.py`
Without it, `/connections` returns a 307 redirect and the frontend crashes on load.

## Start commands (dev)
```powershell
# Kill anything on 8000 first
(Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess |
  ForEach-Object { Stop-Process -Id $_ -Force }

# Backend
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload

# Frontend
cd frontend
npm run dev
```

## Start commands (Docker / production)
```powershell
docker compose up -d   # serves on port 3000
```

## License system
- Lemon Squeezy generates and emails keys on purchase
- First launch shows Activate screen → user enters key → backend calls LS API
- Key + instance_id stored in SQLite `app_settings` table
- **DEV bypass:** set `LICENSE_KEY=DEV` in `backend/.env` OR run:
  ```sql
  INSERT INTO app_settings(key,value) VALUES('license_key','DEV')
  ON CONFLICT(key) DO UPDATE SET value='DEV';
  ```

## Sales info
- **Checkout:** https://queryoptimizer.lemonsqueezy.com/checkout/buy/50cb7c74-b67d-4058-ba70-4f108cc9f686
- **Landing page:** https://rajeshguntupalli59.github.io/query-optimizer/
- **Support:** queryoptimizer78@gmail.com
- **Price:** $149 one-time, 1 activation per license

## Key files
- `backend/main.py` — FastAPI app (redirect_slashes=False is critical)
- `backend/license.py` — Lemon Squeezy API validation
- `backend/routers/license.py` — GET /api/license, POST /api/license/activate
- `backend/services/db_adapter.py` — `get_adapter(db_type)` → PostgreSQL or MSSQL adapter
- `backend/services/ai_assistant.py` — BYOE AI proxy (openai/anthropic/ollama/azure)
- `backend/database.py` — SQLite bootstrap
- `backend/config.py` — Fernet key loader, AI env vars
- `frontend/src/App.jsx` — license check on load, Activate screen if not licensed
- `frontend/src/components/Activate.jsx` — activation UI
- `frontend/src/components/Settings.jsx` — license status + AI config

## Features (all complete)
1. **EXPLAIN Visualizer** — plan tree, color-coded nodes, auto warnings
2. **Index Advisor** — missing indexes from live pg/MSSQL catalogs
3. **Slow Query Dashboard** — pg_stat_statements / sys.dm_exec_query_stats
4. **Query Rewriter** — 8 rule-based anti-pattern checks
5. **AI Assistant** — BYOE (OpenAI / Anthropic / Ollama / Azure)
6. **Connection Manager** — SQLite-persisted, Fernet-encrypted passwords
7. **Settings UI** — configure AI from browser
8. **License activation** — Lemon Squeezy

## Test credentials (local)
- PostgreSQL 16: port 5432, user=dba, password=dba123, database=shopdb
- SQL Server 2022 Express: localhost\SQLEXPRESS, Windows Auth
- Test DB: shopdb (500 customers, 200 products, 2000 orders, 6000 order_items)

## Bugs fixed (do not reintroduce)
1. `index_advisor.py`: pg_stat_user_indexes columns are `indexrelname` and `relname` (not `indexname`/`tablename`)
2. `index_advisor.py`: `_pg_fk_without_index` — use dict access on RealDictCursor rows, not tuple unpack
3. `db_adapter.py`: MSSQL named instance (`host\INSTANCE`) — don't append TCP port when instance name given

## Packaging
- `build-package.ps1` / `build-package.sh` — builds client ZIP (excludes .venv, node_modules, .git, .claude)
- Client receives ZIP + license key via Lemon Squeezy automatically

## Auto-push hook
Stop hook at `.claude/settings.local.json` auto-commits and pushes after each Claude session.
Script: `.claude/auto-push.ps1`
