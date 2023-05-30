-- schema.sql

-- Drop existing tables (if any)
DROP TABLE IF EXISTS complaints;
DROP TABLE IF EXISTS solved;

-- Create complaints table
CREATE TABLE complaints (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    name TEXT,
    gender TEXT,
    phone_number TEXT,
    email_address TEXT,
    product_service TEXT,
    complaint TEXT,
    admin_comment TEXT,
    solved INTEGER
);


-- Create solved table
CREATE TABLE solved (
    id INTEGER PRIMARY KEY,
    complaint_id INTEGER,
    solved INTEGER,
    FOREIGN KEY (complaint_id) REFERENCES complaints (id)
);

ALTER TABLE complaints ADD COLUMN email_address TEXT;
