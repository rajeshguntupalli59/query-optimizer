-- ============================================================
-- QueryOptimizer — Sample Test Database
-- Database: shopdb
-- Run this entire script after connecting to your test DB
-- ============================================================

-- Enable slow query tracking (PostgreSQL only)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- ============================================================
-- SCHEMA
-- ============================================================

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders     CASCADE;
DROP TABLE IF EXISTS products   CASCADE;
DROP TABLE IF EXISTS customers  CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(200) NOT NULL UNIQUE,
    phone       VARCHAR(20),
    city        VARCHAR(100),
    country     VARCHAR(100) DEFAULT 'US',
    created_at  TIMESTAMP DEFAULT NOW(),
    is_active   BOOLEAN DEFAULT TRUE
    -- NOTE: no index on email (intentional — Index Advisor will catch this)
);

CREATE TABLE products (
    id           SERIAL PRIMARY KEY,
    category_id  INT REFERENCES categories(id),
    name         VARCHAR(200) NOT NULL,
    sku          VARCHAR(50),
    price        NUMERIC(10,2) NOT NULL,
    stock_qty    INT DEFAULT 0,
    created_at   TIMESTAMP DEFAULT NOW()
    -- NOTE: no index on category_id FK (intentional)
);

CREATE TABLE orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INT REFERENCES customers(id),
    status       VARCHAR(50) DEFAULT 'pending',
    total_amount NUMERIC(10,2),
    created_at   TIMESTAMP DEFAULT NOW(),
    shipped_at   TIMESTAMP
    -- NOTE: no index on customer_id or status (intentional)
);

CREATE TABLE order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INT REFERENCES orders(id),
    product_id  INT REFERENCES products(id),
    quantity    INT NOT NULL,
    unit_price  NUMERIC(10,2) NOT NULL
);

-- ============================================================
-- SAMPLE DATA
-- ============================================================

INSERT INTO categories (name, description) VALUES
  ('Electronics',   'Phones, laptops, gadgets'),
  ('Clothing',      'Apparel and accessories'),
  ('Books',         'Print and digital books'),
  ('Home & Garden', 'Furniture and tools'),
  ('Sports',        'Equipment and gear');

-- 500 customers
INSERT INTO customers (first_name, last_name, email, phone, city, country)
SELECT
    'First'  || i,
    'Last'   || i,
    'user'   || i || '@example.com',
    '555-'   || LPAD(i::text, 4, '0'),
    (ARRAY['New York','London','Paris','Tokyo','Sydney','Berlin','Toronto'])[1 + (i % 7)],
    (ARRAY['US','UK','FR','JP','AU','DE','CA'])[1 + (i % 7)]
FROM generate_series(1, 500) i;

-- 200 products
INSERT INTO products (category_id, name, sku, price, stock_qty)
SELECT
    1 + (i % 5),
    'Product ' || i,
    'SKU-' || LPAD(i::text, 5, '0'),
    (5 + (i * 7.3))::NUMERIC(10,2),
    (i * 3) % 200
FROM generate_series(1, 200) i;

-- 2000 orders
INSERT INTO orders (customer_id, status, total_amount, created_at)
SELECT
    1 + (i % 500),
    (ARRAY['pending','processing','shipped','delivered','cancelled'])[1 + (i % 5)],
    (20 + (i * 4.7))::NUMERIC(10,2),
    NOW() - ((i % 365) || ' days')::INTERVAL
FROM generate_series(1, 2000) i;

-- 6000 order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    1 + (i % 2000),
    1 + (i % 200),
    1 + (i % 5),
    (10 + (i * 2.3))::NUMERIC(10,2)
FROM generate_series(1, 6000) i;

-- Refresh statistics
ANALYZE;

SELECT 'Test database ready!' AS status,
       (SELECT COUNT(*) FROM customers) AS customers,
       (SELECT COUNT(*) FROM products)  AS products,
       (SELECT COUNT(*) FROM orders)    AS orders,
       (SELECT COUNT(*) FROM order_items) AS order_items;
