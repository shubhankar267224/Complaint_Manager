from flask import Flask, render_template, request, redirect, url_for, g, make_response, send_file, flash 
import secrets
import sqlite3
import os
import io
import csv
from werkzeug.datastructures import Headers
from flask import Response


# Generate a secret key
secret_key = secrets.token_hex(16)

# Create the Flask application
app = Flask(__name__)

# Set the secret key for the Flask application
#app.secret_key = secret_key

# Rest of your Flask application code follows...


app.secret_key = secret_key

DATABASE = 'database/complaints.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
            #try:
            db = g._database = sqlite3.connect(DATABASE)
            #except sqlite3.Error as e:
            # Log the error or print it for debugging
            #print("Error connecting to the database:", e)
            db.execute("PRAGMA foreign_keys = 1")  # Enable foreign key support
    return db


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create the "complaints" table if it doesn't exist
        cursor.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         customer_id INTEGER,
         name TEXT,
         gender TEXT,
         phone_number TEXT,
         email_address TEXT,
         product_service TEXT,
         complaint TEXT,
         admin_comment TEXT,
         solved INTEGER DEFAULT 0
    )
''')


        # Create the "solved" table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solved (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER,
                solved INTEGER,
                FOREIGN KEY (complaint_id) REFERENCES complaints (id)
            )
        ''')

        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        print(request.form) #line for debugging
        customer_id = request.form['customer_id']
        name = request.form['name']
        gender = request.form['gender']
        phone_number = request.form['phone_number']
        email_address = request.form['email_address']
        product_service = request.form['product_service']
        complaint_text = request.form['complaint']


        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO complaints (customer_id, name, gender, phone_number, email_address, product_service, complaint)'
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (customer_id, name, gender, phone_number, email_address, product_service, complaint_text)
        )
        db.commit()
        return redirect(url_for('home'))

    return render_template('complaint.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'Adm00rp':
            return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html')



@app.route('/admin/dashboard')
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()

    # Check if the "solved" table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='solved'")
    table_exists = cursor.fetchone()

    if table_exists:
        cursor.execute('''
            SELECT c.id, c.customer_id, c.name, c.gender, c.phone_number, c.email_address,
               c.product_service, c.complaint, c.admin_comment, COALESCE(s.solved, 0)
        FROM complaints c
        LEFT JOIN solved s ON c.id = s.complaint_id
        ''')
        complaints = cursor.fetchall()
    else:
        complaints = []

    # Fetch admin comments for each complaint
    cursor.execute('SELECT id, admin_comment FROM complaints')
    comments = cursor.fetchall()
    comments_dict = {comment[0]: comment[1] for comment in comments}

    return render_template('admin_dashboard.html', complaints=complaints, comments=comments_dict)




@app.route('/admin/solved/<int:complaint_id>', methods=['GET', 'POST'])
def mark_solved(complaint_id):
    db = get_db()
    cursor = db.cursor()
    admin_comment = "" # Initialize with default value

    if request.method == 'POST':
        admin_comment = request.form['admin_comment']
        #db = get_db()
        #cursor = db.cursor()

    # Update the solved column and admin_comment column in the complaints table
    cursor.execute('UPDATE complaints SET solved = ?, admin_comment = ? WHERE id = ?',
                   (1, admin_comment, complaint_id))

    db.commit()
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/add_comment', methods=['POST'])
def add_comment():
    complaint_id = request.form['complaint_id']
    admin_comment = request.form['admin_comment']
    db = get_db()
    cursor = db.cursor()

    # Update the admin_comment column in the complaints table
    cursor.execute('UPDATE complaints SET admin_comment = ? WHERE id = ?', (admin_comment, complaint_id))

    db.commit()
    flash('Admin comment added Successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete/<int:complaint_id>', methods=['GET', 'POST'])
def delete_complaint(complaint_id):
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()

        # Delete the complaint from the complaints table
        cursor.execute('DELETE FROM complaints WHERE id = ?', (complaint_id,))

        db.commit()
        return redirect(url_for('admin_dashboard'))
    else:
        # Handle GET requests if needed
        # For example, you can show a confirmation page before deleting the complaint
        return render_template('confirm_delete.html', complaint_id=complaint_id)




@app.route('/admin/download')
def download():
    db = get_db()
    cursor = db.cursor()

    # Check if the "solved" table exists
    #cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='solved'")
    cursor.execute('SELECT id, customer_id, name, gender, phone_number, email_address, product_service, complaint, admin_comment, solved FROM complaints')
    complaints = cursor.fetchall()
    #table_exists = cursor.fetchone()

    #if table_exists:
    #    complaints = cursor.execute('''
    #        SELECT c.id, c.customer_id, c.name, c.gender, c.phone_number, c.email_address,
    #               c.product_service, c.complaint, c.admin_comment, s.solved
    #        FROM complaints c
    #        JOIN solved s ON c.id = s.complaint_id
    #    ''').fetchall()
    #else:
    #    complaints = []

    # Prepare the CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Complaint ID', 'Customer ID', 'Name', 'Gender', 'Phone Number', 'Email Address', 'Product/Service', 'Complaint', 'Admin Comment', 'Solved'])

    for complaint in complaints:
        complaint_id, customer_id, name, gender, phone_number, email_address, product_service, complaint_text, admin_comment, solved = complaint
        solved_text = 'YES' if solved else 'NO'
        writer.writerow([complaint_id, customer_id, name, gender, phone_number, email_address, 
                         product_service, complaint_text, admin_comment if admin_comment else '', solved_text])

    # Set up the response headers
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=complaints.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    if not os.path.exists('database/complaints.db'):
        init_db()
    app.run(debug=True)
