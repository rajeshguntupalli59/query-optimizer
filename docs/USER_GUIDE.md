# QueryOptimizer — User Guide

**Version 1.0 · Commercial Self-Hosted Edition**

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Requirements](#2-system-requirements)
3. [Installation](#3-installation)
4. [First-Time Setup](#4-first-time-setup)
5. [Managing Database Connections](#5-managing-database-connections)
6. [EXPLAIN Visualizer](#6-explain-visualizer)
7. [Index Advisor](#7-index-advisor)
8. [Slow Query Dashboard](#8-slow-query-dashboard)
9. [Query Rewriter](#9-query-rewriter)
10. [AI Assistant](#10-ai-assistant)
11. [Settings](#11-settings)
12. [Troubleshooting](#12-troubleshooting)
13. [FAQ](#13-faq)

---

## 1. Overview

**QueryOptimizer** is a self-hosted DBA workbench for diagnosing and improving SQL query performance. It connects directly to your PostgreSQL or Microsoft SQL Server databases and provides five core capabilities:

| Feature | What it does |
|---|---|
| **EXPLAIN Visualizer** | Runs `EXPLAIN` / `EXPLAIN ANALYZE` and renders the execution plan as an interactive tree with cost breakdowns and warnings |
| **Index Advisor** | Analyzes your queries against live catalog data and generates ready-to-run `CREATE INDEX` statements |
| **Slow Query Dashboard** | Surfaces your slowest queries from `pg_stat_statements` (PostgreSQL) or `sys.dm_exec_query_stats` (SQL Server) |
| **Query Rewriter** | Detects SQL anti-patterns — `SELECT *`, leading wildcards, `NOT IN`, large `OFFSET`, and more — without needing a database connection |
| **AI Assistant** | Connects to your own AI endpoint (OpenAI, Anthropic, Ollama, Azure, or any compatible API) for context-aware query rewrites and tuning advice |

**All data stays within your infrastructure.** The tool has no cloud dependency, no telemetry, and no callbacks to the vendor after installation.

---

## 2. System Requirements

### Server running QueryOptimizer

| Requirement | Minimum |
|---|---|
| OS | Windows 10/Server 2019, Ubuntu 20.04+, macOS 12+ |
| CPU | 2 cores |
| RAM | 2 GB |
| Disk | 1 GB (for Docker images + SQLite database) |
| Docker | Docker Desktop 4.0+ (Windows/Mac) or Docker Engine 20.10+ (Linux) |
| Network | Must be able to reach your database servers on the appropriate port |

### Target databases (what you connect TO)

| Database | Supported versions |
|---|---|
| PostgreSQL | 12, 13, 14, 15, 16, 17 |
| Microsoft SQL Server | 2016, 2017, 2019, 2022, Azure SQL |

> **Note:** The Slow Query feature requires `pg_stat_statements` extension for PostgreSQL (see [Section 8](#8-slow-query-dashboard)).

---

## 3. Installation

### Step 1 — Download the package

Extract the `queryoptimizer-v1.0.zip` archive you received to a folder of your choice, for example:

- Windows: `C:\Tools\queryoptimizer\`
- Linux/Mac: `/opt/queryoptimizer/`

### Step 2 — Run the installer

**Windows (PowerShell):**
```powershell
cd C:\Tools\queryoptimizer
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**Linux / macOS (Terminal):**
```bash
cd /opt/queryoptimizer
chmod +x setup.sh
./setup.sh
```

The installer will:
1. Verify Docker is installed and running
2. Create your `.env` configuration file from the template
3. Create the `data/` directory for persistent storage
4. Build the Docker containers (5–10 minutes on first run)
5. Start the application

### Step 3 — Open the application

Once the installer completes, open your browser and navigate to:

```
http://localhost:3000
```

The API documentation (for integrators) is available at:
```
http://localhost:8000/docs
```

### Changing the default ports

Edit the `.env` file before running the installer:

```env
FRONTEND_PORT=8080    # Change from default 3000
BACKEND_PORT=9000     # Change from default 8000
```

### Running on a server (remote access)

If installing on a server that other team members will access, expose the frontend port through your firewall. Team members connect to `http://your-server-ip:3000`.

For production deployments, we recommend placing a reverse proxy (nginx or Caddy) in front and enabling HTTPS.

---

## 4. First-Time Setup

When you open QueryOptimizer for the first time, you will see the **Overview** screen showing the four core features.

**To begin analyzing queries:**

1. **Add a connection** — click **New** in the left sidebar
2. **Select your database type** — PostgreSQL or SQL Server
3. **Fill in your connection details** (host, port, database, username, password)
4. **Test the connection** — click the checkmark icon to verify connectivity
5. **Select the connection** — click the connection row to activate it
6. **Choose a feature tab** from the top navigation

Your connections are **saved to disk** and will still be there after a restart. Passwords are stored encrypted.

---

## 5. Managing Database Connections

### Adding a connection

Click **New** in the sidebar and fill in:

| Field | PostgreSQL default | SQL Server default |
|---|---|---|
| Connection Name | Any label (e.g., "Production DB") | Any label |
| Database Type | PostgreSQL | SQL Server |
| Host | `localhost` | `localhost` |
| Port | `5432` | `1433` |
| Database | your database name | your database name |
| Username | `postgres` | `sa` |
| Password | your password | your password |

> **SQL Server note:** The tool uses the Microsoft ODBC Driver 18 for SQL Server, which is pre-installed inside the Docker container. You do not need to install it separately.

### Testing a connection

Hover over a saved connection and click the **checkmark icon**. A green checkmark confirms success; a red X shows the error message.

### Switching connections

Click any saved connection row to make it the active connection. The active connection is shown in the top-right pill indicator.

### Deleting a connection

Hover over a saved connection and click the **trash icon**.

---

## 6. EXPLAIN Visualizer

**Tab:** EXPLAIN  
**Requires:** An active database connection

The EXPLAIN Visualizer runs PostgreSQL's `EXPLAIN` command or SQL Server's `SET SHOWPLAN_ALL ON` and renders the execution plan as an interactive tree.

### Running an estimated plan

1. Paste your SQL query into the editor
2. Click **EXPLAIN**

This does **not** execute the query — it only asks the database planner to show what it *would* do. Safe to run on production.

### Running an actual plan (ANALYZE mode)

1. Toggle **ANALYZE** (PostgreSQL) or **STATISTICS PROFILE** (SQL Server)
2. Click **EXPLAIN**

> ⚠️ **Warning:** ANALYZE/STATISTICS PROFILE actually executes the query. Do not run destructive statements (`DELETE`, `UPDATE`, `INSERT`) with this toggle enabled, as they will execute against your database.

For PostgreSQL, you can also enable **BUFFERS** alongside ANALYZE to see I/O statistics (shared block hits vs. reads).

### Reading the plan tree

Each row in the tree is a **plan node** — one step the database takes to execute your query. Color coding:

| Color | Meaning |
|---|---|
| 🔴 Red | Sequential Scan — the database is reading an entire table |
| 🟢 Green | Index Scan / Seek — the database is using an index |
| 🟡 Yellow | Join operation |
| 🔵 Blue | Other operations (Sort, Aggregate, etc.) |

**Key metrics per node:**

- `cost=X..Y` — estimated startup cost and total cost (arbitrary planner units)
- `rows=N` — estimated number of rows this node will produce
- `actual Xms, N rows` — shown only with ANALYZE; real execution time and row count

### Automatic warnings

After running EXPLAIN, the tool automatically highlights:

| Warning | What it means |
|---|---|
| **Sequential scan** | The table is being fully scanned. If the table is large, an index would help. |
| **Row estimate off by Nx** | The planner estimated far fewer/more rows than actually returned. Run `ANALYZE` on the table to refresh statistics. |
| **Expensive join** | A Hash Match or Nested Loop join with very high cost. Ensure the join columns are indexed. |
| **Key Lookup** *(SQL Server)* | The non-clustered index doesn't cover all selected columns. Consider adding `INCLUDE` columns to the index. |
| **Table Scan** *(SQL Server)* | Equivalent to a PostgreSQL sequential scan. |

---

## 7. Index Advisor

**Tab:** Index Advisor  
**Requires:** An active database connection

The Index Advisor analyzes your SQL query against the live database catalog to identify missing or ineffective indexes.

### How to use it

1. Paste your SQL query (SELECT, UPDATE, DELETE — anything with a WHERE clause or JOIN)
2. Click **Analyze Indexes**
3. Review the recommendations

### What it checks

| Check | Source |
|---|---|
| Tables with no indexes at all | `pg_stat_user_indexes` / `sys.indexes` |
| Foreign key columns with no supporting index | `information_schema` / `sys.foreign_keys` |
| WHERE clause columns with no index | SQL text analysis + catalog lookup |
| ORDER BY columns with no index | SQL text analysis + catalog lookup |
| Missing indexes flagged by the query optimiser | `sys.dm_db_missing_index_details` *(SQL Server only)* |

### Reading a recommendation

Each card shows:

- **Table and columns** involved
- **Reason** — why this index is recommended
- **Estimated benefit** — High / Medium-High / Medium / Low
- **DDL** — the exact `CREATE INDEX` statement, ready to copy and execute

### Applying a recommendation

Click the **copy icon** on the DDL block to copy the statement. Review it carefully, then run it in your database client during a maintenance window.

> **Important:** Always test index changes on a non-production copy first. Creating an index on a large table acquires a lock that can briefly impact writes.

---

## 8. Slow Query Dashboard

**Tab:** Slow Queries  
**Requires:** An active database connection

The Slow Query Dashboard surfaces your worst-performing queries ranked by average execution time.

### PostgreSQL — enabling pg_stat_statements

Before using this feature with PostgreSQL, the `pg_stat_statements` extension must be installed and enabled.

**Step 1** — Add to `postgresql.conf`:
```ini
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

**Step 2** — Restart PostgreSQL, then run once:
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

**Step 3** — The extension starts collecting data immediately. Wait at least a few minutes of normal workload before using the dashboard for meaningful results.

### SQL Server — no setup required

SQL Server's `sys.dm_exec_query_stats` is always available. No configuration needed.

### Using the dashboard

1. Set **Top N** (how many queries to show, max 100)
2. Set **Min calls** (filter out queries that ran fewer than N times — useful to ignore one-off queries)
3. Click **Load**
4. Click any query row to expand its full details

### Metrics explained

| Metric | Meaning |
|---|---|
| **Calls** | How many times this query has been executed |
| **Mean time** | Average execution time — the primary ranking column |
| **Min / Max time** | Fastest and slowest individual executions |
| **Total time** | Cumulative time spent in this query across all executions |
| **Rows** | Average number of rows returned per execution |
| **Cache hit %** | Percentage of data served from memory vs. disk. Below 90% suggests memory pressure. |

### Resetting statistics

Click **Reset stats** to clear accumulated data and start fresh.

> ⚠️ **Warning (SQL Server):** Reset runs `DBCC FREEPROCCACHE`, which clears the entire plan cache server-wide. This can cause a temporary performance spike as all queries re-compile their execution plans. Use with caution on production servers.

---

## 9. Query Rewriter

**Tab:** Query Rewriter  
**Requires:** No database connection needed

The Query Rewriter performs static analysis on any SQL you paste in, detecting common anti-patterns that hurt performance. It works without a live database connection — useful for reviewing queries before deploying them.

### How to use it

1. Paste your SQL query into the editor
2. Click **Analyze Query**
3. Review the issues found, severity, and suggestions

### Anti-patterns detected

| Anti-pattern | Severity | Why it's a problem |
|---|---|---|
| `SELECT *` | High | Fetches all columns including those you don't need, increasing I/O and memory usage |
| `OR` in `WHERE` clause | High | Prevents index use on either branch; consider `UNION ALL` instead |
| Function applied to indexed column | High | `WHERE LOWER(email) = 'x'` cannot use an index on `email` |
| `LIKE '%value'` leading wildcard | Medium | A leading `%` prevents B-tree index use; consider full-text search |
| `SELECT DISTINCT` | Medium | Forces a sort/hash step; may indicate a join producing duplicates |
| `NOT IN (SELECT ...)` | Medium | Fails silently with NULLs; use `NOT EXISTS` instead |
| Implicit cross join (`FROM a, b`) | Medium | Comma-separated tables create a cartesian product if no WHERE clause ties them |
| Large `IN` list (50+ values) | Low | May cause plan instability; load values into a temp table and JOIN |
| Large `OFFSET` (10,000+) | Low | Forces the database to scan and discard rows; use keyset pagination |

### Severity levels

- **High** — Likely causing a significant performance problem right now
- **Medium** — May cause issues at scale or under certain conditions
- **Low** — Best practice violation; worth addressing before the table grows large

---

## 10. AI Assistant

**Tab:** AI Assistant  
**Requires:** AI endpoint configured in Settings (see [Section 11](#11-settings))

The AI Assistant sends your SQL query to your configured AI endpoint and returns:

- **Optimized query** — a rewritten version of your SQL with explanations of every change
- **What changed & why** — plain-English explanation of the optimizations
- **Warnings** — potential issues the AI identified
- **Tuning tips** — additional advice specific to your query and database type

### How to use it

1. Optionally add **context** in the text field above the editor (e.g., table sizes, known constraints, relevant schema)
2. Paste your SQL into the editor
3. Click **Analyze with AI**

### Providing context

The AI produces significantly better results when given context. Examples:

```
orders table has 80 million rows. customer_id is not indexed.
The query runs every 5 seconds from the application layer.
```

```
This runs on SQL Server 2019. The product table has a full-text index on name.
```

### If AI is not configured

If you see "AI is not configured," click the **Settings** button in the prompt or navigate to Settings via the gear icon in the top-right corner.

---

## 11. Settings

**Access:** Click the **gear icon ⚙** in the top-right corner of the header

### AI Integration

Configure your AI endpoint here. The tool supports any HTTP-based LLM API.

| Field | Description |
|---|---|
| **Provider** | Select your AI provider to auto-fill the endpoint URL and model list |
| **API Endpoint** | The full URL the tool will call |
| **API Key** | Your API token (stored encrypted on your server; never transmitted to the vendor) |
| **Model** | The model name to request |

**Supported providers:**

| Provider | Endpoint example | Notes |
|---|---|---|
| OpenAI | `https://api.openai.com/v1/chat/completions` | Requires `OPENAI_API_KEY` |
| Anthropic | `https://api.anthropic.com/v1/messages` | Requires `ANTHROPIC_API_KEY` |
| Ollama (local) | `http://localhost:11434/api/generate` | No API key needed; runs on your own hardware |
| Azure OpenAI | `https://<resource>.openai.azure.com/openai/deployments/<model>/chat/completions?api-version=2024-02-01` | Use your Azure API key |
| Any OpenAI-compatible API | Your endpoint URL | Use the "Generic" provider option |

> **Privacy note:** The tool sends only the SQL query text (and optional context you type) to your AI endpoint. No database credentials, schema, or query results are ever sent.

### Configuring via `.env` file (alternative)

Instead of using the Settings UI, you can pre-configure AI settings in the `.env` file before starting the application:

```env
AI_PROVIDER=openai
AI_ENDPOINT=https://api.openai.com/v1/chat/completions
AI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4o
```

Settings saved in the UI take precedence over `.env` values.

---

## 12. Troubleshooting

### Application won't start

**Check Docker is running:**
```bash
docker ps
```
If this fails, open Docker Desktop and wait for it to fully start.

**Check port conflicts:**
```bash
# Windows PowerShell
netstat -ano | findstr ":3000"
netstat -ano | findstr ":8000"
```
If another application is using port 3000 or 8000, change the ports in `.env` and restart with `docker compose up -d`.

**View container logs:**
```bash
docker compose logs backend
docker compose logs frontend
```

---

### Cannot connect to database

**"Connection refused"**
- The database host is not reachable from the Docker container
- If connecting to `localhost`, use your machine's LAN IP address instead (e.g., `192.168.1.10`), not `localhost` or `127.0.0.1`, because those resolve to the container itself

**"Password authentication failed"**
- Verify the username and password are correct
- For PostgreSQL, ensure the user has `CONNECT` privilege on the database

**"SSL connection required"** (PostgreSQL)
- Some cloud PostgreSQL providers (e.g., AWS RDS, Google Cloud SQL) require SSL
- Append `?sslmode=require` to your connection or contact support for SSL configuration

**SQL Server: "Named Pipes Provider, error 40"**
- SQL Server is configured to listen on TCP/IP only; verify TCP/IP is enabled in SQL Server Configuration Manager
- Confirm the SQL Server Browser service is running if connecting by instance name

---

### Slow Query tab shows "pg_stat_statements is not enabled"

Follow the setup steps in [Section 8](#8-slow-query-dashboard). After adding `shared_preload_libraries` to `postgresql.conf`, a **full restart** of PostgreSQL is required (not just `pg_reload_conf()`).

---

### EXPLAIN returns an error

Common causes:
- The query has a **syntax error** — verify it runs correctly in your database client first
- The query references a **table or schema you don't have access to**
- The query uses **dollar-quoted strings** or other advanced syntax — ensure your PostgreSQL version supports it

---

### AI Assistant returns "Could not parse AI response"

This usually means the AI endpoint returned text that is not valid JSON. Try:
1. Switching to a model that better follows instruction formats (e.g., `gpt-4o` instead of `gpt-3.5-turbo`)
2. For Ollama, ensure the model you selected is pulled: `ollama pull llama3`
3. Check your API key hasn't expired

---

### Resetting the application to factory defaults

To clear all saved connections and settings:
```bash
docker compose down
rm -rf data/
docker compose up -d
```

> ⚠️ This permanently deletes all saved connections. Back up the `data/` folder first if needed.

---

## 13. FAQ

**Q: Do I need an internet connection to use QueryOptimizer?**

A: Only if you use an internet-based AI endpoint (OpenAI, Anthropic). The core EXPLAIN, Index Advisor, Slow Query, and Query Rewriter features work entirely offline. If you use Ollama locally, the AI feature also works offline.

---

**Q: Can multiple team members use it at the same time?**

A: Yes. Install it on a shared server and have team members access it via `http://your-server-ip:3000`. All connections saved by one user are visible to all users (there is no user account system in v1.0).

---

**Q: Is my database password safe?**

A: Passwords are encrypted using Fernet symmetric encryption before being written to the SQLite database. The encryption key is stored in `data/.secret_key` (auto-generated on first start) or can be set via the `SECRET_KEY` environment variable. Protect the `data/` directory as you would any credential store.

---

**Q: Can QueryOptimizer modify my database?**

A: Only if you explicitly run DDL statements (like the generated `CREATE INDEX`) from the Index Advisor. The EXPLAIN Visualizer, Query Rewriter, Slow Query Dashboard, and AI Assistant are all read-only. The only time a query executes against your database is when you enable the ANALYZE/STATISTICS PROFILE toggle in EXPLAIN, or when you manually run a query you typed.

---

**Q: How do I update to a new version?**

A: Replace the files in your installation directory with the new version archive, then run:
```bash
docker compose build
docker compose up -d
```
Your `data/` folder (connections and settings) is preserved across updates.

---

**Q: Can I use QueryOptimizer with Amazon RDS, Google Cloud SQL, or Azure SQL?**

A: Yes. Use the external endpoint hostname provided by your cloud provider. Ensure your server running QueryOptimizer can reach the database on the appropriate port (usually 5432 for PostgreSQL, 1433 for SQL Server). You may need to add the server's IP to your cloud database's firewall/security group rules.

---

**Q: The AI gives wrong or hallucinated advice. What should I do?**

A: AI-generated suggestions are advisory only — always review and test them before applying to production. Providing specific context (table sizes, index names, known constraints) significantly improves accuracy. The deterministic tools (EXPLAIN, Index Advisor, Query Rewriter) do not use AI and are always reliable.

---

*QueryOptimizer v1.0 — Commercial Self-Hosted Edition*
*For support, contact your vendor with your purchase reference number.*
