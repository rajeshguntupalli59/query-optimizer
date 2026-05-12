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

**QueryOptimizer** is a self-hosted DBA workbench for diagnosing and improving SQL query performance. It connects directly to your PostgreSQL or Microsoft SQL Server databases and gives you five tools in one interface:

| Feature | What it does | Needs a DB? |
|---|---|---|
| **EXPLAIN Visualizer** | Renders the execution plan as a tree with cost breakdowns and automatic warnings | Yes |
| **Index Advisor** | Analyzes your query against the live catalog and generates ready-to-run `CREATE INDEX` statements | Yes |
| **Slow Query Dashboard** | Surfaces your worst-performing queries ranked by average execution time | Yes |
| **Query Rewriter** | Detects SQL anti-patterns without touching the database — useful before deployment | No |
| **AI Assistant** | Sends your query to your own AI endpoint for context-aware rewrites and tuning advice | No |

**Everything stays in your infrastructure.** No cloud dependency, no telemetry, no callbacks to the vendor after installation.

---

## 2. System Requirements

### Server running QueryOptimizer

| Requirement | Minimum |
|---|---|
| OS | Windows 10 / Server 2019, Ubuntu 20.04+, macOS 12+ |
| CPU | 2 cores |
| RAM | 2 GB |
| Disk | 1 GB (Docker images + SQLite database) |
| Docker | Docker Desktop 4.0+ (Windows/Mac) or Docker Engine 20.10+ (Linux) |
| Network | Must reach your database servers on the appropriate port |

### Target databases (what you connect TO)

| Database | Supported versions |
|---|---|
| PostgreSQL | 12, 13, 14, 15, 16, 17 |
| Microsoft SQL Server | 2016, 2017, 2019, 2022, Express, Azure SQL |

> **Note:** The Slow Query Dashboard requires `pg_stat_statements` for PostgreSQL. See [Section 8](#8-slow-query-dashboard) for setup.

---

## 3. Installation

### Step 1 — Download the package

Extract the `queryoptimizer-v1.0.zip` archive to a folder of your choice:

- **Windows:** `C:\Tools\queryoptimizer\`
- **Linux / macOS:** `/opt/queryoptimizer/`

### Step 2 — Run the installer

**Windows (PowerShell):**
```powershell
cd C:\Tools\queryoptimizer
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**Linux / macOS:**
```bash
cd /opt/queryoptimizer
chmod +x setup.sh && ./setup.sh
```

The installer will:
1. Verify Docker is installed and running
2. Create your `.env` configuration file from the template
3. Create the `data/` directory for persistent storage
4. Build and start the Docker containers (5–10 minutes on first run)

### Step 3 — Open the application

```
http://localhost:3000
```

The API explorer (for integrators) is at:
```
http://localhost:8000/docs
```

### Changing the default ports

Edit `.env` before running the installer:

```env
FRONTEND_PORT=8080
BACKEND_PORT=9000
```

### Installing on a shared server

If other team members will access the tool remotely, expose port 3000 through your firewall. They connect via `http://your-server-ip:3000`. For production use, put a reverse proxy (nginx or Caddy) in front and enable HTTPS.

---

## 4. First-Time Setup

When you open QueryOptimizer for the first time you will see the Overview screen.

**To start analyzing queries:**

1. Click **New** in the left sidebar to add a database connection
2. Select your database type — **PostgreSQL** or **SQL Server**
3. Enter your connection details and click **Save**
4. Hover the connection row and click the **checkmark ✓** to test connectivity
5. Click the connection row to activate it (it appears in the top-right pill)
6. Choose a feature tab from the top navigation bar

Connections are saved to disk and persist across restarts. Passwords are stored encrypted.

---

## 5. Managing Database Connections

### Adding a connection

Click **New** in the sidebar and fill in the fields:

| Field | PostgreSQL | SQL Server |
|---|---|---|
| Connection Name | Any label, e.g. "Prod DB" | Any label |
| Host | `localhost` or hostname | `localhost` or `hostname\INSTANCE` |
| Port | `5432` | `1433` |
| Database | your database name | your database name |
| Username | `postgres` | `sa` (or leave blank for Windows Auth) |
| Password | your password | your password (or blank for Windows Auth) |

**SQL Server named instances** — if your SQL Server uses a named instance (e.g., SQL Server Express), enter the host as `hostname\INSTANCE`:

```
localhost\SQLEXPRESS
192.168.1.10\PROD2022
```

Do not enter a port number when using a named instance — the tool resolves it automatically.

**Windows Authentication** — leave both Username and Password blank. The tool will connect using the Windows account that runs the service. This works when QueryOptimizer is installed on the same Windows server as SQL Server.

### Testing a connection

Hover over a saved connection and click the **checkmark icon ✓**. A green checkmark confirms success; a red indicator shows the error message.

### Switching connections

Click any saved connection row to make it active. The active connection is shown in the top-right corner.

### Editing a connection

Hover over a saved connection and click the **pencil icon**.

### Deleting a connection

Hover over a saved connection and click the **trash icon**.

---

## 6. EXPLAIN Visualizer

**Tab:** EXPLAIN
**Requires:** Active database connection

The EXPLAIN Visualizer runs the database's query planner and renders the execution plan as an interactive tree with cost breakdowns and automatic warnings.

### Running an estimated plan

1. Paste your SQL into the editor
2. Click **EXPLAIN**

This does **not** execute the query — it only asks the planner what it *would* do. Safe to run on production databases.

### Running an actual plan (ANALYZE mode)

1. Toggle **ANALYZE** on
2. Click **EXPLAIN**

> ⚠️ **ANALYZE actually executes the query.** Do not run `DELETE`, `UPDATE`, or `INSERT` statements with ANALYZE enabled — they will modify your data.

For PostgreSQL you can also enable **BUFFERS** alongside ANALYZE to see I/O statistics (shared block hits vs. disk reads).

### Reading the plan tree

Each row in the tree is one step the database takes. Color coding:

| Color | Meaning |
|---|---|
| 🔴 Red | Sequential Scan / Table Scan — full table read, no index used |
| 🟢 Green | Index Scan / Index Seek — index is being used |
| 🟡 Yellow | Join operation |
| 🔵 Blue | Sort, Aggregate, or other operation |

**Key metrics per node:**

- **cost=X..Y** — estimated startup and total cost (planner units, not milliseconds)
- **rows=N** — estimated rows this step produces
- **actual Xms, N rows** — real execution time and row count (ANALYZE only)

### Automatic warnings

The tool flags these patterns automatically:

| Warning | What it means |
|---|---|
| Sequential scan / Table scan | Full table read — an index on the filter column would help |
| Row estimate off by Nx | Planner estimates are way off — run `ANALYZE` on the table to refresh statistics |
| Expensive join | High-cost Hash Match or Nested Loop — ensure join columns are indexed |
| Key Lookup *(SQL Server)* | Non-clustered index doesn't cover all selected columns — add `INCLUDE` columns |

---

## 7. Index Advisor

**Tab:** Index Advisor
**Requires:** Active database connection

The Index Advisor checks your query against the live database catalog to find missing or ineffective indexes. It generates ready-to-run DDL.

### How to use it

1. Paste your SQL (any SELECT, UPDATE, DELETE with a WHERE clause or JOIN)
2. Click **Analyze Indexes**
3. Review the recommendation cards

### What it checks

| Check | How it works |
|---|---|
| Tables with no indexes | Checks the index catalog for each table in your query |
| FK columns with no index | Finds foreign key columns that lack a supporting index (common cause of slow joins) |
| WHERE clause columns | Identifies filter columns not covered by any index |
| ORDER BY columns | Identifies sort columns not covered by any index |
| Optimizer-recommended indexes *(SQL Server)* | Reads `sys.dm_db_missing_index_details` — SQL Server's own missing index recommendations |

### Reading a recommendation card

Each card shows:
- **Table and column(s)** — where the index should go
- **Reason** — why the index is recommended
- **Estimated benefit** — High / Medium-High / Medium / Low
- **DDL** — the exact `CREATE INDEX` statement to copy and run

### Applying a recommendation

Click **Copy** on the DDL block, review the statement, and run it in your database client during a maintenance window.

> **Important:** Always test index changes on a non-production copy first. Creating an index on a large table acquires a brief write lock.

---

## 8. Slow Query Dashboard

**Tab:** Slow Queries
**Requires:** Active database connection

The Slow Query Dashboard shows your worst-performing queries ranked by average execution time, using the database's own query statistics.

### PostgreSQL — enabling pg_stat_statements

This feature requires the `pg_stat_statements` extension. If it is not already enabled:

**Step 1** — Add to `postgresql.conf`:
```ini
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

**Step 2** — Fully restart PostgreSQL (a reload is not enough).

**Step 3** — Connect to your database and run once:
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

The extension begins collecting data immediately. Run a workload for a few minutes before using the dashboard for meaningful results.

### SQL Server — no setup required

`sys.dm_exec_query_stats` is available by default. No configuration needed.

### Using the dashboard

1. Set **Top N** — how many queries to show (max 100)
2. Set **Min calls** — hide queries that ran fewer than N times (filters out one-off queries)
3. Click **Load**
4. Click any row to expand its full details

### Metrics explained

| Metric | Meaning |
|---|---|
| **Calls** | How many times this query has been executed |
| **Mean time** | Average execution time — the primary ranking column |
| **Min / Max** | Fastest and slowest individual runs |
| **Total time** | Cumulative time spent across all executions |
| **Rows** | Average rows returned per execution |
| **Cache hit %** | Data served from memory vs. disk. Below 90% suggests memory pressure. |

### Resetting statistics

Click **Reset stats** to clear accumulated data and start fresh.

> ⚠️ **SQL Server warning:** Reset runs `DBCC FREEPROCCACHE`, clearing the entire plan cache server-wide. All queries will recompile on next execution, which can cause a short performance spike. Use with caution on busy production servers.

---

## 9. Query Rewriter

**Tab:** Query Rewriter
**Requires:** No database connection needed

The Query Rewriter performs static analysis on SQL you paste in, detecting common anti-patterns that hurt performance. It works offline — useful for reviewing queries before deploying them to production.

### How to use it

1. Paste your SQL into the editor
2. Click **Analyze Query**
3. Review the issues, severity ratings, and suggested fixes

### Anti-patterns detected

| Anti-pattern | Severity | Why it's a problem |
|---|---|---|
| `SELECT *` | High | Fetches all columns including unused ones — wastes I/O and memory |
| `OR` in `WHERE` | High | Prevents index use on either branch; consider `UNION ALL` |
| Function on indexed column | High | `WHERE LOWER(email) = 'x'` cannot use a B-tree index on `email` |
| `LIKE '%value'` leading wildcard | Medium | B-tree index cannot be used; consider full-text search |
| `SELECT DISTINCT` | Medium | Forces a sort/hash step; may indicate a join producing unwanted duplicates |
| `NOT IN (subquery)` | Medium | Returns no rows if the subquery contains a NULL; use `NOT EXISTS` instead |
| Implicit cross join (`FROM a, b`) | Medium | Comma-separated tables create a cartesian product without a proper JOIN |
| Large `IN` list (50+ values) | Low | Can cause plan instability; load values into a temp table and JOIN |
| Large `OFFSET` (10,000+) | Low | Database scans and discards all skipped rows; use keyset pagination |

### Severity levels

- **High** — Likely causing a significant performance problem right now
- **Medium** — May cause problems at scale or under certain conditions
- **Low** — Best-practice violation worth fixing before the table grows large

---

## 10. AI Assistant

**Tab:** AI Assistant
**Requires:** AI endpoint configured in Settings

The AI Assistant sends your SQL to your configured AI endpoint and returns:

- **Rewritten query** — an optimized version with explanations of every change
- **Explanation** — plain-English summary of what was changed and why
- **Warnings** — potential issues identified in the original query
- **Tuning tips** — additional advice specific to your query and database

### How to use it

1. Optionally add **context** in the field above the editor — table sizes, known indexes, performance targets
2. Paste your SQL into the editor
3. Click **Analyze with AI**

### Writing good context

The AI produces much better results with context. Examples:

```
orders table has 80 million rows. customer_id has no index.
This query runs every 5 seconds from the application layer.
Response time target: under 100ms.
```

```
Running on SQL Server 2022. The products table has a full-text
index on the name column. Report query — not latency-sensitive.
```

### If AI is not configured

If the tab shows "AI is not configured," click the gear icon ⚙ in the top-right corner to open Settings and add your AI endpoint details.

> **Privacy:** The tool sends only the SQL text (and any context you type) to your AI endpoint. No database credentials, schema metadata, or query results are ever included.

---

## 11. Settings

**Access:** Gear icon ⚙ — top-right corner of the header

### AI Integration

| Field | Description |
|---|---|
| **Provider** | Select your provider to auto-fill the endpoint URL |
| **API Endpoint** | The full URL the tool will POST to |
| **API Key** | Your API token — stored encrypted on your server, never sent to the vendor |
| **Model** | The model name to request |

**Supported providers:**

| Provider | Endpoint | Notes |
|---|---|---|
| OpenAI | `https://api.openai.com/v1/chat/completions` | Requires an OpenAI API key |
| Anthropic | `https://api.anthropic.com/v1/messages` | Requires an Anthropic API key |
| Ollama | `http://localhost:11434/api/generate` | No key needed — runs on your own machine |
| Azure OpenAI | `https://<resource>.openai.azure.com/openai/deployments/<model>/chat/completions?api-version=2024-02-01` | Use your Azure key |
| Any OpenAI-compatible API | Your endpoint URL | Select **Generic** |

### Configuring via `.env` (alternative)

You can pre-configure AI settings in the `.env` file instead of the UI:

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
If this fails, open Docker Desktop and wait for it to fully start, then try again.

**Check port conflicts:**
```powershell
# Windows PowerShell
netstat -ano | findstr ":3000"
netstat -ano | findstr ":8000"
```
If another application is using port 3000 or 8000, change those ports in `.env` and run `docker compose up -d`.

**View logs:**
```bash
docker compose logs backend
docker compose logs frontend
```

---

### Cannot connect to database

**"Connection refused" / "target machine actively refused it"**
- Verify the database is running and accepting connections
- If connecting from Docker to a database on your local machine, use your machine's LAN IP address (e.g., `192.168.1.10`) instead of `localhost` — inside a Docker container, `localhost` refers to the container itself, not your host machine

**"Login failed" / "Password authentication failed"**
- Verify username and password are correct
- For PostgreSQL: ensure the user has `CONNECT` privilege on the database
- For SQL Server: ensure the login is enabled and has access to the database

**SQL Server: Named Instance not found**
- Enter the host as `hostname\INSTANCE` (e.g., `localhost\SQLEXPRESS`)
- Do not enter a port number alongside a named instance
- Ensure the SQL Server Browser service is running: open **Services** → find **SQL Server Browser** → set to Automatic and start it

**SQL Server: Windows Authentication**
- Leave both Username and Password blank in the connection form
- The tool connects using the Windows account running the Docker service
- This works when QueryOptimizer and SQL Server are on the same Windows machine

**"SSL connection required"** (PostgreSQL cloud providers)
- AWS RDS, Google Cloud SQL, and similar providers require SSL
- Contact your vendor with this requirement — SSL connection support can be added as a configuration option

---

### Slow Query tab shows "pg_stat_statements must be loaded via shared_preload_libraries"

This means `pg_stat_statements` was added with `CREATE EXTENSION` but the library was not loaded at startup. You must:

1. Add `shared_preload_libraries = 'pg_stat_statements'` to `postgresql.conf`
2. **Fully restart PostgreSQL** — `pg_reload_conf()` is not sufficient
3. Reconnect and try again

---

### Index Advisor returns no recommendations

This can happen when:
- All tables in your query already have indexes covering the queried columns — this is the correct result
- The query has no WHERE clause, JOIN, or ORDER BY that would benefit from an index
- The query uses table aliases that the advisor couldn't resolve

Try running the query first against an unindexed table to confirm recommendations appear.

---

### EXPLAIN returns an error

Common causes:
- **Syntax error** — verify the query runs in your database client first
- **Insufficient permissions** — the user needs SELECT privilege on all tables referenced
- **ANALYZE on a write query** — ANALYZE executes the query; use EXPLAIN without ANALYZE for INSERT/UPDATE/DELETE

---

### AI Assistant returns "Could not parse AI response"

The AI endpoint returned text that the tool couldn't parse as structured output. Try:

1. Switch to a model that follows instructions reliably (e.g., `gpt-4o` instead of `gpt-3.5-turbo`)
2. For Ollama: ensure the model is downloaded — `ollama pull llama3`
3. Verify your API key is valid and has not expired
4. Check your endpoint URL — a missing `/v1/` in the path is a common mistake

---

### Resetting to factory defaults

To clear all saved connections and settings:
```bash
docker compose down
rm -rf data/
docker compose up -d
```

> ⚠️ This permanently deletes all saved connections. Back up the `data/` folder first if needed.

---

## 13. FAQ

**Q: Do I need an internet connection?**

A: Only if you use an internet-based AI provider (OpenAI, Anthropic). The EXPLAIN, Index Advisor, Slow Query, and Query Rewriter features work fully offline. Ollama also works offline.

---

**Q: Can multiple team members use it at the same time?**

A: Yes. Install it on a shared server and point team members to `http://your-server-ip:3000`. All saved connections are shared — there is no per-user account system in v1.0.

---

**Q: Are my database passwords safe?**

A: Passwords are encrypted using Fernet symmetric encryption before being written to the local SQLite database. The encryption key is stored in `data/.secret_key` (auto-generated on first start). Protect the `data/` folder as you would any credential store — do not share it or commit it to version control.

---

**Q: Can QueryOptimizer change anything in my database?**

A: Only if you explicitly run something that modifies data. The EXPLAIN Visualizer (without ANALYZE), Index Advisor, Slow Query Dashboard, and Query Rewriter are all read-only. The only times a query executes are:

- When you enable ANALYZE in the EXPLAIN Visualizer (runs your query)
- When you copy a `CREATE INDEX` from the Index Advisor and run it yourself in your database client

---

**Q: Can I connect to Amazon RDS, Google Cloud SQL, or Azure SQL?**

A: Yes. Use the endpoint hostname provided by your cloud provider. Ensure the server running QueryOptimizer can reach the database port (5432 for PostgreSQL, 1433 for SQL Server) — you may need to add the server's IP to your cloud firewall or security group rules.

---

**Q: How do I update to a new version?**

A: Replace the files in your installation directory with the new version archive, then run:
```bash
docker compose build
docker compose up -d
```
Your `data/` folder (connections and settings) is preserved across updates.

---

**Q: The AI gives incorrect advice. What should I do?**

A: AI suggestions are advisory — always review and test before applying to production. Providing specific context (table row counts, existing indexes, query frequency) significantly improves accuracy. The deterministic tools (EXPLAIN, Index Advisor, Query Rewriter) do not use AI and are always accurate.

---

**Q: What SQL dialects does the Query Rewriter support?**

A: The Query Rewriter analyzes SQL text without connecting to a database, so it works with both PostgreSQL and SQL Server syntax. It focuses on patterns that are problematic in both dialects.

---

*QueryOptimizer v1.0 — Commercial Self-Hosted Edition*
*For support, contact your vendor with your purchase reference number.*
