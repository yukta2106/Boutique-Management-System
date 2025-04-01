CREATE DATABASE boutique_db;
USE boutique_db;

CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    address TEXT,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE Products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INT DEFAULT 0
);

CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2),
    status ENUM('Pending', 'Completed', 'Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);

CREATE TABLE Order_Items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE CASCADE
);

CREATE TABLE Employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role ENUM('Manager', 'Salesperson', 'Cashier'),
    phone VARCHAR(15),
    email VARCHAR(100) UNIQUE
);

CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10,2),
    payment_method ENUM('Cash', 'Card', 'UPI') DEFAULT 'Cash',
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE
);

CREATE VIEW OrderSummary AS
SELECT o.order_id, c.name AS customer_name, o.order_date, o.total_amount, o.status
FROM Orders o
JOIN Customers c ON o.customer_id = c.customer_id;

DELIMITER //
CREATE TRIGGER update_stock_after_order
AFTER INSERT ON Order_Items
FOR EACH ROW
BEGIN
    UPDATE Products 
    SET stock = stock - NEW.quantity 
    WHERE product_id = NEW.product_id;
END;
//
DELIMITER ;

DELIMITER //
CREATE TRIGGER restore_stock_after_cancel
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF NEW.status = 'Cancelled' THEN
        UPDATE Products 
        SET stock = stock + (SELECT quantity FROM Order_Items WHERE order_id = NEW.order_id)
        WHERE product_id IN (SELECT product_id FROM Order_Items WHERE order_id = NEW.order_id);
    END IF;
END;
//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE GetSalesReport()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE orderId INT;
    DECLARE total DECIMAL(10,2);
    
    -- Declare a cursor to loop through orders
    DECLARE order_cursor CURSOR FOR
    SELECT order_id, total_amount FROM Orders;
    
    -- Declare a handler for loop end
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
    
    OPEN order_cursor;
    
    sales_loop: LOOP
        FETCH order_cursor INTO orderId, total;
        IF done THEN 
            LEAVE sales_loop;
        END IF;
        
        -- Display each order's details
        SELECT CONCAT('Order ID: ', orderId, ' - Total: ', total) AS SalesReport;
    END LOOP;
    
    CLOSE order_cursor;
END;
//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE AddCustomer(
    IN cust_name VARCHAR(100), 
    IN cust_email VARCHAR(100), 
    IN cust_phone VARCHAR(15), 
    IN cust_address TEXT, 
    IN cust_password VARCHAR(255)
)
BEGIN
    INSERT INTO Customers (name, email, phone, address, password)
    VALUES (cust_name, cust_email, cust_phone, cust_address, cust_password);
END;
//
DELIMITER ;

CALL AddCustomer('Mainak Sen', 'mainak@example.com', '9876543210', 'Chennai, India', 'securepass');

SHOW TABLES;
DESC Customers;
DESC Orders;
DESC Order_Items;
DESC Employees;
DESC Payments;
DESC Products;

SELECT * FROM OrderSummary;
CALL GetSalesReport();
