PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

DROP TABLE IF EXISTS sale_items;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS credit_payments;
DROP TABLE IF EXISTS credit_customers;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('ADMIN', 'STAFF'))
);

INSERT INTO users (name, username, password, role) VALUES
('Juan Dela Cruz', 'admin', 'admin123', 'ADMIN'),
('Maria Santos', 'cashier1', 'cashier123', 'STAFF'),
('Pedro Reyes', 'staff1', 'staff123', 'STAFF');

CREATE TABLE credit_customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    total_credit REAL NOT NULL DEFAULT 0.00,
    total_paid REAL NOT NULL DEFAULT 0.00,
    balance REAL NOT NULL DEFAULT 0.00,
    status TEXT NOT NULL DEFAULT 'UNPAID' CHECK(status IN ('UNPAID', 'PARTIAL', 'PAID')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO credit_customers(customer_name, phone, address, total_credit, total_paid, balance, status) VALUES
('Jose Ramirez', '09171234567', 'Cebu City', 5000.00, 2000.00, 3000.00, 'PARTIAL'),
('Maria Lopez', '09179876543', 'Mandaue City', 2500.00, 0.00, 2500.00, 'UNPAID');

CREATE TABLE credit_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    credit_customer_id INTEGER NOT NULL,
    amount_paid REAL NOT NULL,
    payment_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (credit_customer_id)
        REFERENCES credit_customers(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

INSERT INTO credit_payments (credit_customer_id, amount_paid, notes) VALUES
(1, 1000.00, 'Partial payment');

CREATE TABLE categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_name TEXT NOT NULL
);

INSERT INTO categories (category_name) VALUES
('Construction Materials'),
('Electrical Supplies'),
('Plumbing Supplies'),
('Hardware Tools'),
('Paint Supplies'),
('Fasteners'),
('Safety Equipment'),
('Garden Tools'),
('Automotive Tools'),
('Household Supplies');

CREATE TABLE suppliers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  supplier_name TEXT NOT NULL,
  contact_person TEXT,
  phone TEXT,
  email TEXT,
  address TEXT
);

INSERT INTO suppliers (supplier_name, contact_person, phone, email, address) VALUES
('ABC Construction Supply', 'Ramon Santos', '09179876543', 'ramon@abc.com', '123 Mabini St, Cebu City'),
('Best Hardware Co.', 'Liza Cruz', '09171234567', 'liza@besthardware.com', '456 Rizal Ave, Cebu City'),
('Cebu Building Materials', 'Jose Dela Cruz', '09171112222', 'jose@cebubuild.com', '789 P. Burgos St, Cebu City'),
('Prime Electrical Supply', 'Mark Lim', '09173334444', 'mark@primeelectrical.com', '101 Colon St, Cebu City'),
('Reliable Plumbing Supply', 'Ana Reyes', '09175556666', 'ana@reliableplumbing.com', '202 Mango Ave, Cebu City'),
('Strong Tools Trading', 'Robert Tan', '09177778888', 'robert@strongtools.com', '303 Jones Ave, Cebu City'),
('ColorPro Paint Supply', 'Grace Ong', '09179990000', 'grace@colorpro.com', '404 Osmena Blvd, Cebu City'),
('SafeWork Equipment', 'Kevin Go', '09172223333', 'kevin@safework.com', '505 Banilad Rd, Cebu City'),
('GardenPro Supplies', 'Nicole Sy', '09174445555', 'nicole@gardenpro.com', '606 Talamban Rd, Cebu City'),
('HomeFix Trading', 'Brian Chua', '09176667777', 'brian@homefix.com', '707 Lahug Rd, Cebu City');

CREATE TABLE products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_name TEXT NOT NULL,
  category_id INTEGER NOT NULL,
  supplier_id INTEGER NOT NULL,
  price REAL NOT NULL,
  cost REAL NOT NULL,
  stock_quantity INTEGER NOT NULL,
  reorder_level INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (category_id)
    REFERENCES categories(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  FOREIGN KEY (supplier_id)
    REFERENCES suppliers(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
);

INSERT INTO products (product_name, category_id, supplier_id, price, cost, stock_quantity, reorder_level) VALUES
('Cement 40kg', 1, 1, 250.00, 220.00, 100, 10),
('Electrical Wire 2.0mm', 2, 4, 850.00, 750.00, 50, 10),
('PVC Pipe 1/2 inch', 3, 5, 120.00, 90.00, 80, 15),
('Claw Hammer 16oz', 4, 6, 350.00, 280.00, 40, 10),
('Paint Brush 4 inch', 5, 7, 85.00, 60.00, 60, 10),
('Common Nails 2 inch', 6, 2, 95.00, 70.00, 150, 20),
('Safety Helmet', 7, 8, 180.00, 140.00, 50, 10),
('Garden Shovel', 8, 9, 450.00, 350.00, 30, 5),
('Adjustable Wrench', 9, 6, 280.00, 220.00, 45, 10),
('Cleaning Brush', 10, 10, 75.00, 50.00, 70, 10);

CREATE TABLE sales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_number TEXT NOT NULL UNIQUE,
  user_id INTEGER NOT NULL,
  total_amount REAL NOT NULL,
  payment_method TEXT NOT NULL CHECK(payment_method IN ('Cash', 'GCash', 'Bank Transfer', 'Credit/Utang')),
  amount_received REAL,
  change_amount REAL,
  sale_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
);

INSERT INTO sales(invoice_number, user_id, total_amount, payment_method, amount_received, change_amount, sale_date) VALUES
('INV-2026-001', 1, 500.00, 'Cash', 1000.00, 500.00, '2026-08-01 09:15:00'),
('INV-2026-002', 2, 700.00, 'GCash', 700.00, 0.00, '2026-08-02 10:20:00'),
('INV-2026-003', 3, 850.00, 'Cash', 1000.00, 150.00, '2026-08-03 11:10:00');

CREATE TABLE sale_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sale_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  price REAL NOT NULL,
  cost REAL NOT NULL,
  subtotal REAL NOT NULL,

  FOREIGN KEY (sale_id)
    REFERENCES sales(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  FOREIGN KEY (product_id)
    REFERENCES products(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
);

INSERT INTO sale_items (sale_id, product_id, quantity, price, cost, subtotal) VALUES
(1, 1, 2, 250.00, 220.00, 500.00),
(2, 2, 1, 850.00, 750.00, 850.00),
(3, 3, 10, 85.00, 60.00, 850.00);

COMMIT;
