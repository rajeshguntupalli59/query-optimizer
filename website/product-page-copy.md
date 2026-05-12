# QueryOptimizer — Product Page Copy
# Paste this into Gumroad or Lemon Squeezy when creating your product listing.

---

## Product Name
QueryOptimizer — Self-Hosted SQL Performance Workbench

## Short Description (shown in search results / cards)
Diagnose slow queries, find missing indexes, and rewrite bad SQL for PostgreSQL and SQL Server. Self-hosted. No subscription. Installs in 5 minutes.

## Price
$149 (one-time)

---

## Full Description

**Stop guessing why your SQL is slow.**

QueryOptimizer is a browser-based workbench for DBAs and developers who need to understand and fix slow queries — without sending their data to the cloud.

It runs entirely on your own server. No subscription. No telemetry. No data ever leaves your infrastructure.

---

### What's included

**EXPLAIN Visualizer**
Run EXPLAIN ANALYZE (PostgreSQL) or SET STATISTICS PROFILE ON (SQL Server) and see the execution plan as an interactive, color-coded tree. Automatic warnings flag sequential scans, row estimate drift, and expensive joins without any manual interpretation.

**Index Advisor**
Paste any SQL query and get a prioritized list of missing indexes backed by live catalog data — not guesswork. Each recommendation includes a ready-to-copy CREATE INDEX statement and an explanation of why it helps. For SQL Server, recommendations pull from sys.dm_db_missing_index_details.

**Slow Query Dashboard**
Surface your worst-performing queries ranked by average execution time. Reads from pg_stat_statements (PostgreSQL) or sys.dm_exec_query_stats (SQL Server). Filter by minimum call count, reset statistics, and drill into timing details per query.

**Query Rewriter**
Catch anti-patterns before they hit production — no database connection needed. Detects SELECT *, OR in WHERE, functions on indexed columns, leading wildcards, NOT IN, large OFFSET, implicit cross joins, and more.

**AI Assistant (Bring Your Own Endpoint)**
Connect your own AI — OpenAI, Anthropic, Ollama, Azure OpenAI, or any OpenAI-compatible API. Get a fully rewritten query with explanations, warnings, and tuning tips. Your API key is stored encrypted on your server and never sent to us.

**Multi-Connection Manager**
Save and switch between multiple database connections. Credentials are encrypted at rest using Fernet symmetric encryption. Supports PostgreSQL and SQL Server from the same interface.

---

### Supported databases

- **PostgreSQL** — versions 12, 13, 14, 15, 16, 17
- **Microsoft SQL Server** — 2016, 2017, 2019, 2022, Express, Azure SQL (including named instances and Windows Authentication)

---

### Installation

QueryOptimizer ships as a single Docker Compose package. Requires Docker Desktop (Windows/Mac) or Docker Engine (Linux).

```
unzip queryoptimizer-v1.0.zip
cd queryoptimizer

# Windows:
powershell -ExecutionPolicy Bypass -File setup.ps1

# Linux / macOS:
chmod +x setup.sh && ./setup.sh
```

Open your browser to http://localhost:3000. Takes under 5 minutes.

---

### Security

- **No cloud dependency.** Zero outbound connections except to AI endpoints you configure.
- **No telemetry.** No usage data, error reports, or analytics are sent anywhere.
- **Encrypted credentials.** Database passwords are encrypted with Fernet symmetric encryption before being stored locally.
- **AI privacy.** Only the SQL text you paste is sent to your AI endpoint. No credentials, schema, or query results.

---

### What you receive after purchase

- `queryoptimizer-v1.0.zip` — the complete application package
- `QUICK_START.md` — 5-minute setup guide (included in the ZIP)
- `USER_GUIDE.md` — complete feature reference (included in the ZIP)
- Email support for installation questions

---

### License

One license = one installation. See the LICENSE file included in the package.
The client is responsible for all database changes made using this tool.

---

## Tags (for discoverability)
sql, postgresql, sql-server, database, dba, performance, query optimization, explain, indexes, self-hosted, developer tools

## Category
Developer Tools / Databases

---

## What to fill in on the platform

| Field | Value |
|---|---|
| Product name | QueryOptimizer — Self-Hosted SQL Performance Workbench |
| Price | $149 |
| File to upload | dist/queryoptimizer-v1.0.zip |
| Call to action | Buy Now |
| Receipt note | Thank you! Extract the ZIP and follow QUICK_START.md inside. Reply to this email if you need help. |
| Support email | queryoptimizer78@gmail.com |
