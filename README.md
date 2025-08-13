# Project Management System

A Flask-based web application for managing projects, committees, funds, and resources.

## Features

- User and Committee Management
- Project Tracking and Budgeting
- Fund Request System
- Resource and Supplier Management
- Transaction Tracking

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Configure database in `app.py`:
```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'newdb',
    'port': 3306
}
```

3. Run the application:
```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

## Main Sections

- Dashboard: `/dashboard`
- Users: `/users`
- Committees: `/committees`
- Projects: `/projects`
- Funds: `/funds`
- Budgets: `/budgets`
- Items: `/items`
- Suppliers: `/suppliers`
- Transactions: `/transactions` 