from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # keep empty if no password
    database="learnedge_db"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def root():
    # Redirect root to login
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            flash('Login successful!')

            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Password must be at least 8 characters long.')
            return redirect(url_for('register'))

        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing = cursor.fetchone()
        if existing:
            flash('Username or email already exists.')
            return redirect(url_for('register'))

        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
            (username, email, password, role)
        )
        db.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash("If this username or email exists, a password reset link will be sent.")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'role' in session and session['role'] == 'student':
        return "Welcome Student! (Dashboard to be implemented)"
    else:
        return redirect(url_for('login'))

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'role' in session and session['role'] == 'teacher':
        return "Welcome Teacher! (Dashboard to be implemented)"
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
