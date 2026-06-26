import traceback
import pymysql
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash
from login import get_db_connection

patient_bp = Blueprint('patient_bp', __name__, url_prefix='/patient')

# ==============================================================================
# PATIENT AUTHENTICATION DECORATOR
# ==============================================================================
def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login_bp.login_page'))

        if session.get("user_type") != "client":
            flash('Access denied. Patient credentials required.', 'error')
            return redirect(url_for('login_bp.login_page'))

        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# PATIENT ROUTES
# ==============================================================================
@patient_bp.route('/dashboard')
@patient_required
def patient_dashboard():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:

            # ================= PROFILE =================
            cursor.execute("""
                SELECT age, last_period, expected_delivery
                FROM user_profiles
                WHERE user_id=%s
            """, (session['user_id'],))
            profile = cursor.fetchone() or {}

            # ================= SYMPTOMS =================
            cursor.execute("""
                SELECT *
                FROM symptom_logs
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT 20
            """, (session['user_id'],))
            symptoms = cursor.fetchall() or []

            # ================= PRE-ECLAMPSIA DATA =================
            cursor.execute("""
                SELECT *
                FROM pre_eclampsia_assesment
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT 20
            """, (session['user_id'],))
            assessments = cursor.fetchall() or []

            try:
                return render_template(
                    'patient_dashboard.html',
                    profile=profile,
                    symptoms=symptoms,
                    assessments=assessments,
                    user=session
                )
            except Exception as template_error:
                return f"""
                <h1>Patient Dashboard (HTML Fallback)</h1>
                <p><b>Template Error:</b> {template_error}</p>
                <h3>Profile Data</h3><pre>{profile}</pre>
                <h3>Assessments Log</h3><pre>{assessments}</pre>
                <h3>Symptoms Log</h3><pre>{symptoms}</pre>
                <a href="/logout">Logout</a>
                """

    except Exception as e:
        print(traceback.format_exc())
        return f"<h1>Patient Dashboard Error</h1><p>{str(e)}</p>", 500
    finally:
        if conn:
            conn.close()
