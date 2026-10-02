from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import database

app = Flask(__name__)
app.secret_key = 'expense_tracker_secret_key'

database.init_db()

CATEGORIES = [
    'Food',
    'Travel',
    'Rent',
    'Utilities',
    'Entertainment',
    'Shopping',
    'Healthcare',
    'Education',
    'Other'
]


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    today_total = database.get_total_spent_today(user_id)
    month_total = database.get_total_spent_this_month(user_id)
    recent = database.get_recent_expenses(user_id, 5)

    return render_template(
        'index.html',
        today_total=today_total,
        month_total=month_total,
        recent_expenses=recent,
        categories=CATEGORIES,
        current_date=datetime.now().strftime('%Y-%m-%d')
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('logged_in'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        contact = request.form.get('identifier')  # This can be either email or phone number
        password = request.form.get('password')

        if not username or not contact or not password:
            flash('Please fill in all fields!', 'danger')
            return redirect(url_for('register'))

        email = contact
        phone = contact

        success = database.register_user(
            username,
            email,
            phone,
            password
        )

        if success:
            flash(
                'Registration successful! Please login now.',
                'success'
            )
            return redirect(url_for('login'))
        else:
            flash(
                'Email or phone number is already registered.',
                'danger'
            )

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')

        if not identifier or not password:
            flash('Please enter your email/phone and password.', 'danger')
            return redirect(url_for('login'))

        user = database.verify_user(identifier, password)

        if user:
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']

            return redirect(url_for('index'))

        else:
            flash(
                'Invalid email/phone or password. Please try again.',
                'danger'
            )

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    title = request.form.get('title')
    amount_str = request.form.get('amount')
    category = request.form.get('category')
    date = request.form.get('date')
    description = request.form.get('description', '')

    if not title or not amount_str or not category or not date:
        flash(
            'All fields except description are required!',
            'danger'
        )
        return redirect(url_for('index'))

    try:
        amount = float(amount_str)

        if amount <= 0:
            flash(
                'Amount must be greater than zero!',
                'danger'
            )
            return redirect(url_for('index'))

    except ValueError:
        flash(
            'Invalid amount entered!',
            'danger'
        )
        return redirect(url_for('index'))

    database.add_expense(
        user_id,
        title,
        amount,
        category,
        date,
        description
    )

    flash(
        'Expense added successfully!',
        'success'
    )

    return redirect(url_for('index'))


@app.route('/expenses')
def expenses():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    all_expenses = database.get_all_expenses(user_id)

    return render_template(
        'expenses.html',
        expenses=all_expenses,
        categories=CATEGORIES
    )


@app.route('/expenses/edit/<int:expense_id>', methods=['POST'])
def edit(expense_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    title = request.form.get('title')
    amount_str = request.form.get('amount')
    category = request.form.get('category')
    date = request.form.get('date')
    description = request.form.get('description', '')

    if not title or not amount_str or not category or not date:
        flash(
            'All fields except description are required for editing!',
            'danger'
        )
        return redirect(url_for('expenses'))

    try:
        amount = float(amount_str)

        if amount <= 0:
            flash(
                'Amount must be greater than zero!',
                'danger'
            )
            return redirect(url_for('expenses'))

    except ValueError:
        flash(
            'Invalid amount entered!',
            'danger'
        )
        return redirect(url_for('expenses'))

    database.update_expense(
        expense_id,
        user_id,
        title,
        amount,
        category,
        date,
        description
    )

    flash(
        'Expense updated successfully!',
        'success'
    )

    return redirect(url_for('expenses'))


@app.route('/expenses/delete/<int:expense_id>', methods=['POST'])
def delete(expense_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    database.delete_expense(
        expense_id,
        user_id
    )

    flash(
        'Expense deleted successfully!',
        'success'
    )

    referrer = request.referrer

    if referrer and 'expenses' in referrer:
        return redirect(url_for('expenses'))

    return redirect(url_for('index'))


@app.route('/report')
def report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    selected_month = request.args.get('month')

    if not selected_month:
        selected_month = datetime.now().strftime('%Y-%m')

    monthly_expenses = database.get_expenses_by_month(
        user_id,
        selected_month
    )

    total_spent = sum(
        item['amount']
        for item in monthly_expenses
    )

    category_summary = database.get_category_summary(
        user_id,
        selected_month
    )

    chart_labels = [
        item['category']
        for item in category_summary
    ]

    chart_values = [
        item['total_amount']
        for item in category_summary
    ]

    try:
        dt_obj = datetime.strptime(
            selected_month,
            '%Y-%m'
        )

        readable_month = dt_obj.strftime(
            '%B %Y'
        )

    except ValueError:
        readable_month = selected_month

    return render_template(
        'report.html',
        expenses=monthly_expenses,
        total_spent=total_spent,
        category_summary=category_summary,
        selected_month=selected_month,
        readable_month=readable_month,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


if __name__ == '__main__':
    app.run(debug=True)