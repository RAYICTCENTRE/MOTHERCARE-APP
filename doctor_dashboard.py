from flask import Blueprint, render_template, session, redirect, url_for, flash
from functools import wraps
from login import get_db_connection
import mysql.connector

# ==============================================================================
# CREATE BLUEPRINT
# ==============================================================================
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
        
        user_id = session['user_id']
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT user_type FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user.get('user_type') != 'doctor':
                    flash('Access denied. Doctor privileges required.', 'error')
                    return redirect(url_for('login_bp.login_page'))
        except Exception as e:
            flash(f'Database error: {str(e)}', 'error')
            return redirect(url_for('login_bp.login_page'))
        finally:
            if conn:
                conn.close()
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# DOCTOR DASHBOARD ROUTE
# ==============================================================================
@doctor_bp.route('/dashboard')
@doctor_required
def doctor_dashboard():
    """Doctor dashboard showing patients and consultations"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Get doctor's info
            cursor.execute("""
                SELECT id, specialty, facility, dcontact 
                FROM doctors 
                WHERE user_id = %s
            """, (session['user_id'],))
            doctor = cursor.fetchone()
            
            # Get doctor's patients
            cursor.execute("""
                SELECT DISTINCT u.id, u.firstname, u.lastname, u.email, u.phone
                FROM users u
                JOIN consultations c ON c.patient_id = u.id
                WHERE c.doctor_id = %s
                ORDER BY u.firstname
            """, (doctor['id'],))
            patients = cursor.fetchall()
            
            # Get consultation statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_consultations,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM consultations
                WHERE doctor_id = %s
            """, (doctor['id'],))
            stats = cursor.fetchone()
            
            # Get recent consultations
            cursor.execute("""
                SELECT c.*, u.firstname, u.lastname 
                FROM consultations c
                JOIN users u ON c.patient_id = u.id
                WHERE c.doctor_id = %s
                ORDER BY c.created_at DESC
                LIMIT 10
            """, (doctor['id'],))
            consultations = cursor.fetchall()
            
            # Try to render template
            try:
                return render_template('doctor_dashboard.html',
                                     doctor=doctor,
                                     patients=patients,
                                     stats=stats,
                                     consultations=consultations,
                                     user=session)
            except Exception as template_error:
                print(f"Template error: {template_error}")
                # Fallback HTML
                return f"""
                <!DOCTYPE html>
                <html>
                <head><title>Doctor Dashboard</title></head>
                <body>
                    <h1>Doctor Dashboard</h1>
                    <p>Welcome Dr. {session.get('firstname', '')}!</p>
                    <h2>Statistics</h2>
                    <ul>
                        <li>Total Consultations: {stats.get('total_consultations', 0)}</li>
                        <li>Pending: {stats.get('pending', 0)}</li>
                        <li>Completed: {stats.get('completed', 0)}</li>
                    </ul>
                    <h2>My Patients ({len(patients)})</h2>
                    <ul>
                    {''.join([f"<li>{p.get('firstname', '')} {p.get('lastname', '')} - {p.get('email', '')}</li>" for p in patients])}
                    </ul>
                    <p><a href="/logout">Logout</a></p>
                </body>
                </html>
                """
                
    except Exception as e:
        print(f"Error in doctor_dashboard: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Doctor Dashboard Error</title></head>
        <body>
            <h1>Error Loading Dashboard</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/logout">Logout</a></p>
        </body>
        </html>
        """, 500
    finally:
        if conn:
            conn.close()
