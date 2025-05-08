-- Boutique Database SQL Dump
CREATE DATABASE IF NOT EXISTS boutique_db;

USE boutique_db;

-- Customers Table
CREATE TABLE
  Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    address TEXT,
    password VARCHAR(255) NOT NULL
  );

-- Products Table
CREATE TABLE
  Products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2),
    image_url VARCHAR(255)
  );

-- Orders Table
CREATE TABLE
  Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status ENUM ('Order Placed', 'Delivered', 'Cancelled') DEFAULT 'Order Placed',
    FOREIGN KEY (customer_id) REFERENCES Customers (customer_id) ON DELETE CASCADE
  );

-- Order_Items Table
CREATE TABLE
  order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    customer_id INT,
    quantity INT,
    FOREIGN KEY (order_id) REFERENCES Orders (order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products (product_id),
    FOREIGN KEY (customer_id) REFERENCES Customers (customer_id)
  );

-- Employees Table
CREATE TABLE
  Employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role ENUM ('Manager', 'Salesperson', 'Cashier'),
    phone VARCHAR(15),
    email VARCHAR(100) UNIQUE
  );

-- Contact Messages Table
CREATE TABLE
  contact_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    message TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
