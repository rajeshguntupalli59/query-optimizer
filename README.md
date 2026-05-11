# SQL Query Optimizer

A full-stack DBA tool for PostgreSQL query analysis, index advising, slow query detection, and query rewriting.

## Features

| Feature | Description |
|---|---|
| **EXPLAIN Visualizer** | Run `EXPLAIN` / `EXPLAIN ANALYZE` and view an interactive plan tree with cost breakdown and warnings |
| **Index Advisor** | Detect missing indexes from your SQL (FK columns, WHERE/ORDER BY columns, unindexed tables) |
| **Slow Query Dashboard** | Surface the slowest queries from `pg_stat_statements` with timing histograms |
| **Query Rewriter** | Rule-based analysis: `SELECT *`, leading wildcards, `NOT IN`, `OR`, `OFFSET` anti-patterns, and more |
| **Multi-Connection Manager** | Save and switch between multiple PostgreSQL environments |

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 12+ (target databases)

## Quick Start

### 1. Backend

```bash
cd query-optimizer/backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd query-optimizer/frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Enabling pg_stat_statements (Slow Query tab)

Add to your `postgresql.conf`:

```ini
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

Then restart PostgreSQL and run:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

## Project Structure

```
query-optimizer/
├── backend/
│   ├── main.py                         # FastAPI entry point
│   ├── schemas.py                      # Pydantic models
│   ├── requirements.txt
│   ├── routers/
│   │   ├── connections.py              # CRUD for saved connections
│   │   ├── explain.py                  # EXPLAIN / EXPLAIN ANALYZE
│   │   ├── indexes.py                  # Index recommendations
│   │   ├── slow_queries.py             # pg_stat_statements
│   │   └── rewriter.py                 # Rule-based query rewriting
│   └── services/
│       ├── connection_manager.py       # DB connection pool
│       ├── explain_analyzer.py         # Plan tree parsing + warnings
│       ├── index_advisor.py            # Missing index detection
│       ├── slow_query_detector.py      # Slow query fetching
│       └── query_rewriter.py           # Rewrite rules engine
└── frontend/
    └── src/
        ├── App.jsx                     # Shell + tab routing
        ├── api/client.js               # Axios API wrappers
        └── components/
            ├── ConnectionManager.jsx
            ├── SqlEditor.jsx           # Monaco-based SQL editor
            ├── ExplainPlan.jsx
            ├── IndexAdvisor.jsx
            ├── SlowQueries.jsx
            └── QueryRewriter.jsx
```

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/connections` | List saved connections |
| POST | `/connections` | Add a new connection |
| DELETE | `/connections/{id}` | Remove a connection |
| POST | `/connections/{id}/test` | Test connectivity |
| POST | `/explain` | Run EXPLAIN (ANALYZE) |
| POST | `/indexes/recommend` | Get index recommendations |
| GET | `/slow-queries/{id}` | Fetch slow queries |
| POST | `/slow-queries/{id}/reset` | Reset pg_stat_statements |
| POST | `/rewrite` | Analyze SQL for anti-patterns |

## Security Note

Connection passwords are stored in memory only (no disk persistence). For production use, add encryption at rest (e.g., Fernet key stored in an environment variable) and HTTPS.
