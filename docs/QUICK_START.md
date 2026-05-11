# QueryOptimizer — Quick Start Reference Card

---

## Install in 3 Steps

```
# 1. Extract the zip archive, then open a terminal in that folder

# 2. Run the installer
Windows:       powershell -ExecutionPolicy Bypass -File setup.ps1
Linux / Mac:   bash setup.sh

# 3. Open your browser
http://localhost:3000
```

---

## Add a Database Connection

1. Click **New** in the left sidebar
2. Select **PostgreSQL** or **SQL Server**
3. Enter host / port / database / username / password
4. Click **Save**, then the **✓ checkmark** to test
5. Click the connection row to activate it

| Database | Default Port |
|---|---|
| PostgreSQL | 5432 |
| SQL Server | 1433 |

> Connecting to `localhost`? Use your machine's **LAN IP** (e.g. `192.168.1.10`), not `localhost`.

---

## Feature Quick Reference

### EXPLAIN Visualizer
```
Paste SQL → toggle ANALYZE if needed → click EXPLAIN

ANALYZE = actually runs the query (don't use on DELETE/UPDATE/INSERT)
BUFFERS = shows I/O stats (PostgreSQL only, requires ANALYZE)
```
**Node colors:** 🔴 Seq Scan (bad) · 🟢 Index Scan (good) · 🟡 Join · 🔵 Other

---

### Index Advisor
```
Paste SQL → click Analyze Indexes
```
Copy the generated `CREATE INDEX` DDL and run it in your DB client.
> Test on a non-production copy first. Index creation locks writes briefly on large tables.

---

### Slow Query Dashboard
```
Set Top N and Min Calls → click Load → click any row for details
```
**PostgreSQL prerequisite** (one-time setup):
```ini
# postgresql.conf
shared_preload_libraries = 'pg_stat_statements'
```
Then restart PostgreSQL and run: `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;`

**SQL Server:** No setup needed — uses `sys.dm_exec_query_stats` (built-in).

---

### Query Rewriter
```
Paste SQL → click Analyze Query   (no DB connection needed)
```
Detects: `SELECT *` · `LIKE '%x'` · `NOT IN (SELECT...)` · `OR` in WHERE · `SELECT DISTINCT` · large `OFFSET` · implicit cross joins · large `IN` lists

---

### AI Assistant
```
Add context (optional) → paste SQL → click Analyze with AI
```
Returns: optimized SQL · explanation · warnings · tuning tips

Requires AI configured in **Settings** (gear icon ⚙, top-right).

---

## Configure AI (Settings ⚙)

| Provider | Endpoint |
|---|---|
| OpenAI | `https://api.openai.com/v1/chat/completions` |
| Anthropic | `https://api.anthropic.com/v1/messages` |
| Ollama (local) | `http://host.docker.internal:11434/api/generate` |
| Azure OpenAI | `https://<resource>.openai.azure.com/openai/deployments/<model>/chat/completions?api-version=2024-02-01` |

---

## Common Fixes

| Problem | Fix |
|---|---|
| App won't open | Check Docker is running: `docker ps` |
| Port conflict | Edit `FRONTEND_PORT` / `BACKEND_PORT` in `.env`, then `docker compose up -d` |
| "Connection refused" to DB | Use LAN IP, not `localhost` |
| Slow Queries — extension missing | See PostgreSQL prerequisite above |
| AI returns no response | Verify API key and endpoint in Settings; check model name |
| Lost all data after restart | Your `data/` folder may have been deleted — back it up regularly |

---

## Manage the Application

```bash
# Stop
docker compose down

# Start
docker compose up -d

# View logs
docker compose logs backend
docker compose logs frontend

# Update to new version
docker compose build && docker compose up -d

# Full reset (deletes all saved connections)
docker compose down && rm -rf data/ && docker compose up -d
```

---

*QueryOptimizer v1.0 · Self-Hosted · Full guide: docs/USER_GUIDE.md*
