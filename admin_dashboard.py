from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from login import get_db_connection
import mysql.connector
from datetime import datetime

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
            return redirect(url_for('login.login_page'))
        
        user_id = session['user_id']
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user['role'] != 'admin':
                    flash('Access denied. Admin privileges required.', 'error')
                    return redirect(url_for('login.login_page'))
        except Exception as e:
            flash(f'Database error: {str(e)}', 'error')
            return redirect(url_for('login.login_page'))
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
            cursor.execute("""
                SELECT id, full_name, email, specialization, qualification, 
                       experience_years, status, created_at 
                FROM doctors 
                ORDER BY created_at DESC
            """)
            doctors = cursor.fetchall()
            
            # Get all patients
            cursor.execute("""
                SELECT id, full_name, email, created_at 
                FROM patients 
                ORDER BY created_at DESC
            """)
            patients = cursor.fetchall()
            
            # Get statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_doctors,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_doctors,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_doctors,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_doctors
                FROM doctors
            """)
            stats = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as total_patients FROM patients")
            patient_stats = cursor.fetchone()
            
            return render_template('admin_dashboard.html', 
                                 doctors=doctors, 
                                 patients=patients,
                                 stats=stats,
                                 patient_stats=patient_stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin_dashboard.html', 
                             doctors=[], 
                             patients=[],
                             stats={'total_doctors': 0, 'pending_doctors': 0, 
                                   'approved_doctors': 0, 'rejected_doctors': 0},
                             patient_stats={'total_patients': 0})
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
            
            # You can add email notification here if needed
            
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
            
            # You can add email notification here if needed
            
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

# ==============================================================================
# DO NOT REGISTER THE BLUEPRINT HERE - DO IT IN APP.PY
# ==============================================================================
# REMOVED: app.register_blueprint(admin_bp) - This was causing the error
