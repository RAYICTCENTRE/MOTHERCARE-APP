from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from login import get_db_connection
import traceback

patient_bp = Blueprint('patient_bp', __name__, url_prefix='/patient')


def patient_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_bp.login_page'))

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_type FROM users WHERE id=%s", (session['user_id'],))
                user = cursor.fetchone()

            if not user or user.get('user_type') != 'client':
                return redirect(url_for('login_bp.login_page'))

        except Exception as e:
            print(e)
            return redirect(url_for('login_bp.login_page'))
        finally:
            if conn:
                conn.close()

        return f(*args, **kwargs)
    return wrapper


@patient_bp.route('/dashboard')
@patient_required
def patient_dashboard():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT age, last_period, expected_delivery
                FROM user_profiles
                WHERE user_id=%s
            """, (session['user_id'],))
            profile = cursor.fetchone()

            cursor.execute("""
                SELECT * FROM consultations
                WHERE patient_id=%s
            """, (session['user_id'],))
            consultations = cursor.fetchall()

            cursor.execute("""
                SELECT * FROM symptom_logs
                WHERE user_id=%s
            """, (session['user_id'],))
            symptoms = cursor.fetchall()

        return render_template(
            'patient_dashboard.html',
            profile=profile,
            consultations=consultations,
            symptoms=symptoms
        )

    except Exception as e:
        print(traceback.format_exc())
        return f"Patient error: {str(e)}"
    finally:
        if conn:
            conn.close()
