from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from login import get_db_connection
import traceback

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ======================
# ADMIN AUTH DECORATOR
# ======================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_bp.login_page'))

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_type FROM users WHERE id=%s", (session['user_id'],))
                user = cursor.fetchone()

            if not user or user.get('user_type') != 'admin':
                return redirect(url_for('login_bp.login_page'))

        except Exception as e:
            print(e)
            return redirect(url_for('login_bp.login_page'))
        finally:
            if conn:
                conn.close()

        return f(*args, **kwargs)
    return decorated_function


# ======================
# DASHBOARD
# ======================
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:

            # DOCTORS
            try:
                cursor.execute("""
                    SELECT id, full_name, email, specialization, qualification,
                           experience_years, status, created_at
                    FROM doctors
                    ORDER BY created_at DESC
                """)
                doctors = cursor.fetchall()
            except:
                cursor.execute("""
                    SELECT id, firstname AS full_name, email,
                           'N/A' AS specialization, 'N/A' AS qualification,
                           0 AS experience_years, 'active' AS status,
                           created_at
                    FROM users
                    WHERE user_type='doctor'
                """)
                doctors = cursor.fetchall()

            # PATIENTS
            try:
                cursor.execute("SELECT id, full_name, email, created_at FROM patients")
                patients = cursor.fetchall()
            except:
                cursor.execute("""
                    SELECT id, firstname AS full_name, email, created_at
                    FROM users
                    WHERE user_type='client'
                """)
                patients = cursor.fetchall()

        return render_template(
            'admin_dashboard.html',
            doctors=doctors,
            patients=patients
        )

    except Exception as e:
        print(traceback.format_exc())
        return f"Admin error: {str(e)}"
    finally:
        if conn:
            conn.close()
