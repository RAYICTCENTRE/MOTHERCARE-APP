from flask import Blueprint, render_template, session, redirect, url_for

doctor_bp = Blueprint('doctor_bp', __name__)

@doctor_bp.route('/doctor/dashboard')
def doctor_dashboard():
    if "user_id" not in session or session.get("user_type") != "doctor":
        return redirect(url_for("login_bp.login_page"))
    return render_template("doctor_dashboard.html")



def doctor_required(f):
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

            if not user or user.get('user_type') != 'doctor':
                return redirect(url_for('login_bp.login_page'))

        except Exception as e:
            print(e)
            return redirect(url_for('login_bp.login_page'))
        finally:
            if conn:
                conn.close()

        return f(*args, **kwargs)
    return wrapper


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
                return "Doctor profile missing"

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
        return f"Doctor error: {str(e)}"
    finally:
        if conn:
            conn.close()
