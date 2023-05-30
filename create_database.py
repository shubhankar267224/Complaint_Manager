import sqlite3

conn = sqlite3.connect('database/complaints.db')

# Create the complaints table
conn.execute('''CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    name TEXT,
    gender TEXT,
    phone_number TEXT,
    email_address TEXT,
    product_service TEXT,
    complaint TEXT,
    solved INTEGER DEFAULT 0,
    admin_comment TEXT
)''')

# Create the admin_comments table
conn.execute('''CREATE TABLE IF NOT EXISTS admin_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER,
    admin_comment TEXT,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id)
)''')

conn.commit()
conn.close()
