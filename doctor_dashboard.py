# doctor_dashboard.py
import traceback
import pymysql
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from login import get_db_connection

doctor_bp = Blueprint('doctor_bp', __name__, url_prefix='/doctor')

# ==============================================================================
# DOCTOR AUTHENTICATION DECORATOR
# ==============================================================================
def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login_bp.login_page'))
        
        if session.get("user_type") != "doctor":
            flash('Access denied. Doctor privileges required.', 'error')
            return redirect(url_for('login_bp.login_page'))
            
        # Check if doctor is approved
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM doctors WHERE user_id = %s
                """, (session['user_id'],))
                doctor = cursor.fetchone()
                
                if not doctor or doctor['status'] != 'approved':
                    flash('Your account is pending approval. Please wait for admin verification.', 'warning')
                    return redirect(url_for('login_bp.login_page'))
        finally:
            conn.close()
            
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# DOCTOR ROUTES
# ==============================================================================
@doctor_bp.route('/dashboard')
@doctor_required
def doctor_dashboard():
    """Doctor dashboard showing patients and consultations"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # Get doctor profile
            cursor.execute("""
                SELECT * FROM doctors WHERE user_id = %s
            """, (session['user_id'],))
            doctor = cursor.fetchone()
            
            # Get doctor's patients (patients who have consulted this doctor)
            cursor.execute("""
                SELECT DISTINCT u.id, u.firstname, u.lastname, u.email, u.phone,
                       up.age, up.expected_delivery
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                INNER JOIN consultations c ON u.id = c.patient_id
                WHERE c.doctor_id = %s AND u.user_type = 'client'
                ORDER BY c.created_at DESC
                LIMIT 50
            """, (session['user_id'],))
            patients = cursor.fetchall()
            
            # Get recent consultations
            cursor.execute("""
                SELECT c.*, u.firstname as patient_name, u.email as patient_email
                FROM consultations c
                JOIN users u ON c.patient_id = u.id
                WHERE c.doctor_id = %s
                ORDER BY c.created_at DESC
                LIMIT 20
            """, (session['user_id'],))
            consultations = cursor.fetchall()
            
            # Get pending messages
            cursor.execute("""
                SELECT m.*, u.firstname as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.receiver_id = %s AND m.is_read = FALSE
                ORDER BY m.created_at DESC
                LIMIT 10
            """, (session['user_id'],))
            messages = cursor.fetchall()
            
            # Statistics
            total_patients = len(patients)
            total_consultations = len(consultations)
            unread_messages = len(messages)
            
            try:
                return render_template('doctor_dashboard.html',
                                     doctor=doctor,
                                     patients=patients,
                                     consultations=consultations,
                                     messages=messages,
                                     total_patients=total_patients,
                                     total_consultations=total_consultations,
                                     unread_messages=unread_messages,
                                     user=session)
            except Exception as template_error:
                # Fallback HTML
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Doctor Dashboard</title>
                    <style>
                        body {{ font-family: sans-serif; padding: 20px; background: #f0f4f8; }}
                        .card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; }}
                        h1 {{ color: #1a472a; }}
                        table {{ width: 100%; border-collapse: collapse; }}
                        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
                        a {{ color: #e67e22; }}
                    </style>
                </head>
                <body>
                    <h1>Doctor Dashboard</h1>
                    <p>Welcome, Dr. {session.get('firstname', 'Doctor')}!</p>
                    <div class="card">
                        <h2>Statistics</h2>
                        <p>Total Patients: {total_patients}</p>
                        <p>Total Consultations: {total_consultations}</p>
                        <p>Unread Messages: {unread_messages}</p>
                    </div>
                    <p><a href="/logout">Logout</a></p>
                </body>
                </html>
                """
                
    except Exception as e:
        print(f"Doctor dashboard error: {traceback.format_exc()}")
        return f"<h1>Error</h1><p>{str(e)}</p>", 500
    finally:
        if conn:
            conn.close()
