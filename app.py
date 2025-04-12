
from flask import Flask, render_template, session,flash,request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email,ValidationError
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from wtforms import SelectField

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3307
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mydatabase'
app.secret_key = 'my_secret_key_here'
mysql = MySQL(app)


# Routes
@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/users', methods=['GET', 'POST'])
def users():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']

        cur.execute("""
            INSERT INTO user (name, email, role, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (name, email, role))
        mysql.connection.commit()

    cur.execute("SELECT user_id, name, email, role, created_at FROM user")
    rows = cur.fetchall()
    cur.close()

    users = [{"id": r[0], "name": r[1], "email": r[2], "role": r[3], "created_at": r[4]} for r in rows]

    return render_template('users.html', users=users)


@app.route('/committees', methods=['GET', 'POST'])
def committees_page():
    cur = mysql.connection.cursor()
    
    # Handle form submission
    if request.method == 'POST':
        name = request.form['name']
        ctype = request.form['type']
        user_id = request.form['user_id']
        cur.execute("INSERT INTO committee (committee_name, committee_type, created_at, user_id) VALUES (%s, %s, NOW(), %s)",
                    (name, ctype, user_id))
        mysql.connection.commit()

    # Fetch all committee records
    cur.execute("SELECT committee_id, committee_name, committee_type, created_at, user_id FROM committee")
    data = cur.fetchall()
    cur.close()

    committees = [
        {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "created_at": row[3],
            "created_by": f"User #{row[4]}"
        } for row in data
    ]

    return render_template('committees.html', committees=committees)

@app.route('/projects', methods=['GET', 'POST'])
def projects():
    cur = mysql.connection.cursor()

    # Handle form submission
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
        mysql.connection.commit()

    # Fetch all projects
    cur.execute("SELECT project_id, project_name, start_date, end_date, status, committee_id FROM project")
    rows = cur.fetchall()
    cur.close()

    projects = [
        {
            "id": row[0],
            "name": row[1],
            "start_date": row[2],
            "end_date": row[3],
            "status": row[4],
            "committee": f"Committee #{row[5]}"
        }
        for row in rows
    ]

    return render_template('projects.html', projects=projects)


@app.route('/funds', methods=['GET', 'POST'])
def funds():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        amount = request.form['amount']
        project_id = request.form['project_id']
        transaction_type = request.form['transaction_type']
        description = request.form['description']

        cur.execute("""
            INSERT INTO fund (amount, project_id, transaction_type, description, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (amount, project_id, transaction_type, description))
        mysql.connection.commit()

    cur.execute("SELECT fund_id, amount, project_id, transaction_type, description, created_at FROM fund")
    rows = cur.fetchall()
    cur.close()

    funds = [
        {
            "id": r[0], "amount": r[1], "project": f"#{r[2]}",
            "type": r[3], "desc": r[4], "date": r[5]
        } for r in rows
    ]
    return render_template('funds.html', funds=funds)


@app.route('/budgets', methods=['GET', 'POST'])
def budgets():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        purpose = request.form['purpose']
        total_amount = request.form['total_amount']
        allocated_amount = request.form['allocated_amount']
        approved = request.form['approved']
        project_id = request.form['project_id']

        cur.execute("""
            INSERT INTO budget (purpose, total_amount, allocated_amount, approved, created_at, project_id)
            VALUES (%s, %s, %s, %s, NOW(), %s)
        """, (purpose, total_amount, allocated_amount, approved == 'yes', project_id))
        mysql.connection.commit()

    cur.execute("SELECT budget_id, purpose, total_amount, allocated_amount, approved, created_at, project_id FROM budget")
    rows = cur.fetchall()
    cur.close()

    budgets = [
        {
            "id": r[0], "purpose": r[1], "total": r[2], "allocated": r[3],
            "approved": '✅' if r[4] else '❌', "date": r[5], "project": f"#{r[6]}"
        } for r in rows
    ]
    return render_template('budgets.html', budgets=budgets)

@app.route('/items', methods=['GET', 'POST'])
def items():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = request.form['quantity']
        unit_price = request.form['unit_price']
        total_cost = float(quantity) * float(unit_price)
        project_id = request.form['project_id']
        supplier_id = request.form['supplier_id']
        purchased_at = request.form['purchased_at']

        cur.execute("""
            INSERT INTO item (item_name, quantity, unit_price, total_cost, project_id, supplier_id, purchased_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (item_name, quantity, unit_price, total_cost, project_id, supplier_id, purchased_at))
        mysql.connection.commit()

    cur.execute("SELECT item_id, item_name, quantity, unit_price, total_cost, project_id, supplier_id, purchased_at FROM item")
    rows = cur.fetchall()
    cur.close()

    items = [
        {
            "id": r[0], "name": r[1], "qty": r[2], "price": r[3], "total": r[4],
            "project": f"#{r[5]}", "supplier": f"#{r[6]}", "date": r[7]
        } for r in rows
    ]
    return render_template('items.html', items=items)


@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']

        cur.execute("""
            INSERT INTO supplier (supplier_name, contact_number, email, address)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, email, address))
        mysql.connection.commit()

    cur.execute("SELECT supplier_id, supplier_name, contact_number, email, address FROM supplier")
    rows = cur.fetchall()
    cur.close()

    suppliers = [{"id": r[0], "name": r[1], "phone": r[2], "email": r[3], "address": r[4]} for r in rows]
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        account_id = request.form['account_id']
        project_id = request.form['project_id']
        amount = request.form['amount']
        transaction_type = request.form['transaction_type']
        purpose = request.form['purpose']
        description = request.form['description']
        date = request.form['date']

        cur.execute("""
            INSERT INTO transaction (account_id, project_id, amount, transaction_type, purpose, description, transaction_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (account_id, project_id, amount, transaction_type, purpose, description, date))
        mysql.connection.commit()

    # ✅ Use standard triple quotes for SELECT
    cur.execute("""
        SELECT transaction_id, account_id, project_id, amount, transaction_type, purpose, description, transaction_date
        FROM transaction
    """)
    rows = cur.fetchall()
    cur.close()

    transactions = [
        {
            "id": r[0],
            "account": f"#{r[1]}",
            "project": f"#{r[2]}",
            "amount": r[3],
            "type": r[4],
            "purpose": r[5],
            "description": r[6],
            "date": r[7]
        }
        for r in rows
    ]
    return render_template('transactions.html', transactions=transactions)

# DELETE
@app.route('/committees/delete/<int:id>', methods=['POST'])
def delete_committee(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM committee WHERE committee_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/committees')

# EDIT
@app.route('/committees/edit/<int:id>', methods=['GET', 'POST'])
def edit_committee(id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        ctype = request.form['type']
        user_id = request.form['user_id']
        cur.execute("""
            UPDATE committee SET committee_name = %s, committee_type = %s, user_id = %s WHERE committee_id = %s
        """, (name, ctype, user_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/committees')

    cur.execute("SELECT committee_name, committee_type, user_id FROM committee WHERE committee_id = %s", (id,))
    row = cur.fetchone()
    cur.close()
    return render_template('edit_committee.html', id=id, name=row[0], type=row[1], user_id=row[2])

@app.route('/users/delete/<int:id>', methods=['POST'])
def delete_user(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE user_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/users')

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        cur.execute("UPDATE user SET name=%s, email=%s, role=%s WHERE user_id=%s",
                    (name, email, role, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/users')

    cur.execute("SELECT name, email, role FROM user WHERE user_id = %s", (id,))
    row = cur.fetchone()
    cur.close()
    return render_template('edit_user.html', id=id, name=row[0], email=row[1], role=row[2])

@app.route('/projects/delete/<int:id>', methods=['POST'])
def delete_project(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM project WHERE project_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/projects')

@app.route('/projects/edit/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        status = request.form['status']
        committee_id = request.form['committee_id']

        cur.execute("""
            UPDATE project SET project_name=%s, start_date=%s, end_date=%s, status=%s, committee_id=%s
            WHERE project_id = %s
        """, (name, start_date, end_date, status, committee_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/projects')

    cur.execute("SELECT project_name, start_date, end_date, status, committee_id FROM project WHERE project_id = %s", (id,))
    row = cur.fetchone()
    cur.close()
    return render_template('edit_project.html', id=id, name=row[0], start=row[1], end=row[2], status=row[3], committee_id=row[4])


@app.route('/funds/delete/<int:id>', methods=['POST'])
def delete_fund(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM fund WHERE fund_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/funds')


@app.route('/funds/edit/<int:id>', methods=['GET', 'POST'])
def edit_fund(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        amount = request.form['amount']
        project_id = request.form['project_id']
        transaction_type = request.form['transaction_type']
        description = request.form['description']
        
        cur.execute("""
            UPDATE fund SET amount=%s, project_id=%s, transaction_type=%s, description=%s
            WHERE fund_id = %s
        """, (amount, project_id, transaction_type, description, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/funds')

    cur.execute("SELECT amount, project_id, transaction_type, description FROM fund WHERE fund_id = %s", (id,))
    row = cur.fetchone()
    cur.close()

    return render_template('edit_fund.html', id=id, amount=row[0], project_id=row[1], transaction_type=row[2], description=row[3])

    
@app.route('/budgets/delete/<int:id>', methods=['POST'])
def delete_budget(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM budget WHERE budget_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/budgets')

@app.route('/budgets/edit/<int:id>', methods=['GET', 'POST'])
def edit_budget(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        purpose = request.form['purpose']
        total = request.form['total_amount']
        allocated = request.form['allocated_amount']
        approved = request.form['approved'] == 'yes'
        project_id = request.form['project_id']
        cur.execute("""
            UPDATE budget SET purpose=%s, total_amount=%s, allocated_amount=%s, approved=%s, project_id=%s
            WHERE budget_id = %s
        """, (purpose, total, allocated, approved, project_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/budgets')

    cur.execute("SELECT purpose, total_amount, allocated_amount, approved, project_id FROM budget WHERE budget_id = %s", (id,))
    row = cur.fetchone()
    cur.close()

    return render_template('edit_budget.html', id=id, purpose=row[0], total=row[1], allocated=row[2], approved=row[3], project_id=row[4])


@app.route('/items/delete/<int:id>', methods=['POST'])
def delete_item(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM item WHERE item_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/items')

@app.route('/items/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['item_name']
        quantity = request.form['quantity']
        unit_price = request.form['unit_price']
        total_cost = float(quantity) * float(unit_price)
        project_id = request.form['project_id']
        supplier_id = request.form['supplier_id']
        purchased_at = request.form['purchased_at']

        cur.execute("""
            UPDATE item SET item_name=%s, quantity=%s, unit_price=%s, total_cost=%s, project_id=%s, supplier_id=%s, purchased_at=%s
            WHERE item_id=%s
        """, (name, quantity, unit_price, total_cost, project_id, supplier_id, purchased_at, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/items')

    cur.execute("SELECT item_name, quantity, unit_price, project_id, supplier_id, purchased_at FROM item WHERE item_id = %s", (id,))
    row = cur.fetchone()
    cur.close()

    return render_template('edit_item.html', id=id, name=row[0], quantity=row[1], unit_price=row[2],
                           project_id=row[3], supplier_id=row[4], purchased_at=row[5])

@app.route('/suppliers/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM supplier WHERE supplier_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/suppliers')



@app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        contact_number = request.form['contact_number']
        email = request.form['email']
        address = request.form['address']

        cur.execute("""
            UPDATE supplier
            SET supplier_name=%s, contact_number=%s, email=%s, address=%s
            WHERE supplier_id = %s
        """, (name, contact_number, email, address, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/suppliers')

    cur.execute("SELECT supplier_name, contact_number, email, address FROM supplier WHERE supplier_id = %s", (id,))
    row = cur.fetchone()
    cur.close()

    return render_template('edit_supplier.html', id=id, name=row[0], contact_number=row[1], email=row[2], address=row[3])

@app.route('/transactions/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        amount = request.form['amount']
        transaction_date = request.form['transaction_date']
        transaction_type = request.form['transaction_type']
        purpose = request.form['purpose']
        description = request.form['description']

        cur.execute("""
            UPDATE transaction
            SET amount=%s, transaction_date=%s, transaction_type=%s, purpose=%s, description=%s
            WHERE transaction_id = %s
        """, (amount, transaction_date, transaction_type, purpose, description, id))
        mysql.connection.commit()
        cur.close()
        return redirect('/transactions')

    cur.execute("SELECT amount, transaction_date, transaction_type, purpose, description FROM transaction WHERE transaction_id = %s", (id,))
    row = cur.fetchone()
    cur.close()
    
    return render_template('edit_transaction.html', id=id, amount=row[0], transaction_date=row[1],
                           transaction_type=row[2], purpose=row[3], description=row[4])

@app.route('/transactions/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM transaction WHERE transaction_id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/transactions')



if __name__ == '__main__':
    app.run(debug=True)
