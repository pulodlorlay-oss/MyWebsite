from flask import Flask, render_template, request, redirect, url_for, session, jsonify  # type: ignore[import]
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Database - storing students with their details and payment info
students_db = {}
registered_users = []  # List of all registered students

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Decorator to check if user is admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'student')
        student_id = request.form.get('student-id', '')
        
        # Admin login
        if user_type == 'admin':
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['username'] = username
                session['user_role'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('login.html', error='Invalid admin credentials')
        # Student login
        else:
            if username and username.strip() and student_id:
                # Add to registered users if not already there
                if not any(u['student_id'] == student_id for u in registered_users):
                    registered_users.append({
                        'name': username,
                        'student_id': student_id,
                        'login_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # Initialize student in database if not exists
                # NOTE: Do NOT auto-create fee data on student login.
                # Fees must be added by admin using the /add-student form.
                if student_id not in students_db:
                    students_db[student_id] = {
                        'name': username,
                        'student_id': student_id,
                        'email': 'student@college.edu',
                        'department': 'Computer Engineering',
                        'payment_received_by': 'Finance Office',
                        'semester': '3rd',
                        'gpa': '3.8',
                        'courses': ['CS101', 'CS102', 'CS103', 'CS104'],
                        'attendance': '85',
                        'fees_due': 0,
                        'fees_paid': 0,
                        'payment_status': 'Unpaid',
                        'payment_history': [],
                        'documents': ['Admit Card', 'ID Card', 'Transcript'],
                        'fee_description': '',
                        'fee_items': []
                    }

                
                session['username'] = username
                session['student_id'] = student_id
                session['user_role'] = 'student'
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error='Please enter your name and Student ID')
    
    return render_template('login.html')

@app.route('/home', methods=['POST', 'GET'])
@login_required
def home():
    if session['user_role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('home.html')

# Student Routes
@app.route('/academic-dashboard')
@login_required
def academic_dashboard():
    if session['user_role'] != 'student':
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    student_data = students_db.get(student_id, {})
    return render_template('academic_dashboard.html', student=student_data)

@app.route('/attendance')
@login_required
def attendance():
    if session['user_role'] != 'student':
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    student_data = students_db.get(student_id, {})
    return render_template('attendance.html', student=student_data)

@app.route('/profile')
@login_required
def profile():
    if session['user_role'] != 'student':
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    student_data = students_db.get(student_id, {})
    return render_template('profile.html', student=student_data)

@app.route('/documents')
@login_required
def documents():
    if session['user_role'] != 'student':
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    student_data = students_db.get(student_id, {})
    return render_template('documents.html', student=student_data)

@app.route('/payment-status')
@login_required
def payment_status():
    if session['user_role'] != 'student':
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    student_data = students_db.get(student_id, {})
    return render_template('payment_status.html', student=student_data)

@app.route('/menu')
@login_required
def menu():
    if session['user_role'] != 'student':
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    student_data = students_db.get(student_id, {})
    return render_template('payment_status.html', student=student_data)

@app.route('/fees')
@login_required
def fees():
    if session['user_role'] != 'student':
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    student_data = students_db.get(student_id, {})
    student_data.setdefault('fee_items', [])
    return render_template('fees.html', student=student_data)

# Admin Routes
@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    total_students = len(registered_users)
    total_fees_due = sum(student.get('fees_due', 0) for student in students_db.values())
    total_fees_paid = sum(student.get('fees_paid', 0) for student in students_db.values())
    pending_payments = sum(student.get('fees_due', 0) - student.get('fees_paid', 0) for student in students_db.values())
    
    stats = {
        'total_students': total_students,
        'total_fees_due': total_fees_due,
        'total_fees_paid': total_fees_paid,
        'pending_payments': pending_payments
    }
    return render_template('admin_dashboard.html', stats=stats)

@app.route('/manage')
@admin_required
def manage():
    students_list = list(students_db.values())
    return render_template('manage.html', students=students_list)

@app.route('/registered-students')
@admin_required
def registered_students():
    return render_template('registered_students.html', users=registered_users)

@app.route('/add-student', methods=['POST'])
@admin_required
def add_student():
    name = request.form.get('full_name', '').strip()
    student_id = request.form.get('student_id', '').strip()
    amount_to_pay = float(request.form.get('amount_to_pay', 0))
    
    if name and student_id and amount_to_pay > 0:
        fee_description = request.form.get('fee_description', '').strip() or 'Tuition, library, and lab fees for this semester'
        payment_received_by = request.form.get('payment_receiver', '').strip() or 'Finance Office'
        if student_id not in students_db:
            students_db[student_id] = {
                'name': name,
                'student_id': student_id,
                'email': f'{student_id}@college.edu',
                'department': 'Computer Engineering',
                'payment_received_by': payment_received_by,
                'semester': '3rd',
                'gpa': '3.8',
                'courses': ['CS101', 'CS102', 'CS103', 'CS104'],
                'attendance': '85',
                'fees_due': amount_to_pay,
                'fees_paid': 0,
                'payment_status': 'Unpaid',
                'payment_history': [],
                'documents': ['Admit Card', 'ID Card', 'Transcript'],
                'fee_description': fee_description,
                'fee_items': [
                    {
                        'description': fee_description,
                        'receiver': payment_received_by,
                        'amount_due': amount_to_pay,
                        'amount_paid': 0,
                        'status': 'Unpaid'
                    }
                ]
            }
            # Add to registered users if not already there
            if not any(u['student_id'] == student_id for u in registered_users):
                registered_users.append({
                    'name': name,
                    'student_id': student_id,
                    'login_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        else:
            student = students_db[student_id]
            student.setdefault('fee_items', [])
            student['fee_items'].append({
                'description': fee_description,
                'receiver': payment_received_by,
                'amount_due': amount_to_pay,
                'amount_paid': 0,
                'status': 'Unpaid'
            })
            student['fees_due'] += amount_to_pay
            student['fee_description'] = fee_description
            student['payment_received_by'] = payment_received_by
            if student['fees_paid'] >= student['fees_due']:
                student['payment_status'] = 'Paid'
            elif student['fees_paid'] > 0:
                student['payment_status'] = 'Partially Paid'
            else:
                student['payment_status'] = 'Unpaid'
    
    return redirect(url_for('manage'))

@app.route('/update-payment/<student_id>', methods=['POST'])
@admin_required
def update_payment(student_id):
    if student_id in students_db:
        payment_amount = float(request.form.get('payment_amount', 0))
        student = students_db[student_id]
        current_paid = student.get('fees_paid', 0)
        new_paid = max(0, current_paid + payment_amount)
        fees_due = student.get('fees_due', 0)
        student['fees_paid'] = new_paid

        # Apply the update to fee items if they exist so deductions affect the specific fee items.
        # This ensures when admin deducts (negative amount), the item-level balances and history reflect it.
        if student.get('fee_items'):

            # Remaining change to distribute across items (negative for deduction, positive for payment)
            remaining_change = payment_amount
            for item in student['fee_items']:
                item_due = item.get('amount_due', 0)
                item_paid = item.get('amount_paid', 0)

                if remaining_change == 0:
                    break

                if remaining_change < 0:
                    # Deduct up to how much this item has already been paid
                    available_to_deduct = item_paid
                    change_for_item = max(remaining_change, -available_to_deduct)
                else:
                    # Pay up to how much this item still needs
                    available_to_pay = max(item_due - item_paid, 0)
                    change_for_item = min(remaining_change, available_to_pay)

                if change_for_item == 0:
                    continue

                item['amount_paid'] = max(0, item_paid + change_for_item)
                item['status'] = (
                    'Paid' if item['amount_paid'] >= item_due and item_due > 0 else
                    'Partially Paid' if item['amount_paid'] > 0 else
                    'Unpaid'
                )

                remaining_change -= change_for_item

            # Recompute total fees_paid and payment status from item sums
            student['fees_paid'] = sum(i.get('amount_paid', 0) for i in student.get('fee_items', []))
            total_paid = student['fees_paid']
            if total_paid >= fees_due and fees_due > 0:
                student['payment_status'] = 'Paid'
            elif total_paid > 0:
                student['payment_status'] = 'Partially Paid'
            else:
                student['payment_status'] = 'Unpaid'
        else:
            # No fee items: keep old behavior.
            if new_paid >= fees_due:
                student['payment_status'] = 'Paid'
            elif new_paid > 0:
                student['payment_status'] = 'Partially Paid'
            else:
                student['payment_status'] = 'Unpaid'

        student['payment_history'].append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'amount': payment_amount,
            'item': 'General Payment',
            'balance_after': max(fees_due - student.get('fees_paid', 0), 0)
        })

        # Also record a per-item history entry when items are present,
        # so the admin can see where the deduction/pay went.
        if student.get('fee_items') and payment_amount < 0:
            # After distribution, each item has updated paid amount/status.
            for idx, it in enumerate(student.get('fee_items', [])):
                item_name = it.get('description', 'Unknown')
                # Only add a record if that item still has some paid amount (it was affected by deduction/payment).
                if it.get('amount_paid', 0) > 0 or it.get('status') in ('Unpaid', 'Partially Paid', 'Paid'):
                    student['payment_history'].append({
                        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'amount': payment_amount,
                        'item': item_name,
                        'balance_after': max(fees_due - student.get('fees_paid', 0), 0)
                    })


    
    return redirect(url_for('manage'))

@app.route('/update-fee-item/<student_id>/<int:item_index>', methods=['POST'])
@admin_required
def update_fee_item(student_id, item_index):
    if student_id in students_db:
        payment_amount = float(request.form.get('payment_amount', 0))
        student = students_db[student_id]
        student.setdefault('fee_items', [])
        if 0 <= item_index < len(student['fee_items']):
            item = student['fee_items'][item_index]
            current_paid = item.get('amount_paid', 0)
            new_paid = max(0, current_paid + payment_amount)
            # Calculate the actual change after clamping at not going below 0
            actual_change = new_paid - current_paid

            item['amount_paid'] = new_paid
            if new_paid >= item.get('amount_due', 0):
                item['status'] = 'Paid'
            elif new_paid > 0:
                item['status'] = 'Partially Paid'
            else:
                item['status'] = 'Unpaid'
            
            # Recalculate total fees_paid
            total_paid = sum(item.get('amount_paid', 0) for item in student['fee_items'])
            student['fees_paid'] = total_paid
            fees_due = student.get('fees_due', 0)
            if total_paid >= fees_due:
                student['payment_status'] = 'Paid'
            elif total_paid > 0:
                student['payment_status'] = 'Partially Paid'
            else:
                student['payment_status'] = 'Unpaid'
            
            student['payment_history'].append({
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'amount': actual_change,
                'item': item.get('description', 'Unknown'),
                'receiver': item.get('receiver', student.get('payment_received_by', '')),
                'balance_after': max(fees_due - total_paid, 0)
            })
    
    return redirect(url_for('manage'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)