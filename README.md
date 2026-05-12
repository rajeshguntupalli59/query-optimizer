# QueryOptimizer

**A self-hosted SQL performance workbench for PostgreSQL and Microsoft SQL Server DBAs.**

QueryOptimizer gives your team a single browser-based tool to diagnose slow queries, find missing indexes, and rewrite inefficient SQL — without sending your data outside your infrastructure.

---

## Features

### EXPLAIN Visualizer
Run `EXPLAIN` or `EXPLAIN ANALYZE` (PostgreSQL) and `SET SHOWPLAN_ALL ON` (SQL Server) and view the execution plan as an interactive tree. Color-coded nodes instantly show where sequential scans and expensive joins are hiding. Automatic warnings flag sequential scans, row estimate drift, and key lookups without any manual interpretation.

### Index Advisor
Paste any SQL query and get a prioritized list of missing indexes backed by live catalog data — not guesswork. Each recommendation comes with a ready-to-copy `CREATE INDEX` statement and an explanation of why it helps. For SQL Server, recommendations also pull from `sys.dm_db_missing_index_details`.

### Slow Query Dashboard
Surface your worst-performing queries ranked by average execution time. Pulls from `pg_stat_statements` (PostgreSQL) or `sys.dm_exec_query_stats` (SQL Server). Filter by minimum call count, reset statistics, and drill into timing details per query.

### Query Rewriter
Paste any SQL and get an instant anti-pattern report — no database connection needed. Catches `SELECT *`, `OR` in `WHERE`, functions on indexed columns, leading wildcards, `NOT IN`, large `OFFSET`, implicit cross joins, and more. Useful for reviewing queries before deploying them.

### AI Assistant (Bring Your Own Endpoint)
Connect your own AI — OpenAI, Anthropic, Ollama, Azure OpenAI, or any OpenAI-compatible API. The tool sends your SQL and context to your endpoint and returns a fully rewritten query with explanations, warnings, and tuning tips. Your API key is stored encrypted on your server and never sent to the vendor.

### Multi-Connection Manager
Save and switch between multiple database connections. Credentials are encrypted at rest using Fernet symmetric encryption. Supports both PostgreSQL and SQL Server from the same interface with a database-type badge on each connection.

---

## Supported Databases

| Database | Supported Versions |
|---|---|
| PostgreSQL | 12, 13, 14, 15, 16, 17 |
| Microsoft SQL Server | 2016, 2017, 2019, 2022, Express, Azure SQL |

---

## Installation

QueryOptimizer ships as a single Docker Compose package. No external dependencies — just Docker.

```bash
# Extract the package
unzip queryoptimizer-v1.0.zip
cd queryoptimizer

# Windows
powershell -ExecutionPolicy Bypass -File setup.ps1

# Linux / macOS
chmod +x setup.sh && ./setup.sh
```

Open your browser to `http://localhost:3000`.

See [docs/QUICK_START.md](docs/QUICK_START.md) for a 5-minute setup guide and [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for the full manual.

---

## Security

- **No cloud dependency.** The tool makes no outbound connections except to AI endpoints you configure.
- **No telemetry.** No usage data, error reports, or analytics are sent anywhere.
- **Encrypted credentials.** Database passwords are encrypted with Fernet symmetric encryption before being written to the local SQLite database. The encryption key is auto-generated on first start and stored in `data/.secret_key`.
- **AI privacy.** Only the SQL text (and any context you type) is sent to your AI endpoint. No database credentials, schema, or query results are included.
- **Client responsibility.** The client is responsible for all database changes made using this tool. The vendor provides the software as-is with no warranty. See [LICENSE](LICENSE).

---

## System Requirements

| Requirement | Minimum |
|---|---|
| OS | Windows 10 / Server 2019, Ubuntu 20.04+, macOS 12+ |
| CPU | 2 cores |
| RAM | 2 GB |
| Disk | 1 GB |
| Docker | Docker Desktop 4.0+ (Windows/Mac) or Docker Engine 20.10+ (Linux) |

---

## Documentation

| Document | Description |
|---|---|
| [QUICK_START.md](docs/QUICK_START.md) | 5-minute setup and first query |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Complete feature reference |
| [TEST_GUIDE.md](docs/TEST_GUIDE.md) | Step-by-step verification with sample database |

---

## License

Commercial self-hosted license. See [LICENSE](LICENSE) for full terms.
One license per installation. The client is responsible for all use of the software after delivery.

---

*QueryOptimizer v1.0*
