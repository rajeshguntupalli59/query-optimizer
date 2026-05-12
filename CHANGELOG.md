# Changelog

All notable changes to QueryOptimizer are documented here.

---

## [1.0.0] — 2026-05-12

### Initial Release

First production release. All features tested against PostgreSQL 12–17 and Microsoft SQL Server 2016–2022 (including Express and Azure SQL).

#### Features

- **EXPLAIN Visualizer** — Interactive execution plan tree for PostgreSQL (`EXPLAIN ANALYZE`) and SQL Server (`SET STATISTICS PROFILE ON`). Color-coded nodes highlight sequential scans, expensive joins, and key lookups. Automatic warnings for row estimate drift and high-cost operations.

- **Index Advisor** — Missing-index recommendations backed by live catalog data. PostgreSQL: queries `pg_indexes`, `pg_stat_user_indexes`, and `information_schema` to detect missing covering indexes and un-indexed foreign keys. SQL Server: pulls from `sys.dm_db_missing_index_details`. Each recommendation includes a ready-to-copy `CREATE INDEX` statement.

- **Slow Query Dashboard** — Surface the worst-performing queries ranked by average execution time. PostgreSQL: reads `pg_stat_statements`. SQL Server: reads `sys.dm_exec_query_stats`. Filter by minimum call count; reset statistics with one click.

- **Query Rewriter** — Static anti-pattern analysis (no database connection required). Detects: `SELECT *`, `OR` in `WHERE`, functions applied to indexed columns, leading wildcards in `LIKE`, `NOT IN` with subqueries, large `OFFSET` pagination, implicit cross joins, and more.

- **AI Assistant** — Bring-your-own-endpoint AI integration. Supports OpenAI, Anthropic, Ollama, Azure OpenAI, and any OpenAI-compatible API. API keys are encrypted at rest and never exposed in API responses. Returns a rewritten query, explanation, warnings, and tuning tips.

- **Multi-Connection Manager** — Save and switch between multiple database connections. Credentials encrypted at rest with Fernet symmetric encryption. Supports PostgreSQL and SQL Server from the same interface.

- **Settings UI** — Configure the AI endpoint, provider, model, and API key from the browser. No server restart required. Accessible via the gear icon in the top-right corner.

#### Platform support

| Database | Versions |
|---|---|
| PostgreSQL | 12, 13, 14, 15, 16, 17 |
| Microsoft SQL Server | 2016, 2017, 2019, 2022, Express, Azure SQL |

| OS | Support |
|---|---|
| Windows 10 / Server 2019+ | Full |
| Ubuntu 20.04+ | Full |
| macOS 12+ | Full |

#### Delivery

- Ships as a single Docker Compose package — no external dependencies beyond Docker.
- One-command installers: `setup.ps1` (Windows) and `setup.sh` (Linux/macOS).
- All data (SQLite database, encryption key) stored in the local `data/` directory — no cloud dependency.

---

*QueryOptimizer is a commercial self-hosted product. See [LICENSE](LICENSE) for terms.*
