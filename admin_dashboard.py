import traceback
import pymysql
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash
from login import get_db_connection

# Matches app.py registration: app.register_blueprint(admin_bp)
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# ==============================================================================
# ADMIN AUTHENTICATION DECORATOR
# ==============================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login_bp.login_page'))
        
        if session.get("user_type") != "admin":
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login_bp.login_page'))
            
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# ADMIN ROUTES
# ==============================================================================
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard showing all doctors and patients"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get all doctors with their status
            try:
                cursor.execute("""
                    SELECT id, full_name, email, specialization, qualification, 
                           experience_years, status, created_at 
                    FROM doctors 
                    ORDER BY created_at DESC
                """)
                doctors = cursor.fetchall()
            except Exception as e:
                # Fallback to users table if doctors table doesn't exist
                cursor.execute("""
                    SELECT id, firstname as full_name, email, 'N/A' as specialization,
                           'N/A' as qualification, 0 as experience_years,
                           'active' as status, created_at 
                    FROM users 
                    WHERE user_type = 'doctor'
                    ORDER BY created_at DESC
                """)
                doctors = cursor.fetchall()
            
            # Get all patients
            try:
                cursor.execute("""
                    SELECT id, full_name, email, created_at 
                    FROM patients 
                    ORDER BY created_at DESC
                """)
                patients = cursor.fetchall()
            except Exception as e:
                # Fallback to users table if patients table doesn't exist
                cursor.execute("""
                    SELECT id, firstname as full_name, email, created_at 
                    FROM users 
                    WHERE user_type = 'client'
                    ORDER BY created_at DESC
                """)
                patients = cursor.fetchall()
            
            # Get statistics
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_doctors,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_doctors,
                        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_doctors,
                        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_doctors
                    FROM doctors
                """)
                stats = cursor.fetchone()
            except Exception as e:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_doctors,
                        0 as pending_doctors,
                        COUNT(*) as approved_doctors,
                        0 as rejected_doctors
                    FROM users 
                    WHERE user_type = 'doctor'
                """)
                stats = cursor.fetchone()
            
            # Get patient count
            try:
                cursor.execute("SELECT COUNT(*) as total_patients FROM patients")
                patient_stats = cursor.fetchone()
            except Exception as e:
                cursor.execute("SELECT COUNT(*) as total_patients FROM users WHERE user_type = 'client'")
                patient_stats = cursor.fetchone()
            
            try:
                return render_template('admin_dashboard.html', 
                                     doctors=doctors, 
                                     patients=patients,
                                     stats=stats,
                                     patient_stats=patient_stats)
            except Exception as template_error:
                return f"""
                <!DOCTYPE html>
                <html>
                <head><title>Admin Dashboard</title></head>
                <body>
                    <h1>Admin Dashboard (HTML Fallback)</h1>
                    <h2>Statistics</h2>
                    <ul>
                        <li>Total Doctors: {stats.get('total_doctors', 0) if stats else 0}</li>
                        <li>Pending Doctors: {stats.get('pending_doctors', 0) if stats else 0}</li>
                        <li>Approved Doctors: {stats.get('approved_doctors', 0) if stats else 0}</li>
                        <li>Total Patients: {patient_stats.get('total_patients', 0) if patient_stats else 0}</li>
                    </ul>
                    <h2>Doctors List</h2>
                    <ul>
                    {''.join([f"<li>{doc.get('full_name', 'Unknown')} - {doc.get('email', 'No email')}</li>" for doc in doctors])}
                    </ul>
                    <h2>Patients List</h2>
                    <ul>
                    {''.join([f"<li>{pat.get('full_name', 'Unknown')} - {pat.get('email', 'No email')}</li>" for pat in patients])}
                    </ul>
                    <p><a href="/logout">Logout</a></p>
                </body>
                </html>
                """
                
    except Exception as e:
        print(f"Error in admin_dashboard: {str(e)}")
        traceback.print_exc()
        return f"<h1>Admin Dashboard Error</h1><p>{str(e)}</p>", 500
    finally:
        if conn:
            conn.close()
