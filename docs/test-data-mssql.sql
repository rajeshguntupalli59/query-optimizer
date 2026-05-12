-- ============================================================
-- QueryOptimizer -- Sample Test Database (SQL Server)
-- Database: shopdb
-- Run this entire script after connecting to your test DB
-- ============================================================

USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = 'shopdb')
    DROP DATABASE shopdb;
GO

CREATE DATABASE shopdb;
GO

USE shopdb;
GO

-- ============================================================
-- SCHEMA
-- ============================================================

CREATE TABLE categories (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    name        NVARCHAR(100) NOT NULL,
    description NVARCHAR(MAX)
);

CREATE TABLE customers (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    first_name  NVARCHAR(100) NOT NULL,
    last_name   NVARCHAR(100) NOT NULL,
    email       NVARCHAR(200) NOT NULL UNIQUE,
    phone       NVARCHAR(20),
    city        NVARCHAR(100),
    country     NVARCHAR(100) DEFAULT 'US',
    created_at  DATETIME DEFAULT GETDATE(),
    is_active   BIT DEFAULT 1
    -- NOTE: no index on country (intentional -- Index Advisor will catch this)
);

CREATE TABLE products (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    category_id INT REFERENCES categories(id),
    name        NVARCHAR(200) NOT NULL,
    sku         NVARCHAR(50),
    price       DECIMAL(10,2) NOT NULL,
    stock_qty   INT DEFAULT 0,
    created_at  DATETIME DEFAULT GETDATE()
    -- NOTE: no index on category_id FK (intentional)
);

CREATE TABLE orders (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    customer_id  INT REFERENCES customers(id),
    status       NVARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10,2),
    created_at   DATETIME DEFAULT GETDATE(),
    shipped_at   DATETIME
    -- NOTE: no index on customer_id or status (intentional)
);

CREATE TABLE order_items (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    order_id    INT REFERENCES orders(id),
    product_id  INT REFERENCES products(id),
    quantity    INT NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL
);
GO

-- ============================================================
-- SAMPLE DATA
-- ============================================================

INSERT INTO categories (name, description) VALUES
    ('Electronics',   'Phones, laptops, gadgets'),
    ('Clothing',      'Apparel and accessories'),
    ('Books',         'Print and digital books'),
    ('Home & Garden', 'Furniture and tools'),
    ('Sports',        'Equipment and gear');
GO

-- 500 customers
WITH nums AS (
    SELECT TOP 500 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.objects a CROSS JOIN sys.objects b
)
INSERT INTO customers (first_name, last_name, email, phone, city, country)
SELECT
    'First' + CAST(i AS NVARCHAR),
    'Last'  + CAST(i AS NVARCHAR),
    'user'  + CAST(i AS NVARCHAR) + '@example.com',
    '555-'  + RIGHT('0000' + CAST(i AS NVARCHAR), 4),
    CHOOSE(1 + (i % 7), 'New York','London','Paris','Tokyo','Sydney','Berlin','Toronto'),
    CHOOSE(1 + (i % 7), 'US','UK','FR','JP','AU','DE','CA')
FROM nums;
GO

-- 200 products
WITH nums AS (
    SELECT TOP 200 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.objects a CROSS JOIN sys.objects b
)
INSERT INTO products (category_id, name, sku, price, stock_qty)
SELECT
    1 + (i % 5),
    'Product ' + CAST(i AS NVARCHAR),
    'SKU-' + RIGHT('00000' + CAST(i AS NVARCHAR), 5),
    CAST(5 + (i * 7.3) AS DECIMAL(10,2)),
    (i * 3) % 200
FROM nums;
GO

-- 2000 orders
WITH nums AS (
    SELECT TOP 2000 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.objects a CROSS JOIN sys.objects b
)
INSERT INTO orders (customer_id, status, total_amount, created_at)
SELECT
    1 + (i % 500),
    CHOOSE(1 + (i % 5), 'pending','processing','shipped','delivered','cancelled'),
    CAST(20 + (i * 4.7) AS DECIMAL(10,2)),
    DATEADD(day, -(i % 365), GETDATE())
FROM nums;
GO

-- 6000 order items
WITH nums AS (
    SELECT TOP 6000 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.objects a CROSS JOIN sys.objects b
)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    1 + (i % 2000),
    1 + (i % 200),
    1 + (i % 5),
    CAST(10 + (i * 2.3) AS DECIMAL(10,2))
FROM nums;
GO

-- Verify
SELECT
    'Test database ready!' AS status,
    (SELECT COUNT(*) FROM customers)   AS customers,
    (SELECT COUNT(*) FROM products)    AS products,
    (SELECT COUNT(*) FROM orders)      AS orders,
    (SELECT COUNT(*) FROM order_items) AS order_items;
GO
