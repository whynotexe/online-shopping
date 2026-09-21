-- ==========================================================
-- ONLINE SHOPPING SYSTEM - DATABASE SCRIPT
-- ==========================================================
-- Run this entire file in MySQL (Workbench, command line, etc.)
-- It creates the database, all tables, one admin account,
-- and a few sample products to get started.
-- ==========================================================

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS online_shopping;
USE online_shopping;

-- 2. USERS table - stores customer accounts
CREATE TABLE IF NOT EXISTS users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password    VARCHAR(100) NOT NULL,
    phone       VARCHAR(15)  NOT NULL
);

-- 3. PRODUCTS table - stores items available for sale
CREATE TABLE IF NOT EXISTS products (
    product_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category     VARCHAR(50)  NOT NULL,
    price        DECIMAL(10,2) NOT NULL,
    quantity     INT NOT NULL DEFAULT 0
);

-- 4. CART table - temporary items a user has added before ordering
CREATE TABLE IF NOT EXISTS cart (
    cart_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    product_id  INT NOT NULL,
    quantity    INT NOT NULL,
    FOREIGN KEY (user_id)    REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 5. ORDERS table - one row per placed order
CREATE TABLE IF NOT EXISTS orders (
    order_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    customer_name  VARCHAR(100) NOT NULL,
    address        VARCHAR(255) NOT NULL,
    phone          VARCHAR(15)  NOT NULL,
    total_amount   DECIMAL(10,2) NOT NULL,
    order_status   VARCHAR(20) NOT NULL DEFAULT 'Pending',
    order_date     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 6. ORDER_ITEMS table - the individual products inside each order
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id  INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT NOT NULL,
    product_id     INT NOT NULL,
    quantity       INT NOT NULL,
    price          DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 7. ADMIN table - login credentials for the admin panel
CREATE TABLE IF NOT EXISTS admin (
    admin_id  INT AUTO_INCREMENT PRIMARY KEY,
    username  VARCHAR(50) NOT NULL UNIQUE,
    password  VARCHAR(50) NOT NULL
);

-- ==========================================================
-- SAMPLE DATA
-- ==========================================================

-- Default admin login -> username: admin , password: admin123
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');

-- A few sample products across different categories
INSERT INTO products (product_name, category, price, quantity) VALUES
('Laptop',        'Electronics', 45000.00, 10),
('Mobile Phone',  'Electronics', 15000.00, 20),
('Headphones',    'Electronics',  1200.00, 50),
('Notebook',      'Stationery',     40.00, 100),
('Pen',           'Stationery',     10.00, 200),
('Backpack',      'Accessories',   900.00, 30),
('Water Bottle',  'Accessories',   250.00, 40),
('T-Shirt',       'Clothing',      500.00, 60);
