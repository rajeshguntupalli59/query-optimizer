-- ============================================================================
-- QueryOptimizer — SQL Server test data (shopdb)
-- Creates a small shop schema with DELIBERATELY missing indexes so the
-- Index Advisor, Rewriter and Slow Query tabs have something to find.
--
-- Run it:
--   GUI (SSMS / Azure Data Studio): open this file, connect to your
--   SQL Server (master database), press F5.
--   docker exec: docker cp docs/mssql-test-data.sql mssql-test:/tmp/seed.sql
--                docker exec -i mssql-test /opt/mssql-tools18/bin/sqlcmd ^
--                  -S localhost -U sa -P "Test1234!" -C -i /tmp/seed.sql
-- ============================================================================

IF DB_ID('shopdb') IS NULL
    CREATE DATABASE shopdb;
GO

USE shopdb;
GO

-- Clean slate for re-runs
IF OBJECT_ID('dbo.order_items', 'U') IS NOT NULL DROP TABLE dbo.order_items;
IF OBJECT_ID('dbo.orders',      'U') IS NOT NULL DROP TABLE dbo.orders;
IF OBJECT_ID('dbo.products',    'U') IS NOT NULL DROP TABLE dbo.products;
IF OBJECT_ID('dbo.customers',   'U') IS NOT NULL DROP TABLE dbo.customers;
GO

CREATE TABLE dbo.customers (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    first_name NVARCHAR(50)  NOT NULL,
    last_name  NVARCHAR(50)  NOT NULL,
    email      NVARCHAR(120) NOT NULL,
    country    CHAR(2)       NOT NULL,   -- no index: advisor should flag it
    created_at DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.products (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    sku        NVARCHAR(30)  NOT NULL,
    name       NVARCHAR(120) NOT NULL,
    price      DECIMAL(10,2) NOT NULL,
    category   NVARCHAR(40)  NOT NULL
);

CREATE TABLE dbo.orders (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT          NOT NULL,   -- FK, no index: advisor should flag it
    status      NVARCHAR(20) NOT NULL,   -- no index: advisor should flag it
    total       DECIMAL(10,2) NOT NULL,
    placed_at   DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_orders_customers FOREIGN KEY (customer_id)
        REFERENCES dbo.customers (id)
);

CREATE TABLE dbo.order_items (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    order_id   INT          NOT NULL,   -- FK, no index: advisor should flag it
    product_id INT          NOT NULL,   -- FK, no index: advisor should flag it
    qty        INT          NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    CONSTRAINT FK_items_orders FOREIGN KEY (order_id)
        REFERENCES dbo.orders (id),
    CONSTRAINT FK_items_products FOREIGN KEY (product_id)
        REFERENCES dbo.products (id)
);
GO

-- 500 customers (set-based, fast)
WITH n AS (
    SELECT TOP (500) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.customers (first_name, last_name, email, country, created_at)
SELECT CONCAT('First', i),
       CONCAT('Last',  i),
       CONCAT('user',  i, '@example.com'),
       CASE i % 5 WHEN 0 THEN 'US' WHEN 1 THEN 'IN' WHEN 2 THEN 'UK'
                  WHEN 3 THEN 'CA' ELSE 'AU' END,
       DATEADD(day, -(i % 900), SYSUTCDATETIME())
FROM n;
GO

-- 200 products
WITH n AS (
    SELECT TOP (200) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.products (sku, name, price, category)
SELECT CONCAT('SKU-', i),
       CONCAT('Product ', i),
       CAST((i % 490) + 10 AS DECIMAL(10,2)),
       CASE i % 4 WHEN 0 THEN 'electronics' WHEN 1 THEN 'books'
                  WHEN 2 THEN 'clothing' ELSE 'home' END
FROM n;
GO

-- 2,000 orders
WITH n AS (
    SELECT TOP (2000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.orders (customer_id, status, total, placed_at)
SELECT ((i * 7) % 500) + 1,
       CASE i % 4 WHEN 0 THEN 'delivered' WHEN 1 THEN 'shipped'
                  WHEN 2 THEN 'pending' ELSE 'cancelled' END,
       CAST((i % 500) + 10 AS DECIMAL(10,2)),
       DATEADD(hour, -(i % 2000), SYSUTCDATETIME())
FROM n;
GO

-- 6,000 order items
WITH n AS (
    SELECT TOP (6000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.order_items (order_id, product_id, qty, unit_price)
SELECT ((i * 13) % 2000) + 1,
       ((i * 17) % 200) + 1,
       (i % 5) + 1,
       CAST((i % 490) + 10 AS DECIMAL(10,2))
FROM n;
GO

-- Warm up the missing-index DMVs: run a few typical queries so
-- sys.dm_db_missing_index_details has data for the Index Advisor.
SELECT c.first_name, c.last_name, COUNT(o.id) AS order_count
FROM dbo.customers c
JOIN dbo.orders o ON o.customer_id = c.id
WHERE c.country = 'US' AND o.status = 'delivered'
GROUP BY c.first_name, c.last_name;

SELECT * FROM dbo.orders WHERE customer_id = 42 AND status = 'pending';

SELECT oi.order_id, SUM(oi.qty * oi.unit_price) AS line_total
FROM dbo.order_items oi
WHERE oi.product_id = 7
GROUP BY oi.order_id;
GO

PRINT 'shopdb seeded: 500 customers, 200 products, 2000 orders, 6000 items.';
GO
