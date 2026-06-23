from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from login import get_db_connection
import mysql.connector
from datetime import datetime
import traceback  # Add this for detailed error logging

# ==============================================================================
# CREATE BLUEPRINT FIRST - BEFORE ANY OTHER OPERATIONS
# ==============================================================================
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==============================================================================
# ADMIN AUTHENTICATION DECORATOR
# ==============================================================================
def admin_required(f):
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
                # Check if user_type is 'admin' instead of 'role'
                cursor.execute("SELECT user_type FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user.get('user_type') != 'admin':
                    flash('Access denied. Admin privileges required.', 'error')
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
# ADMIN ROUTES
# ==============================================================================

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard showing all doctors and patients"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Get all doctors with their status
            # Check if doctors table exists, if not, use users table
            try:
                cursor.execute("""
                    SELECT id, full_name, email, specialization, qualification, 
                           experience_years, status, created_at 
                    FROM doctors 
                    ORDER BY created_at DESC
                """)
                doctors = cursor.fetchall()
            except mysql.connector.Error as e:
                # If doctors table doesn't exist, try users table
                print(f"Doctors table error: {e}")
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
            except mysql.connector.Error as e:
                # If patients table doesn't exist, try users table
                print(f"Patients table error: {e}")
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
            except:
                # If doctors table doesn't exist, get stats from users
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
            except:
                cursor.execute("SELECT COUNT(*) as total_patients FROM users WHERE user_type = 'client'")
                patient_stats = cursor.fetchone()
            
            # Try to render template, if it fails, return simple HTML
            try:
                return render_template('admin_dashboard.html', 
                                     doctors=doctors, 
                                     patients=patients,
                                     stats=stats,
                                     patient_stats=patient_stats)
            except Exception as template_error:
                # If template is missing, return a simple HTML page
                print(f"Template error: {template_error}")
                return f"""
                <!DOCTYPE html>
                <html>
                <head><title>Admin Dashboard</title></head>
                <body>
                    <h1>Admin Dashboard</h1>
                    <p>Welcome Admin!</p>
                    <h2>Statistics</h2>
                    <ul>
                        <li>Total Doctors: {stats.get('total_doctors', 0)}</li>
                        <li>Pending Doctors: {stats.get('pending_doctors', 0)}</li>
                        <li>Approved Doctors: {stats.get('approved_doctors', 0)}</li>
                        <li>Total Patients: {patient_stats.get('total_patients', 0)}</li>
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
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Admin Dashboard Error</title></head>
        <body>
            <h1>Error Loading Dashboard</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please check the logs for more details.</p>
            <p><a href="/logout">Logout</a></p>
        </body>
        </html>
        """, 500
    finally:
        if conn:
            conn.close()

@admin_bp.route('/doctor/<int:doctor_id>/approve', methods=['POST'])
@admin_required
def approve_doctor(doctor_id):
    """Approve a doctor's registration"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                UPDATE doctors 
                SET status = 'approved', 
                    updated_at = NOW() 
                WHERE id = %s
            """, (doctor_id,))
            conn.commit()
            
            # Get doctor info for notification
            cursor.execute("SELECT full_name, email FROM doctors WHERE id = %s", (doctor_id,))
            doctor = cursor.fetchone()
            
            flash(f'✅ Doctor {doctor["full_name"]} has been approved successfully!', 'success')
            
    except Exception as e:
        flash(f'Error approving doctor: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/doctor/<int:doctor_id>/reject', methods=['POST'])
@admin_required
def reject_doctor(doctor_id):
    """Reject a doctor's registration"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Get doctor info before update
            cursor.execute("SELECT full_name, email FROM doctors WHERE id = %s", (doctor_id,))
            doctor = cursor.fetchone()
            
            cursor.execute("""
                UPDATE doctors 
                SET status = 'rejected', 
                    updated_at = NOW() 
                WHERE id = %s
            """, (doctor_id,))
            conn.commit()
            
            flash(f'❌ Doctor {doctor["full_name"]} has been rejected.', 'warning')
            
    except Exception as e:
        flash(f'Error rejecting doctor: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/patient/<int:patient_id>/delete', methods=['POST'])
@admin_required
def delete_patient(patient_id):
    """Delete a patient record"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
            conn.commit()
            flash('Patient deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting patient: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/doctor/<int:doctor_id>/delete', methods=['POST'])
@admin_required
def delete_doctor(doctor_id):
    """Delete a doctor record"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
            conn.commit()
            flash('Doctor deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting doctor: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin.admin_dashboard'))

# ==============================================================================
# API ENDPOINTS FOR AJAX REQUESTS
# ==============================================================================

@admin_bp.route('/api/stats')
@admin_required
def get_stats():
    """Get dashboard statistics as JSON"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Doctor statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_doctors,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                FROM doctors
            """)
            doctor_stats = cursor.fetchone()
            
            # Patient statistics
            cursor.execute("SELECT COUNT(*) as total_patients FROM patients")
            patient_stats = cursor.fetchone()
            
            # Recent activity
            cursor.execute("""
                (SELECT 'doctor' as type, full_name as name, status, created_at 
                 FROM doctors 
                 ORDER BY created_at DESC 
                 LIMIT 5)
                UNION
                (SELECT 'patient' as type, full_name as name, 'active' as status, created_at 
                 FROM patients 
                 ORDER BY created_at DESC 
                 LIMIT 5)
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent_activity = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'doctor_stats': doctor_stats,
                'patient_stats': patient_stats,
                'recent_activity': recent_activity
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()
