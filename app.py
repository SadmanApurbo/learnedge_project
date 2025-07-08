from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from itsdangerous import URLSafeTimedSerializer
from utils.email_utils import send_reset_email  # Assuming you have this

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# DB connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="learnedge_db"
)
cursor = db.cursor(dictionary=True)
s = URLSafeTimedSerializer(app.secret_key)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
        else:
            flash("Invalid username or password.")
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
        if cursor.fetchone():
            flash('Username or email already exists.')
            return redirect(url_for('register'))

        cursor.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)", 
                       (username, email, password, role))
        db.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        input_value = request.form['username_or_email']
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (input_value, input_value))
        user = cursor.fetchone()
        if user:
            email = user['email']
            token = s.dumps(email, salt='password-reset-salt')
            reset_link = url_for('reset_password', token=token, _external=True)
            send_reset_email(email, reset_link)
            flash('Password reset link has been sent to your email.')
        else:
            flash('No user found with that username or email.')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The reset link is invalid or expired.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(request.url)

        if len(new_password) < 8:
            flash('Password must be at least 8 characters.')
            return redirect(request.url)

        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
        db.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    cursor.execute("""
        SELECT courses.id, courses.name, courses.semester
        FROM courses
        JOIN teacher_courses ON courses.id = teacher_courses.course_id
        WHERE teacher_courses.teacher_id = %s
    """, (session['user_id'],))

    courses = cursor.fetchall()
    return render_template('teacher_dashboard.html', username=session['username'], courses=courses)

@app.route('/teacher_mcq/<int:course_id>', methods=['GET', 'POST'])
def teacher_mcq(course_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    if request.method == 'POST':
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option'].upper()

        cursor.execute("""
            INSERT INTO mcq_questions (course_id, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (course_id, question, option_a, option_b, option_c, option_d, correct_option))
        db.commit()
        flash("MCQ added successfully.")

    cursor.execute("SELECT * FROM mcq_questions WHERE course_id = %s", (course_id,))
    mcqs = cursor.fetchall()
    return render_template('teacher_mcq.html', mcqs=mcqs, course_id=course_id)

@app.route('/publish_exam/<int:course_id>', methods=['GET', 'POST'])
def publish_exam(course_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    if request.method == 'POST':
        duration = int(request.form['duration'])

        cursor.execute("SELECT * FROM exams WHERE course_id = %s", (course_id,))
        existing_exam = cursor.fetchone()

        if existing_exam:
            cursor.execute("""
                UPDATE exams SET duration_minutes = %s, published = TRUE WHERE course_id = %s
            """, (duration, course_id))
        else:
            cursor.execute("""
                INSERT INTO exams (course_id, duration_minutes, published)
                VALUES (%s, %s, TRUE)
            """, (course_id, duration))

        db.commit()
        flash("Exam published successfully.")
        return redirect(url_for('teacher_dashboard'))

    return render_template('publish_exam.html', course_id=course_id)

@app.route('/student_dashboard')
def student_dashboard():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    cursor.execute("""
        SELECT c.id, c.name, c.semester
        FROM courses c
        JOIN student_courses sc ON c.id = sc.course_id
        WHERE sc.student_id = %s
    """, (session['user_id'],))

    courses = cursor.fetchall()

    return render_template('student_dashboard.html', username=session['username'], courses=courses)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
