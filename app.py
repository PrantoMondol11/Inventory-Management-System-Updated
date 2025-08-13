from flask import Flask, render_template, session, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
from flask_bcrypt import Bcrypt
from wtforms import SelectField
import mysql.connector
from mysql.connector import Error
import traceback
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'my_secret_key_here'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'newdb',
    'port': 3306
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        traceback.print_exc()
        return None

# Test database connection
def test_db_connection():
    try:
        conn = get_db_connection()
        if conn:
            print("Successfully connected to MySQL database!")
            conn.close()
            return True
        else:
            print("Failed to connect to MySQL database!")
            return False
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        traceback.print_exc()
        return False

# Test connection on startup
test_db_connection()

# Routes
@app.route('/')
@app.route('/dashboard')
def dashboard():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('dashboard.html')

        cur = conn.cursor()
        
        # Get counts for dashboard
        cur.execute("SELECT COUNT(*) FROM user")
        user_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM project")
        project_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM committee")
        committee_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM item")
        item_count = cur.fetchone()[0]
        
        # Get recent transactions
        cur.execute("""
            SELECT t.transaction_id, t.amount, t.transaction_type, t.transaction_date, p.project_name
            FROM transaction t
            LEFT JOIN project p ON t.project_id = p.project_id
            ORDER BY t.transaction_date DESC
            LIMIT 5
        """)
        recent_transactions = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('dashboard.html', 
                             user_count=user_count,
                             project_count=project_count,
                             committee_count=committee_count,
                             item_count=item_count,
                             recent_transactions=recent_transactions)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('dashboard.html')

@app.route('/users', methods=['GET', 'POST'])
def users():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('users.html', users=[])

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            role = request.form['role']

            cur.execute("""
                INSERT INTO user (name, email, role, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (name, email, role))
            conn.commit()
            flash('User added successfully!', 'success')

        cur.execute("SELECT user_id, name, email, role, created_at FROM user")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        users = [{"id": r[0], "name": r[1], "email": r[2], "role": r[3], "created_at": r[4]} for r in rows]
        return render_template('users.html', users=users)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        traceback.print_exc()
        return render_template('users.html', users=[])

@app.route('/committees', methods=['GET', 'POST'])
def committees_page():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('committees.html', committees=[])

        cur = conn.cursor()
        
        if request.method == 'POST':
            name = request.form['name']
            ctype = request.form['type']
            user_name = request.form['user_name']

            cur.execute("""
                INSERT INTO committee (committee_name, committee_type, created_at, user_name)
                VALUES (%s, %s, NOW(), %s)
            """, (name, ctype, user_name))
            conn.commit()
            flash('Committee added successfully!', 'success')
            return redirect(url_for('committees_page'))

        cur.execute("""
            SELECT committee_id, committee_name, committee_type, created_at, user_name
            FROM committee
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()

        committees = [
            {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "created_at": row[3],
                "created_by": row[4]
            } for row in data
        ]
        return render_template('committees.html', committees=committees)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        traceback.print_exc()
        return render_template('committees.html', committees=[])

@app.route('/projects', methods=['GET', 'POST'])
def projects():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('projects.html', projects=[], committees=[])

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            status = request.form['status']
            committee_id = request.form['committee_id']

            cur.execute("""
                INSERT INTO project (project_name, start_date, end_date, status, committee_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, start_date, end_date, status, committee_id))
            conn.commit()
            flash('Project added successfully!', 'success')

        # Get all committees for the dropdown
        cur.execute("""
            SELECT committee_id, committee_name 
            FROM committee 
            ORDER BY committee_name
        """)
        committees_data = cur.fetchall()
        committees = [{"id": row[0], "name": row[1]} for row in committees_data]

        # Get projects with committee names
        cur.execute("""
            SELECT p.project_id, p.project_name, p.start_date, p.end_date, p.status, 
                   c.committee_name
            FROM project p
            LEFT JOIN committee c ON p.committee_id = c.committee_id
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        projects = [
            {
                "id": row[0],
                "name": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "status": row[4],
                "committee": row[5] if row[5] else "No Committee"
            }
            for row in rows
        ]
        return render_template('projects.html', projects=projects, committees=committees)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        traceback.print_exc()
        return render_template('projects.html', projects=[], committees=[])

@app.route('/funds', methods=['GET', 'POST'])
def funds():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('funds.html', funds=[], projects=[])

        cur = conn.cursor()

        if request.method == 'POST':
            amount = float(request.form['amount'])
            project_id = request.form['project_id']
            purpose = request.form['purpose']
            description = request.form['description']

            # Start transaction
            conn.start_transaction()

            try:
                # Insert fund record with pending status
                cur.execute("""
                    INSERT INTO fund (amount, project_id, purpose, description, status, created_at)
                    VALUES (%s, %s, %s, %s, 'pending', NOW())
                """, (amount, project_id, purpose, description))

                conn.commit()
                flash('Fund request submitted successfully!', 'success')
            except Error as e:
                conn.rollback()
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('funds'))

        # Get all projects for the dropdown
        cur.execute("""
            SELECT project_id, project_name 
            FROM project 
            ORDER BY project_name
        """)
        projects_data = cur.fetchall()
        projects = [{"id": row[0], "name": row[1]} for row in projects_data]

        # Get funds with project names and remaining budget
        cur.execute("""
            SELECT f.fund_id, f.amount, f.purpose, f.description, f.created_at,
                   p.project_name, pb.allocated_amount as remaining_budget, f.status
            FROM fund f
            LEFT JOIN project p ON f.project_id = p.project_id
            LEFT JOIN project_budget pb ON f.project_id = pb.project_id
            ORDER BY f.created_at DESC
        """)
        funds_data = cur.fetchall()
        
        # Close cursor and connection
        cur.close()
        conn.close()

        funds = [
            {
                "id": row[0],
                "amount": row[1],
                "purpose": row[2],
                "description": row[3],
                "date": row[4],
                "project": row[5] if row[5] else "No Project",
                "remaining_budget": row[6] if row[6] else 0,
                "status": row[7]
            }
            for row in funds_data
        ]
        
        return render_template('funds.html', funds=funds, projects=projects)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('funds.html', funds=[], projects=[])

@app.route('/budgets', methods=['GET', 'POST'])
def budgets():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('budgets.html', total_balance=0, last_updated=datetime.now())

        cur = conn.cursor()

        if request.method == 'POST':
            amount = float(request.form['amount'])

            # Start transaction
            conn.start_transaction()

            try:
                # Check if budget exists
                cur.execute("SELECT budget_id, total_amount FROM budget LIMIT 1")
                budget = cur.fetchone()

                if budget:
                    # Update existing budget
                    cur.execute("""
                        UPDATE budget 
                        SET total_amount = total_amount + %s
                        WHERE budget_id = %s
                    """, (amount, budget[0]))
                else:
                    # Create new budget
                    cur.execute("""
                        INSERT INTO budget (total_amount)
                        VALUES (%s)
                    """, (amount,))

                conn.commit()
                flash(f'Added ${amount:.2f} to budget successfully!', 'success')
            except Error as e:
                conn.rollback()
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('budgets'))

        # Get total budget balance
        cur.execute("""
            SELECT total_amount, updated_at
            FROM budget
            LIMIT 1
        """)
        budget_data = cur.fetchone()
        
        total_balance = budget_data[0] if budget_data else 0
        last_updated = budget_data[1] if budget_data else datetime.now()

        cur.close()
        conn.close()

        return render_template('budgets.html', 
                             total_balance=total_balance,
                             last_updated=last_updated)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('budgets.html', total_balance=0, last_updated=datetime.now())

@app.route('/items', methods=['GET', 'POST'])
def items():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('items.html', items=[], suppliers=[], projects=[])

        cur = conn.cursor()

        if request.method == 'POST':
            try:
                # Get form data
                item_name = request.form['item_name']
                quantity = int(request.form['quantity'])
                unit_price = float(request.form['unit_price'])
                total_cost = quantity * unit_price
                project_id = request.form['project_id'] if request.form['project_id'] else None
                supplier_id = request.form['supplier_id'] if request.form['supplier_id'] else None
                purchased_at = request.form['purchased_at']

                # Insert into database
                cur.execute("""
                    INSERT INTO item (item_name, quantity, unit_price, total_cost, 
                                    project_id, supplier_id, purchased_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (item_name, quantity, unit_price, total_cost, project_id, supplier_id, purchased_at))
                
                conn.commit()
                flash('Item added successfully!', 'success')
                return redirect(url_for('items'))
            except Exception as e:
                conn.rollback()
                flash(f'Error adding item: {str(e)}', 'error')
                return redirect(url_for('items'))

        # Get all suppliers for dropdown
        cur.execute("""
            SELECT supplier_id, supplier_name 
            FROM supplier 
            ORDER BY supplier_name
        """)
        suppliers_data = cur.fetchall()
        suppliers = [{"id": row[0], "name": row[1]} for row in suppliers_data]

        # Get all projects for dropdown
        cur.execute("""
            SELECT project_id, project_name 
            FROM project 
            ORDER BY project_name
        """)
        projects_data = cur.fetchall()
        projects = [{"id": row[0], "name": row[1]} for row in projects_data]

        # Get items with project and supplier names
        cur.execute("""
            SELECT i.item_id, i.item_name, i.quantity, i.unit_price, i.total_cost,
                   p.project_name, s.supplier_name, i.purchased_at
            FROM item i
            LEFT JOIN project p ON i.project_id = p.project_id
            LEFT JOIN supplier s ON i.supplier_id = s.supplier_id
            ORDER BY i.purchased_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        items = [
            {
                "id": row[0],
                "name": row[1],
                "quantity": row[2],
                "unit_price": row[3],
                "total_cost": row[4],
                "project": row[5] if row[5] else "No Project",
                "supplier": row[6] if row[6] else "No Supplier",
                "date": row[7]
            }
            for row in rows
        ]
        return render_template('items.html', items=items, suppliers=suppliers, projects=projects)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        traceback.print_exc()
        return render_template('items.html', items=[], suppliers=[], projects=[])

@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('suppliers.html', suppliers=[])

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            address = request.form['address']

            cur.execute("""
                INSERT INTO supplier (supplier_name, contact_number, email, address)
                VALUES (%s, %s, %s, %s)
            """, (name, phone, email, address))
            conn.commit()
            flash('Supplier added successfully!', 'success')

        cur.execute("""
            SELECT supplier_id, supplier_name, contact_number, email, address 
            FROM supplier
            ORDER BY supplier_name
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        suppliers = [
            {
                "id": row[0],
                "name": row[1],
                "phone": row[2],
                "email": row[3],
                "address": row[4]
            }
            for row in rows
        ]
        return render_template('suppliers.html', suppliers=suppliers)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        traceback.print_exc()
        return render_template('suppliers.html', suppliers=[])

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('transactions.html', transactions=[])

        cur = conn.cursor()

        if request.method == 'POST':
            amount = float(request.form['amount'])
            purpose = request.form['purpose']
            description = request.form['description']
            date = request.form['date']

            # Start transaction
            conn.start_transaction()

            try:
                # Check if budget exists
                cur.execute("SELECT budget_id FROM budget LIMIT 1")
                budget = cur.fetchone()
                
                if not budget:
                    # Create initial budget if it doesn't exist
                    cur.execute("""
                        INSERT INTO budget (total_amount)
                        VALUES (0)
                    """)
                    budget_id = cur.lastrowid
                else:
                    budget_id = budget[0]

                # Insert transaction record
                cur.execute("""
                    INSERT INTO transaction (amount, purpose, description, transaction_date)
                    VALUES (%s, %s, %s, %s)
                """, (amount, purpose, description, date))

                # Add to total budget
                cur.execute("""
                    UPDATE budget 
                    SET total_amount = total_amount + %s
                    WHERE budget_id = %s
                """, (amount, budget_id))

                conn.commit()
                flash(f'Transaction of ৳{amount:.2f} recorded successfully!', 'success')
            except Error as e:
                conn.rollback()
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('transactions'))

        # Get transactions with current budget
        cur.execute("""
            SELECT t.transaction_id, t.amount, t.purpose, t.description, 
                   t.transaction_date, COALESCE(b.total_amount, 0) as current_budget
            FROM transaction t
            LEFT JOIN budget b ON b.budget_id = 1
            ORDER BY t.transaction_date DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        transactions = [
            {
                "id": row[0],
                "amount": row[1],
                "purpose": row[2],
                "description": row[3],
                "date": row[4],
                "current_budget": row[5]
            }
            for row in rows
        ]
        return render_template('transactions.html', transactions=transactions)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('transactions.html', transactions=[])

# Delete routes
@app.route('/committees/delete/<int:id>', methods=['POST'])
def delete_committee(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('committees_page'))

        cur = conn.cursor()
        cur.execute("DELETE FROM committee WHERE committee_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Committee deleted successfully!', 'success')
        return redirect(url_for('committees_page'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('committees_page'))

@app.route('/users/delete/<int:id>', methods=['POST'])
def delete_user(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('users'))

        cur = conn.cursor()
        cur.execute("DELETE FROM user WHERE user_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('User deleted successfully!', 'success')
        return redirect(url_for('users'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('users'))

@app.route('/projects/delete/<int:id>', methods=['POST'])
def delete_project(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('projects'))

        cur = conn.cursor()
        cur.execute("DELETE FROM project WHERE project_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Project deleted successfully!', 'success')
        return redirect(url_for('projects'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('projects'))

@app.route('/funds/delete/<int:id>', methods=['POST'])
def delete_fund(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('funds'))

        cur = conn.cursor()
        cur.execute("DELETE FROM fund WHERE fund_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Fund deleted successfully!', 'success')
        return redirect(url_for('funds'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('funds'))

@app.route('/budgets/delete/<int:id>', methods=['POST'])
def delete_budget(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('budgets'))

        cur = conn.cursor()
        cur.execute("DELETE FROM budget WHERE budget_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Budget deleted successfully!', 'success')
        return redirect(url_for('budgets'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('budgets'))

@app.route('/items/delete/<int:id>', methods=['POST'])
def delete_item(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('items'))

        cur = conn.cursor()
        cur.execute("DELETE FROM item WHERE item_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Item deleted successfully!', 'success')
        return redirect(url_for('items'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('items'))

@app.route('/suppliers/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('suppliers'))

        cur = conn.cursor()
        cur.execute("DELETE FROM supplier WHERE supplier_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Supplier deleted successfully!', 'success')
        return redirect(url_for('suppliers'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('suppliers'))

@app.route('/transactions/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('transactions'))

        cur = conn.cursor()
        cur.execute("DELETE FROM transaction WHERE transaction_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Transaction deleted successfully!', 'success')
        return redirect(url_for('transactions'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('transactions'))

# Edit routes
@app.route('/committees/edit/<int:id>', methods=['GET', 'POST'])
def edit_committee(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('committees_page'))

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            ctype = request.form['type']
            user_name = request.form['user_name']

            cur.execute("""
                UPDATE committee 
                SET committee_name = %s, committee_type = %s, user_name = %s
                WHERE committee_id = %s
            """, (name, ctype, user_name, id))
            conn.commit()
            flash('Committee updated successfully!', 'success')
            return redirect(url_for('committees_page'))

        cur.execute("SELECT committee_name, committee_type, user_name FROM committee WHERE committee_id = %s", (id,))
        committee = cur.fetchone()
        cur.close()
        conn.close()

        if committee:
            return render_template('edit_committee.html', 
                                 id=id,
                                 name=committee[0],
                                 type=committee[1],
                                 user_name=committee[2])
        else:
            flash('Committee not found!', 'error')
            return redirect(url_for('committees_page'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('committees_page'))

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('users'))

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            role = request.form['role']

            cur.execute("""
                UPDATE user 
                SET name = %s, email = %s, role = %s
                WHERE user_id = %s
            """, (name, email, role, id))
            conn.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('users'))

        cur.execute("SELECT name, email, role FROM user WHERE user_id = %s", (id,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            return render_template('edit_user.html', 
                                 id=id,
                                 name=user[0],
                                 email=user[1],
                                 role=user[2])
        else:
            flash('User not found!', 'error')
            return redirect(url_for('users'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('users'))

@app.route('/projects/edit/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('projects'))

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            status = request.form['status']
            committee_id = request.form['committee_id']

            cur.execute("""
                UPDATE project 
                SET project_name = %s, start_date = %s, end_date = %s, 
                    status = %s, committee_id = %s
                WHERE project_id = %s
            """, (name, start_date, end_date, status, committee_id, id))
            conn.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('projects'))

        # Get project details
        cur.execute("""
            SELECT project_name, start_date, end_date, status, committee_id 
            FROM project WHERE project_id = %s
        """, (id,))
        project = cur.fetchone()

        # Get all committees for dropdown
        cur.execute("SELECT committee_id, committee_name FROM committee")
        committees = cur.fetchall()

        cur.close()
        conn.close()

        if project:
            return render_template('edit_project.html', 
                                 id=id,
                                 name=project[0],
                                 start_date=project[1],
                                 end_date=project[2],
                                 status=project[3],
                                 committee_id=project[4],
                                 committees=committees)
        else:
            flash('Project not found!', 'error')
            return redirect(url_for('projects'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('projects'))

@app.route('/funds/edit/<int:id>', methods=['GET', 'POST'])
def edit_fund(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('funds'))

        cur = conn.cursor()

        if request.method == 'POST':
            amount = request.form['amount']
            project_id = request.form['project_id']
            transaction_type = request.form['transaction_type']
            description = request.form['description']
            
            cur.execute("""
                UPDATE fund 
                SET amount = %s, project_id = %s, transaction_type = %s, description = %s
                WHERE fund_id = %s
            """, (amount, project_id, transaction_type, description, id))
            conn.commit()
            flash('Fund updated successfully!', 'success')
            return redirect(url_for('funds'))

        # Get fund details
        cur.execute("""
            SELECT amount, project_id, transaction_type, description 
            FROM fund WHERE fund_id = %s
        """, (id,))
        fund = cur.fetchone()

        # Get all projects for dropdown
        cur.execute("SELECT project_id, project_name FROM project")
        projects = cur.fetchall()

        cur.close()
        conn.close()

        if fund:
            return render_template('edit_fund.html', 
                                 id=id,
                                 amount=fund[0],
                                 project_id=fund[1],
                                 transaction_type=fund[2],
                                 description=fund[3],
                                 projects=projects)
        else:
            flash('Fund not found!', 'error')
            return redirect(url_for('funds'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('funds'))

@app.route('/budgets/edit/<int:id>', methods=['GET', 'POST'])
def edit_budget(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('budgets'))

        cur = conn.cursor()

        if request.method == 'POST':
            purpose = request.form['purpose']
            total_amount = request.form['total_amount']
            allocated_amount = request.form['allocated_amount']
            approved = request.form.get('approved') == 'yes'
            project_id = request.form['project_id']

            cur.execute("""
                UPDATE budget 
                SET purpose = %s, total_amount = %s, allocated_amount = %s, 
                    approved = %s, project_id = %s
                WHERE budget_id = %s
            """, (purpose, total_amount, allocated_amount, approved, project_id, id))
            conn.commit()
            flash('Budget updated successfully!', 'success')
            return redirect(url_for('budgets'))

        # Get budget details
        cur.execute("""
            SELECT purpose, total_amount, allocated_amount, approved, project_id 
            FROM budget WHERE budget_id = %s
        """, (id,))
        budget = cur.fetchone()

        # Get all projects for dropdown
        cur.execute("""
            SELECT project_id, project_name 
            FROM project 
            ORDER BY project_name
        """)
        projects_data = cur.fetchall()
        projects = [{"id": row[0], "name": row[1]} for row in projects_data]

        cur.close()
        conn.close()

        if budget:
            return render_template('edit_budget.html', 
                                 id=id,
                                 purpose=budget[0],
                                 total_amount=budget[1],
                                 allocated_amount=budget[2],
                                 approved=budget[3],
                                 project_id=budget[4],
                                 projects=projects)
        else:
            flash('Budget not found!', 'error')
            return redirect(url_for('budgets'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('budgets'))

@app.route('/items/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('items'))

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['item_name']
            quantity = request.form['quantity']
            unit_price = request.form['unit_price']
            total_cost = float(quantity) * float(unit_price)
            project_id = request.form['project_id']
            supplier_id = request.form['supplier_id']
            purchased_at = request.form['purchased_at']

            cur.execute("""
                UPDATE item 
                SET item_name = %s, quantity = %s, unit_price = %s, total_cost = %s,
                    project_id = %s, supplier_id = %s, purchased_at = %s
                WHERE item_id = %s
            """, (name, quantity, unit_price, total_cost, project_id, supplier_id, purchased_at, id))
            conn.commit()
            flash('Item updated successfully!', 'success')
            return redirect(url_for('items'))

        # Get item details
        cur.execute("""
            SELECT item_name, quantity, unit_price, project_id, supplier_id, purchased_at 
            FROM item WHERE item_id = %s
        """, (id,))
        item = cur.fetchone()

        # Get all projects and suppliers for dropdowns
        cur.execute("SELECT project_id, project_name FROM project")
        projects = cur.fetchall()
        cur.execute("SELECT supplier_id, supplier_name FROM supplier")
        suppliers = cur.fetchall()

        cur.close()
        conn.close()

        if item:
            return render_template('edit_item.html', 
                                 id=id,
                                 name=item[0],
                                 quantity=item[1],
                                 unit_price=item[2],
                                 project_id=item[3],
                                 supplier_id=item[4],
                                 purchased_at=item[5],
                                 projects=projects,
                                 suppliers=suppliers)
        else:
            flash('Item not found!', 'error')
            return redirect(url_for('items'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('items'))

@app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('suppliers'))

        cur = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            address = request.form['address']

            cur.execute("""
                UPDATE supplier 
                SET supplier_name = %s, contact_number = %s, email = %s, address = %s
                WHERE supplier_id = %s
            """, (name, phone, email, address, id))
            conn.commit()
            flash('Supplier updated successfully!', 'success')
            return redirect(url_for('suppliers'))

        cur.execute("""
            SELECT supplier_name, contact_number, email, address 
            FROM supplier WHERE supplier_id = %s
        """, (id,))
        supplier = cur.fetchone()
        cur.close()
        conn.close()

        if supplier:
            return render_template('edit_supplier.html', 
                                 id=id,
                                 name=supplier[0],
                                 phone=supplier[1],
                                 email=supplier[2],
                                 address=supplier[3])
        else:
            flash('Supplier not found!', 'error')
            return redirect(url_for('suppliers'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('suppliers'))

@app.route('/transactions/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('transactions'))

        cur = conn.cursor()

        if request.method == 'POST':
            account_id = request.form['account_id']
            project_id = request.form['project_id']
            amount = request.form['amount']
            transaction_type = request.form['transaction_type']
            purpose = request.form['purpose']
            description = request.form['description']
            date = request.form['date']

            cur.execute("""
                UPDATE transaction 
                SET account_id = %s, project_id = %s, amount = %s, transaction_type = %s,
                    purpose = %s, description = %s, transaction_date = %s
                WHERE transaction_id = %s
            """, (account_id, project_id, amount, transaction_type, purpose, description, date, id))
            conn.commit()
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('transactions'))

        # Get transaction details
        cur.execute("""
            SELECT account_id, project_id, amount, transaction_type, purpose, description, transaction_date 
            FROM transaction WHERE transaction_id = %s
        """, (id,))
        transaction = cur.fetchone()

        # Get all projects for dropdown
        cur.execute("SELECT project_id, project_name FROM project")
        projects = cur.fetchall()

        cur.close()
        conn.close()

        if transaction:
            return render_template('edit_transaction.html', 
                                 id=id,
                                 account_id=transaction[0],
                                 project_id=transaction[1],
                                 amount=transaction[2],
                                 transaction_type=transaction[3],
                                 purpose=transaction[4],
                                 description=transaction[5],
                                 date=transaction[6],
                                 projects=projects)
        else:
            flash('Transaction not found!', 'error')
            return redirect(url_for('transactions'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('transactions'))

@app.route('/pending_projects')
def pending_projects():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('pending_projects.html', projects=[])

        cur = conn.cursor()

        # Get pending projects with committee names
        cur.execute("""
            SELECT p.project_id, p.project_name, p.start_date, p.end_date, p.status, 
                   c.committee_name
            FROM project p
            LEFT JOIN committee c ON p.committee_id = c.committee_id
            WHERE p.status = 'Pending'
        """)
        projects = cur.fetchall()
        cur.close()
        conn.close()

        return render_template('pending_projects.html', projects=projects)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('pending_projects.html', projects=[])

@app.route('/approve_project/<int:project_id>', methods=['POST'])
def approve_project(project_id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('pending_projects'))

        cur = conn.cursor()
        cur.execute("""
            UPDATE project 
            SET status = 'Approved'
            WHERE project_id = %s
        """, (project_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Project approved successfully!', 'success')
        return redirect(url_for('pending_projects'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('pending_projects'))

@app.route('/admin_dashboard')
def admin_dashboard():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('admin_dashboard.html', users=[])

        cur = conn.cursor()
        
        # Get all users
        cur.execute("SELECT user_id, name, email, role, created_at FROM user")
        users_data = cur.fetchall()
        
        # Get all committees with their members
        cur.execute("""
            SELECT c.committee_id, c.committee_name, c.committee_type, 
                   GROUP_CONCAT(u.name) as members
            FROM committee c
            LEFT JOIN committee_members cm ON c.committee_id = cm.committee_id
            LEFT JOIN user u ON cm.user_id = u.user_id
            GROUP BY c.committee_id
        """)
        committees_data = cur.fetchall()
        
        cur.close()
        conn.close()

        users = [{"id": r[0], "name": r[1], "email": r[2], "role": r[3], "created_at": r[4]} for r in users_data]
        committees = [{"id": r[0], "name": r[1], "type": r[2], "members": r[3]} for r in committees_data]
        
        return render_template('admin_dashboard.html', users=users, committees=committees)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('admin_dashboard.html', users=[])

@app.route('/create_committee', methods=['POST'])
def create_committee():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('admin_dashboard'))

        cur = conn.cursor()
        
        # Get form data
        committee_name = request.form['committee_name']
        committee_type = request.form['committee_type']
        selected_users = request.form.getlist('selected_users')  # This gets all selected user IDs
        
        if not selected_users:
            flash('Please select at least one member for the committee!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Insert new committee
        cur.execute("""
            INSERT INTO committee (committee_name, committee_type, created_at)
            VALUES (%s, %s, NOW())
        """, (committee_name, committee_type))
        
        # Get the new committee ID
        committee_id = cur.lastrowid
        
        # Insert all selected users as committee members
        for user_id in selected_users:
            try:
                cur.execute("""
                    INSERT INTO committee_members (committee_id, user_id)
                    VALUES (%s, %s)
                """, (committee_id, user_id))
            except Error as e:
                if e.errno == 1062:  # Duplicate entry error
                    flash(f'User is already a member of this committee!', 'warning')
                else:
                    raise e
        
        conn.commit()
        flash('Committee created successfully with selected members!', 'success')
        
        cur.close()
        conn.close()
        
        return redirect(url_for('admin_dashboard'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

# Add a new route to view committee members
@app.route('/committee/<int:committee_id>/members')
def view_committee_members(committee_id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('admin_dashboard'))

        cur = conn.cursor()
        
        # Get committee details
        cur.execute("""
            SELECT committee_name, committee_type 
            FROM committee 
            WHERE committee_id = %s
        """, (committee_id,))
        committee = cur.fetchone()
        
        if not committee:
            flash('Committee not found!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get all members of this committee
        cur.execute("""
            SELECT u.user_id, u.name, u.email, u.role, cm.created_at as joined_date
            FROM committee_members cm
            JOIN user u ON cm.user_id = u.user_id
            WHERE cm.committee_id = %s
            ORDER BY u.name
        """, (committee_id,))
        members = cur.fetchall()

        # Get all users who are not members of this committee
        cur.execute("""
            SELECT u.user_id, u.name, u.email, u.role
            FROM user u
            WHERE u.user_id NOT IN (
                SELECT user_id 
                FROM committee_members 
                WHERE committee_id = %s
            )
            ORDER BY u.name
        """, (committee_id,))
        available_users = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('committee_members.html',
                             committee_id=committee_id,
                             committee_name=committee[0],
                             committee_type=committee[1],
                             members=members,
                             available_users=available_users)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/committee/<int:committee_id>/remove_member/<int:user_id>', methods=['POST'])
def remove_committee_member(committee_id, user_id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('view_committee_members', committee_id=committee_id))

        cur = conn.cursor()
        
        # Remove the member from the committee
        cur.execute("""
            DELETE FROM committee_members 
            WHERE committee_id = %s AND user_id = %s
        """, (committee_id, user_id))
        
        conn.commit()
        flash('Member removed from committee successfully!', 'success')
        
        cur.close()
        conn.close()
        
        return redirect(url_for('view_committee_members', committee_id=committee_id))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('view_committee_members', committee_id=committee_id))

@app.route('/committee/<int:committee_id>/add_members', methods=['POST'])
def add_committee_members(committee_id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('admin_dashboard'))

        cur = conn.cursor()
        
        # Get selected user IDs
        selected_users = request.form.getlist('selected_users')
        
        if not selected_users:
            flash('Please select at least one user to add!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Check if committee exists
        cur.execute("SELECT committee_name FROM committee WHERE committee_id = %s", (committee_id,))
        committee = cur.fetchone()
        
        if not committee:
            flash('Committee not found!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Add each selected user to the committee
        added_count = 0
        skipped_count = 0
        
        for user_id in selected_users:
            try:
                cur.execute("""
                    INSERT INTO committee_members (committee_id, user_id)
                    VALUES (%s, %s)
                """, (committee_id, user_id))
                added_count += 1
            except Error as e:
                if e.errno == 1062:  # Duplicate entry error
                    skipped_count += 1
                else:
                    raise e
        
        conn.commit()
        
        if added_count > 0:
            flash(f'Successfully added {added_count} new member(s) to the committee!', 'success')
        if skipped_count > 0:
            flash(f'Skipped {skipped_count} user(s) who were already members.', 'warning')
        
        cur.close()
        conn.close()
        
        return redirect(url_for('view_committee_members', committee_id=committee_id))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/pending_budgets')
def pending_budgets():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('pending_budgets.html', pending_requests=[], approved_requests=[])

        cur = conn.cursor()
        
        # Get all pending fund requests with project names
        cur.execute("""
            SELECT f.fund_id, f.amount, f.purpose, f.description, f.created_at,
                   p.project_name, f.approval_notes
            FROM fund f
            JOIN project p ON f.project_id = p.project_id
            WHERE f.status = 'pending'
            ORDER BY f.created_at DESC
        """)
        pending_requests = cur.fetchall()
        
        # Get all approved fund requests
        cur.execute("""
            SELECT f.fund_id, f.amount, f.purpose, f.description, f.created_at,
                   p.project_name, f.approval_notes, f.approved_at
            FROM fund f
            JOIN project p ON f.project_id = p.project_id
            WHERE f.status = 'approved'
            ORDER BY f.approved_at DESC
        """)
        approved_requests = cur.fetchall()
        
        cur.close()
        conn.close()
        
        pending_requests_list = [
            {
                "id": row[0],
                "amount": row[1],
                "purpose": row[2],
                "description": row[3],
                "created_at": row[4],
                "project_name": row[5],
                "approval_notes": row[6]
            }
            for row in pending_requests
        ]
        
        approved_requests_list = [
            {
                "id": row[0],
                "amount": row[1],
                "purpose": row[2],
                "description": row[3],
                "created_at": row[4],
                "project_name": row[5],
                "approval_notes": row[6],
                "approved_at": row[7]
            }
            for row in approved_requests
        ]
        
        return render_template('pending_budgets.html', 
                             pending_requests=pending_requests_list,
                             approved_requests=approved_requests_list)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('pending_budgets.html', pending_requests=[], approved_requests=[])

@app.route('/fund_request/<int:request_id>/approve', methods=['POST'])
def approve_fund_request(request_id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('pending_budgets'))

        cur = conn.cursor()
        
        # Start transaction
        conn.start_transaction()
        
        try:
            # Get fund request details
            cur.execute("""
                SELECT amount, project_id, purpose, description
                FROM fund
                WHERE fund_id = %s AND status = 'pending'
            """, (request_id,))
            fund_request = cur.fetchone()
            
            if not fund_request:
                raise Error("Fund request not found or already processed")
            
            amount, project_id, purpose, description = fund_request
            
            # Check if we have enough total budget
            cur.execute("SELECT total_amount FROM budget LIMIT 1")
            total_budget = cur.fetchone()
            
            if not total_budget or total_budget[0] < amount:
                raise Error(f"Insufficient total budget. Available: ৳{total_budget[0] if total_budget else 0:.2f}")
            
            # Get approval notes from form
            approval_notes = request.form.get('approval_notes', '')
            
            # Update fund request status
            cur.execute("""
                UPDATE fund 
                SET status = 'approved',
                    approval_notes = %s,
                    approved_at = NOW()
                WHERE fund_id = %s
            """, (approval_notes, request_id))
            
            # Deduct from total budget
            cur.execute("""
                UPDATE budget 
                SET total_amount = total_amount - %s
                WHERE budget_id = 1
            """, (amount,))
            
            # Add to project budget
            cur.execute("""
                INSERT INTO project_budget (project_id, allocated_amount)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE allocated_amount = allocated_amount + %s
            """, (project_id, amount, amount))
            
            conn.commit()
            flash('Fund request approved successfully!', 'success')
            
        except Error as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'error')
        
        cur.close()
        conn.close()
        
        return redirect(url_for('pending_budgets'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('pending_budgets'))

@app.route('/fund_request/<int:request_id>/reject', methods=['POST'])
def reject_fund_request(request_id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('pending_budgets'))

        cur = conn.cursor()
        
        # Get rejection reason
        rejection_reason = request.form.get('rejection_reason')
        if not rejection_reason:
            flash('Rejection reason is required!', 'error')
            return redirect(url_for('pending_budgets'))
        
        # Update fund request status
        cur.execute("""
            UPDATE fund 
            SET status = 'rejected',
                rejection_reason = %s,
                rejected_at = NOW()
            WHERE fund_id = %s
        """, (rejection_reason, request_id))
        
        conn.commit()
        flash('Fund request rejected successfully!', 'success')
        
        cur.close()
        conn.close()
        
        return redirect(url_for('pending_budgets'))
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('pending_budgets'))

@app.route('/fund_request/<int:request_id>/details')
def fund_request_details(request_id):
    try:
        conn = get_db_connection()
        if not conn:
            return 'Error connecting to database', 500

        cur = conn.cursor()
        
        # Get detailed fund request information
        cur.execute("""
            SELECT f.fund_id, f.amount, f.purpose, f.description,
                   f.created_at, f.status, f.approval_notes, f.rejection_reason,
                   f.approved_at, f.rejected_at,
                   p.project_name, p.project_id,
                   u.name as requested_by
            FROM fund f
            JOIN project p ON f.project_id = p.project_id
            LEFT JOIN user u ON f.created_by = u.user_id
            WHERE f.fund_id = %s
        """, (request_id,))
        
        request = cur.fetchone()
        
        if not request:
            return 'Fund request not found', 404
        
        cur.close()
        conn.close()
        
        return render_template('fund_request_details.html',
                             request={
                                 "id": request[0],
                                 "amount": request[1],
                                 "purpose": request[2],
                                 "description": request[3],
                                 "created_at": request[4],
                                 "status": request[5],
                                 "approval_notes": request[6],
                                 "rejection_reason": request[7],
                                 "approved_at": request[8],
                                 "rejected_at": request[9],
                                 "project_name": request[10],
                                 "project_id": request[11],
                                 "requested_by": request[12]
                             })
    except Error as e:
        return f'Database error: {str(e)}', 500

@app.route('/pending_funds')
def pending_funds():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('pending_funds.html', pending_funds=[])

        cur = conn.cursor()
        
        # Get only pending fund requests with project names
        cur.execute("""
            SELECT f.fund_id, f.amount, f.purpose, f.description, f.created_at,
                   p.project_name, f.approval_notes
            FROM fund f
            JOIN project p ON f.project_id = p.project_id
            WHERE f.status = 'pending'
            ORDER BY f.created_at DESC
        """)
        funds = cur.fetchall()
        
        cur.close()
        conn.close()
        
        pending_funds = [
            {
                "id": row[0],
                "amount": row[1],
                "purpose": row[2],
                "description": row[3],
                "created_at": row[4],
                "project_name": row[5],
                "approval_notes": row[6]
            }
            for row in funds
        ]
        
        return render_template('pending_funds.html', pending_funds=pending_funds)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('pending_funds.html', pending_funds=[])

@app.route('/approved_funds')
def approved_funds():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('approved_funds.html', approved_funds=[])

        cur = conn.cursor()
        
        # Get only approved fund requests with project names
        cur.execute("""
            SELECT f.fund_id, f.amount, f.purpose, f.description, f.created_at,
                   p.project_name, f.approval_notes, f.approved_at
            FROM fund f
            JOIN project p ON f.project_id = p.project_id
            WHERE f.status = 'approved'
            ORDER BY f.approved_at DESC
        """)
        funds = cur.fetchall()
        
        cur.close()
        conn.close()
        
        approved_funds = [
            {
                "id": row[0],
                "amount": row[1],
                "purpose": row[2],
                "description": row[3],
                "created_at": row[4],
                "project_name": row[5],
                "approval_notes": row[6],
                "approved_at": row[7]
            }
            for row in funds
        ]
        
        return render_template('approved_funds.html', approved_funds=approved_funds)
    except Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('approved_funds.html', approved_funds=[])

def create_tables():
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database")
            return

        cur = conn.cursor()

        # Create item table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS item (
                item_id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(255) NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(15,2) NOT NULL,
                total_cost DECIMAL(15,2) NOT NULL,
                project_id INT,
                supplier_id INT,
                purchased_at DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE SET NULL,
                FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id) ON DELETE SET NULL
            )
        """)

        # Create budget table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                budget_id INT AUTO_INCREMENT PRIMARY KEY,
                total_amount DECIMAL(15,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # Create project_budget table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS project_budget (
                project_budget_id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT,
                allocated_amount DECIMAL(15,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
            )
        """)

        # Create fund table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fund (
                fund_id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT,
                amount DECIMAL(15,2) NOT NULL,
                purpose VARCHAR(255) NOT NULL,
                description TEXT,
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                created_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP NULL,
                rejected_at TIMESTAMP NULL,
                approval_notes TEXT,
                rejection_reason TEXT,
                FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES user(user_id) ON DELETE SET NULL
            )
        """)

        conn.commit()
        print("Database tables checked/created successfully!")
        
        cur.close()
        conn.close()
    except Error as e:
        print(f"Error creating tables: {e}")
        if conn:
            conn.rollback()

# Call create_tables() when the application starts
create_tables()

if __name__ == '__main__':
    app.run(debug=True) 