# QueryOptimizer — Testing Guide

This guide walks you through setting up a test database and running a query through every feature of the tool.

---

## Step 1 — Get a Test PostgreSQL Database

Pick whichever option works for you:

---

### Option A — Docker Desktop (fastest, if Docker is installed)

Open a terminal and run:

```bash
docker run -d \
  --name qo-test-db \
  -e POSTGRES_USER=dba \
  -e POSTGRES_PASSWORD=dba123 \
  -e POSTGRES_DB=shopdb \
  -p 5433:5432 \
  postgres:16 \
  -c shared_preload_libraries=pg_stat_statements \
  -c pg_stat_statements.track=all
```

**Windows (PowerShell):**
```powershell
docker run -d `
  --name qo-test-db `
  -e POSTGRES_USER=dba `
  -e POSTGRES_PASSWORD=dba123 `
  -e POSTGRES_DB=shopdb `
  -p 5433:5432 `
  postgres:16 `
  -c shared_preload_libraries=pg_stat_statements `
  -c pg_stat_statements.track=all
```

Connection details to use in QueryOptimizer:
| Field    | Value    |
|----------|----------|
| Host     | `localhost` |
| Port     | `5433`   |
| Database | `shopdb` |
| Username | `dba`    |
| Password | `dba123` |

---

### Option B — Install PostgreSQL locally (no Docker needed)

1. Download from **https://www.postgresql.org/download/**
2. Install with default settings (port 5432)
3. Create a test database:
   ```sql
   CREATE DATABASE shopdb;
   ```
4. Use these connection details in QueryOptimizer:

| Field    | Value        |
|----------|--------------|
| Host     | `localhost`  |
| Port     | `5432`       |
| Database | `shopdb`     |
| Username | `postgres`   |
| Password | *(your install password)* |

---

### Option C — Free cloud PostgreSQL (no install at all)

1. Go to **https://neon.tech** (free tier, no credit card)
2. Create a project → it gives you a connection string
3. Extract host, port (5432), database, username, password from the connection string
4. Use those details in QueryOptimizer

---

## Step 2 — Load the Sample Data

Once you have a database running, load the sample schema and data.

**Using psql (command line):**
```bash
psql -h localhost -p 5433 -U dba -d shopdb -f docs/test-data.sql
```

**Using any GUI (pgAdmin, DBeaver, TablePlus):**
- Open the file `docs/test-data.sql`
- Connect to your database
- Run the entire script

The script creates 5 tables and loads:
- 500 customers
- 200 products
- 2,000 orders
- 6,000 order items
- Deliberately **missing indexes** so the Index Advisor has something to find

---

## Step 3 — Add the Connection in QueryOptimizer

1. Open **http://localhost:5173**
2. Click **New** in the sidebar
3. Select **PostgreSQL**
4. Enter the connection details from Step 1
5. Click **Save**
6. Hover the connection row and click the **✓ checkmark** to test
7. Click the connection row to activate it

---

## Step 4 — Test Each Feature

Work through each tab in order. Each section below gives you a real query that produces interesting results.

---

### Feature 1 — EXPLAIN Visualizer

**Tab:** EXPLAIN

Paste this query and click **EXPLAIN** (no ANALYZE toggle yet):

```sql
SELECT
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.id)       AS total_orders,
    SUM(o.total_amount) AS lifetime_value
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE c.country = 'US'
  AND o.status = 'delivered'
GROUP BY c.id, c.first_name, c.last_name, c.email
ORDER BY lifetime_value DESC
LIMIT 10;
```

**What to look for:**
- 🔴 Red nodes labeled **Seq Scan** — the database is reading the full table because there are no indexes on `country` or `status`
- High **Total Cost** number at the root node
- The **warnings panel** should flag the sequential scans automatically

Now toggle **ANALYZE** and run again.

**What changes with ANALYZE:**
- Each node now shows **actual time** and **actual rows** alongside the estimates
- If the estimate and actual rows differ a lot, the tool shows a warning like *"row estimate off by Nx"*

---

### Feature 2 — Index Advisor

**Tab:** Index Advisor

Paste the same query and click **Analyze Indexes**:

```sql
SELECT
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.id)         AS total_orders,
    SUM(o.total_amount) AS lifetime_value
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE c.country = 'US'
  AND o.status = 'delivered'
GROUP BY c.id, c.first_name, c.last_name, c.email
ORDER BY lifetime_value DESC
LIMIT 10;
```

**What you should see:**
- A recommendation to index `orders.customer_id` (FK with no index)
- A recommendation to index `customers.country` (used in WHERE)
- A recommendation to index `orders.status` (used in WHERE)
- Each card has a ready-to-copy `CREATE INDEX` DDL statement

**Try applying one** — copy the DDL for `customer_id`, run it in your DB client, then re-run the advisor. That card should disappear.

---

### Feature 3 — Slow Query Dashboard

**Tab:** Slow Queries

First, run these queries a few times in your DB client to generate some history:

```sql
-- Run this 20 times (slow — full scan)
SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC;

-- Run this 10 times
SELECT c.email, COUNT(*) FROM customers c
JOIN orders o ON o.customer_id = c.id
GROUP BY c.email ORDER BY COUNT(*) DESC LIMIT 5;

-- Run this 5 times
SELECT * FROM products WHERE price > 100 ORDER BY price DESC;
```

Then in QueryOptimizer:
1. Set **Top** to `10`, **Min calls** to `1`
2. Click **Load**

**What to look for:**
- Your queries listed, ranked by average time (slowest first)
- The bar chart shows relative performance at a glance
- Click any row to expand full details — total time, min/max, cache hit %
- A **Cache hit %** below 90% means the database is reading from disk, not memory

---

### Feature 4 — Query Rewriter

**Tab:** Query Rewriter *(no DB connection needed)*

Paste this deliberately bad query:

```sql
SELECT DISTINCT *
FROM customers c, orders o
WHERE LOWER(c.email) LIKE '%@gmail.com'
   OR c.country = 'US'
ORDER BY c.created_at
OFFSET 5000 LIMIT 20;
```

**What you should see flagged:**

| Anti-pattern | Why it's bad |
|---|---|
| `SELECT *` | Fetches all columns |
| `SELECT DISTINCT` | Forces an extra sort step |
| `LOWER(email) LIKE '%...'` | Function on column + leading wildcard = no index |
| `OR` in WHERE | Prevents index use |
| Comma-separated tables | Implicit cross join |
| `OFFSET 5000` | Scans and discards 5000 rows every time |

Each issue shows the severity, explanation, and a suggested fix.

---

### Feature 5 — AI Assistant

**Tab:** AI Assistant *(requires AI configured in Settings)*

**First, configure AI** (gear icon ⚙ top-right → Settings):
- Set your provider, endpoint, API key, and model
- Click **Save Settings**

Then come back to AI Assistant and paste:

```sql
SELECT DISTINCT *
FROM customers c, orders o
WHERE LOWER(c.email) LIKE '%@gmail.com'
   OR c.country = 'US'
ORDER BY c.created_at
OFFSET 5000 LIMIT 20;
```

Add this in the **context** field:
```
customers has 500 rows, orders has 2000 rows.
email column has no index. country has no index.
```

Click **Analyze with AI**.

**What the AI returns:**
- A fully rewritten, optimized version of the query
- An explanation of every change it made
- Specific warnings about the original query
- Additional tuning tips

---

## Step 5 — Compare Before and After

After applying the recommended indexes from the Index Advisor, re-run the EXPLAIN to see the improvement:

```sql
-- Apply these indexes first:
CREATE INDEX ON orders (customer_id);
CREATE INDEX ON customers (country);
CREATE INDEX ON orders (status);

-- Then re-run EXPLAIN on the original query:
SELECT
    c.first_name, c.last_name, c.email,
    COUNT(o.id) AS total_orders,
    SUM(o.total_amount) AS lifetime_value
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE c.country = 'US'
  AND o.status = 'delivered'
GROUP BY c.id, c.first_name, c.last_name, c.email
ORDER BY lifetime_value DESC
LIMIT 10;
```

You'll see the **Seq Scan** nodes turn into **Index Scan** nodes (green) and the Total Cost drop significantly.

---

## Cleanup

When you're done testing, remove the test database:

```bash
# Docker Option A
docker stop qo-test-db && docker rm qo-test-db

# Local PostgreSQL
DROP DATABASE shopdb;
```

---

## Summary of What Each Feature Proved

| Feature | What the test showed |
|---|---|
| EXPLAIN | Seq scans on unindexed columns; actual vs estimated rows |
| Index Advisor | 3 missing indexes detected automatically from the query |
| Slow Queries | Real execution history ranked by mean time |
| Query Rewriter | 6 anti-patterns caught without touching the database |
| AI Assistant | Full query rewrite with explanations |
