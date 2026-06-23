from flask import Blueprint, render_template, session, redirect, url_for, flash
from functools import wraps
from login import get_db_connection

patient_bp = Blueprint('patient_bp', __name__, url_prefix='/patient')

# ==============================================================================
# PATIENT AUTH DECORATOR
# ==============================================================================
def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login_bp.login_page'))

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_type FROM users WHERE id=%s", (session['user_id'],))
                user = cursor.fetchone()

                if not user or user[0] != 'client':
                    flash('Access denied.', 'error')
                    return redirect(url_for('login_bp.login_page'))

        finally:
            if conn:
                conn.close()

        return f(*args, **kwargs)

    return decorated_function


# ==============================================================================
# PATIENT DASHBOARD (FIXED)
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
            profile = cursor.fetchone()

            if profile is None:
                profile = {}

            # ================= SYMPTOMS =================
            cursor.execute("""
                SELECT *
                FROM symptom_logs
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT 20
            """, (session['user_id'],))
            symptoms = cursor.fetchall()

            if symptoms is None:
                symptoms = []

            # ================= FIXED: PRE-ECLAMPSIA DATA =================
            cursor.execute("""
                SELECT *
                FROM pre_eclampsia_assesment
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT 20
            """, (session['user_id'],))
            assessments = cursor.fetchall()

            if assessments is None:
                assessments = []

            # ================= RENDER =================
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
                <h1>Patient Dashboard</h1>
                <p><b>Template Error:</b> {template_error}</p>

                <h3>Profile</h3>
                <pre>{profile}</pre>

                <h3>Assessments</h3>
                <pre>{assessments}</pre>

                <h3>Symptoms</h3>
                <pre>{symptoms}</pre>

                <a href="/logout">Logout</a>
                """

    except Exception as e:
        return f"""
        <h1>Patient Dashboard Error</h1>
        <p>{str(e)}</p>
        <a href="/logout">Logout</a>
        """, 500

    finally:
        if conn:
            conn.close()
