import traceback
import pymysql
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash
from login import get_db_connection

doctor_bp = Blueprint('doctor_bp', __name__, url_prefix='/doctor')

# ==============================================================================
# DOCTOR AUTHENTICATION DECORATOR
# ==============================================================================
def doctor_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login_bp.login_page'))

        if session.get("user_type") != "doctor":
            flash('Access denied. Doctor privileges required.', 'error')
            return redirect(url_for('login_bp.login_page'))

        return f(*args, **kwargs)
    return wrapper

# ==============================================================================
# DOCTOR ROUTES
# ==============================================================================
@doctor_bp.route('/dashboard')
@doctor_required
def doctor_dashboard():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id, specialty, facility, dcontact
                FROM doctors
                WHERE user_id=%s
            """, (session['user_id'],))
            doctor = cursor.fetchone()

            if not doctor:
                return "<h1>Doctor profile configuration missing</h1><p>Please complete your profile setup.</p>"

            cursor.execute("""
                SELECT DISTINCT u.id, u.firstname, u.lastname, u.email
                FROM users u
                JOIN consultations c ON c.patient_id = u.id
                WHERE c.doctor_id=%s
            """, (doctor['id'],))
            patients = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) as total FROM consultations
                WHERE doctor_id=%s
            """, (doctor['id'],))
            stats = cursor.fetchone()

        return render_template(
            'doctor_dashboard.html',
            doctor=doctor,
            patients=patients,
            stats=stats
        )

    except Exception as e:
        print(traceback.format_exc())
        return f"<h1>Doctor Dashboard Error</h1><p>{str(e)}</p>", 500
    finally:
        if conn:
            conn.close()
