-- Time Dimension
CREATE TABLE time_dim (
    time_key INT IDENTITY(1,1) PRIMARY KEY,
    order_date DATE,
    year INT,
    quarter INT,
    month INT,
    day INT
) SORTKEY(order_date);


-- Customers Dimension
CREATE TABLE customers_dim (
    customer_key INT IDENTITY(1,1) PRIMARY KEY,
    customer_id VARCHAR(20),
    customer_name VARCHAR(100),
    segment VARCHAR(50),
    country VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    postal_code VARCHAR(10),
    region VARCHAR(20)
) DISTKEY(customer_id);

-- Products Dimension
CREATE TABLE products_dim (
    product_key INT IDENTITY(1,1) PRIMARY KEY,
    product_id VARCHAR(20),
    product_name VARCHAR(200),
    category VARCHAR(50),
    sub_category VARCHAR(50)
) DISTKEY(product_id);

-- Sales Facts
CREATE TABLE sales_facts (
    sales_key INT IDENTITY(1,1) PRIMARY KEY,
    order_id VARCHAR(20),
    time_key INT,
    customer_key INT,
    product_key INT,
    sales FLOAT,
    FOREIGN KEY (time_key) REFERENCES time_dim(time_key),
    FOREIGN KEY (customer_key) REFERENCES customers_dim(customer_key),
    FOREIGN KEY (product_key) REFERENCES products_dim(product_key)
) DISTKEY(customer_key) SORTKEY(time_key);