-- 1. جدول المتاجر
CREATE TABLE IF NOT EXISTS stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    store_type VARCHAR(30) CHECK (store_type IN ('Flagship', 'Standard', 'Express'))
);

-- 2. جدول المنتجات
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit_cost DECIMAL(10, 2) NOT NULL CHECK (unit_cost >= 0),
    base_price DECIMAL(10, 2) NOT NULL CHECK (base_price >= unit_cost)
);

-- 3. جدول المبيعات اليومية (السلسلة الزمنية)
CREATE TABLE IF NOT EXISTS daily_sales (
    sale_id BIGSERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    store_id INT NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    units_sold INT NOT NULL CHECK (units_sold >= 0),
    selling_price DECIMAL(10, 2) NOT NULL CHECK (selling_price >= 0),
    is_promotion BOOLEAN NOT NULL DEFAULT FALSE,
    temperature_c DECIMAL(4, 1),
    UNIQUE (sale_date, store_id, product_id)
);