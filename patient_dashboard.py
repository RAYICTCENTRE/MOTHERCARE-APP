from flask import Blueprint, render_template, session, redirect, url_for, flash
from functools import wraps
from login import get_db_connection
import mysql.connector

# ==============================================================================
# CREATE BLUEPRINT
# ==============================================================================
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
        
        user_id = session['user_id']
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT user_type FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user.get('user_type') != 'client':
                    flash('Access denied. Patient privileges required.', 'error')
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
# PATIENT DASHBOARD ROUTE
# ==============================================================================
@patient_bp.route('/dashboard')
@patient_required
def patient_dashboard():
    """Patient dashboard showing health records and consultations"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Get patient's profile
            cursor.execute("""
                SELECT age, last_period, expected_delivery 
                FROM user_profiles 
                WHERE user_id = %s
            """, (session['user_id'],))
            profile = cursor.fetchone()
            
            # Get patient's consultations
            cursor.execute("""
                SELECT c.*, d.full_name as doctor_name, d.specialty
                FROM consultations c
                JOIN doctors d ON c.doctor_id = d.id
                WHERE c.patient_id = (
                    SELECT id FROM users WHERE id = %s
                )
                ORDER BY c.created_at DESC
                LIMIT 10
            """, (session['user_id'],))
            consultations = cursor.fetchall()
            
            # Get symptom history
            cursor.execute("""
                SELECT * FROM symptom_logs 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (session['user_id'],))
            symptoms = cursor.fetchall()
            
            # Try to render template
            try:
                return render_template('patient_dashboard.html',
                                     profile=profile,
                                     consultations=consultations,
                                     symptoms=symptoms,
                                     user=session)
            except Exception as template_error:
                print(f"Template error: {template_error}")
                return f"""
                <!DOCTYPE html>
                <html>
                <head><title>Patient Dashboard</title></head>
                <body>
                    <h1>Patient Dashboard</h1>
                    <p>Welcome {session.get('firstname', '')}!</p>
                    <h2>Your Profile</h2>
                    <ul>
                        <li>Age: {profile.get('age', 'Not set')}</li>
                        <li>Last Period: {profile.get('last_period', 'Not set')}</li>
                        <li>Expected Delivery: {profile.get('expected_delivery', 'Not set')}</li>
                    </ul>
                    <h2>Consultations ({len(consultations)})</h2>
                    <ul>
                    {''.join([f"<li>{c.get('doctor_name', '')} - {c.get('specialty', '')} - {c.get('status', '')}</li>" for c in consultations])}
                    </ul>
                    <p><a href="/logout">Logout</a></p>
                </body>
                </html>
                """
                
    except Exception as e:
        print(f"Error in patient_dashboard: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Patient Dashboard Error</title></head>
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
