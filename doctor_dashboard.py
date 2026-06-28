# doctor_dashboard.py
import traceback
import pymysql
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
from login import get_db_connection
from datetime import datetime

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
                
                if not doctor:
                    flash('Doctor profile not found. Please complete your profile setup.', 'warning')
                    return redirect(url_for('doctor_profile_setup.setup_profile'))
                    
                if doctor['status'] != 'approved':
                    flash('Your account is pending approval. Please wait for admin verification.', 'warning')
                    return redirect(url_for('login_bp.login_page'))
        finally:
            conn.close()
            
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# DOCTOR DASHBOARD ROUTE
# ==============================================================================
@doctor_bp.route('/dashboard')
@doctor_required
def doctor_dashboard():
    """Main doctor dashboard showing patients, consultations, and messages"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # Get doctor profile
            cursor.execute("""
                SELECT id, user_id, full_name, email, phone, specialization, 
                       qualification, experience_years, license_number, 
                       hospital_affiliation, bio, profile_photo, status
                FROM doctors 
                WHERE user_id = %s
            """, (session['user_id'],))
            doctor = cursor.fetchone()
            
            if not doctor:
                flash('Please complete your profile setup first.', 'warning')
                return redirect(url_for('doctor_profile_setup.setup_profile'))
            
            # Get doctor's patients (patients who have consulted this doctor)
            cursor.execute("""
                SELECT DISTINCT 
                    u.id, u.firstname, u.lastname, u.email, u.phone,
                    up.age, up.expected_delivery, up.blood_group,
                    (SELECT COUNT(*) FROM consultations c2 
                     WHERE c2.patient_id = u.id AND c2.doctor_id = %s) as consultation_count
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                INNER JOIN consultations c ON u.id = c.patient_id
                WHERE c.doctor_id = %s AND u.user_type = 'client'
                ORDER BY c.created_at DESC
                LIMIT 50
            """, (session['user_id'], session['user_id']))
            patients = cursor.fetchall()
            
            # Get recent consultations
            cursor.execute("""
                SELECT c.id, c.patient_id, c.doctor_id, c.symptoms, c.diagnosis, 
                       c.prescription, c.notes, c.status, c.created_at,
                       u.firstname as patient_name, u.lastname as patient_lastname,
                       u.email as patient_email, u.phone as patient_phone
                FROM consultations c
                JOIN users u ON c.patient_id = u.id
                WHERE c.doctor_id = %s
                ORDER BY c.created_at DESC
                LIMIT 20
            """, (session['user_id'],))
            consultations = cursor.fetchall()
            
            # Get unread messages
            cursor.execute("""
                SELECT m.id, m.sender_id, m.receiver_id, m.message, m.is_read, m.created_at,
                       u.firstname as sender_name, u.lastname as sender_lastname,
                       u.user_type as sender_type
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.receiver_id = %s AND m.is_read = FALSE
                ORDER BY m.created_at DESC
                LIMIT 10
            """, (session['user_id'],))
            unread_messages = cursor.fetchall()
            
            # Get all messages (recent)
            cursor.execute("""
                SELECT m.id, m.sender_id, m.receiver_id, m.message, m.is_read, m.created_at,
                       u.firstname as sender_name, u.lastname as sender_lastname
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.receiver_id = %s OR m.sender_id = %s
                ORDER BY m.created_at DESC
                LIMIT 30
            """, (session['user_id'], session['user_id']))
            all_messages = cursor.fetchall()
            
            # Get pending consultation requests
            cursor.execute("""
                SELECT c.id, c.patient_id, c.symptoms, c.created_at,
                       u.firstname as patient_name, u.lastname as patient_lastname,
                       u.email as patient_email
                FROM consultations c
                JOIN users u ON c.patient_id = u.id
                WHERE c.doctor_id = %s AND c.status = 'pending'
                ORDER BY c.created_at DESC
            """, (session['user_id'],))
            pending_consultations = cursor.fetchall()
            
            # Statistics
            total_patients = len(patients) if patients else 0
            total_consultations = len(consultations) if consultations else 0
            unread_count = len(unread_messages) if unread_messages else 0
            pending_count = len(pending_consultations) if pending_consultations else 0
            
            # Active consultations
            active_consultations = [c for c in consultations if c.get('status') == 'active']
            active_count = len(active_consultations)
            
            try:
                return render_template('doctor_dashboard.html',
                                     doctor=doctor,
                                     patients=patients,
                                     consultations=consultations,
                                     unread_messages=unread_messages,
                                     all_messages=all_messages,
                                     pending_consultations=pending_consultations,
                                     total_patients=total_patients,
                                     total_consultations=total_consultations,
                                     unread_count=unread_count,
                                     pending_count=pending_count,
                                     active_count=active_count,
                                     user=session)
            except Exception as template_error:
                print(f"Template error: {template_error}")
                traceback.print_exc()
                
                # Fallback HTML response
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Doctor Dashboard - MotherCare</title>
                    <style>
                        body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; background: #f0f4f8; margin: 0; }}
                        .header {{ background: #1e3a8a; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                        .header h1 {{ margin: 0; }}
                        .card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
                        h2 {{ color: #1e3a8a; border-bottom: 2px solid #fbbf24; padding-bottom: 10px; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                        th {{ background: #f8f9fa; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; }}
                        td {{ padding: 12px; border-bottom: 1px solid #ecf0f1; }}
                        tr:hover {{ background: #f8f9fa; }}
                        .badge {{ padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: 600; }}
                        .badge-pending {{ background: #fff3cd; color: #856404; }}
                        .badge-active {{ background: #d4edda; color: #155724; }}
                        .badge-completed {{ background: #cce5ff; color: #004085; }}
                        .btn {{ padding: 8px 15px; border-radius: 6px; text-decoration: none; color: white; display: inline-block; margin: 2px; font-size: 13px; }}
                        .btn-primary {{ background: #1e3a8a; }}
                        .btn-success {{ background: #28a745; }}
                        .btn-danger {{ background: #dc3545; }}
                        .btn-warning {{ background: #ffc107; color: #000; }}
                        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }}
                        .stat-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
                        .stat-card .number {{ font-size: 32px; font-weight: bold; color: #1e3a8a; }}
                        .stat-card .label {{ color: #6c757d; font-size: 13px; margin-top: 5px; }}
                        a {{ color: #1e3a8a; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🏥 Doctor Dashboard</h1>
                        <p>Welcome, Dr. {session.get('firstname', 'Doctor')} {session.get('lastname', '')}!</p>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="number">{total_patients}</div>
                            <div class="label">Total Patients</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{total_consultations}</div>
                            <div class="label">Consultations</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{unread_count}</div>
                            <div class="label">Unread Messages</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{pending_count}</div>
                            <div class="label">Pending Requests</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>📋 My Patients ({total_patients})</h2>
                        <table>
                            <tr>
                                <th>Patient Name</th>
                                <th>Email</th>
                                <th>Expected Delivery</th>
                                <th>Consultations</th>
                                <th>Actions</th>
                            </tr>
                            {''.join([f'''
                            <tr>
                                <td><strong>{p.get('firstname', '')} {p.get('lastname', '')}</strong></td>
                                <td>{p.get('email', 'N/A')}</td>
                                <td>{p.get('expected_delivery', 'Not set')}</td>
                                <td>{p.get('consultation_count', 0)}</td>
                                <td>
                                    <a href="/doctor/view-patient/{p.get('id')}" class="btn btn-primary">View</a>
                                    <a href="/chat-patient?patient_id={p.get('id')}" class="btn btn-success">Chat</a>
                                </td>
                            </tr>
                            ''' for p in patients]) if patients else '<tr><td colspan="5" style="text-align:center;">No patients yet</td></tr>'}
                        </table>
                    </div>
                    
                    <div class="card">
                        <h2>🩺 Recent Consultations</h2>
                        <table>
                            <tr>
                                <th>Patient</th>
                                <th>Date</th>
                                <th>Symptoms</th>
                                <th>Status</th>
                            </tr>
                            {''.join([f'''
                            <tr>
                                <td>{c.get('patient_name', '')} {c.get('patient_lastname', '')}</td>
                                <td>{c.get('created_at', 'N/A')}</td>
                                <td>{(c.get('symptoms', '') or '')[:50]}...</td>
                                <td><span class="badge badge-{c.get('status', 'pending')}">{c.get('status', 'pending')}</span></td>
                            </tr>
                            ''' for c in consultations]) if consultations else '<tr><td colspan="4" style="text-align:center;">No consultations yet</td></tr>'}
                        </table>
                    </div>
                    
                    <p style="margin-top: 20px;">
                        <a href="/logout" class="btn btn-danger">🚪 Logout</a>
                    </p>
                </body>
                </html>
                """
                
    except Exception as e:
        print(f"Doctor dashboard error: {traceback.format_exc()}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Dashboard Error</h1>
            <p>An error occurred while loading your dashboard.</p>
            <p style="color: red;">{str(e)}</p>
            <a href="/logout">Logout</a>
        </body>
        </html>
        """, 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# VIEW PATIENT DETAILS
# ==============================================================================
@doctor_bp.route('/view-patient/<int:patient_id>')
@doctor_required
def view_patient(patient_id):
    """View detailed patient information"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # Get patient details
            cursor.execute("""
                SELECT u.id, u.firstname, u.lastname, u.email, u.phone, u.created_at,
                       up.age, up.last_period, up.expected_delivery, up.blood_group,
                       up.weight, up.height, up.medical_history
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE u.id = %s AND u.user_type = 'client'
            """, (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash('Patient not found.', 'error')
                return redirect(url_for('doctor_bp.doctor_dashboard'))
            
            # Get patient's assessments
            cursor.execute("""
                SELECT * FROM pre_eclampsia_assesment 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (patient_id,))
            assessments = cursor.fetchall()
            
            # Get patient's consultations with this doctor
            cursor.execute("""
                SELECT * FROM consultations 
                WHERE patient_id = %s AND doctor_id = %s 
                ORDER BY created_at DESC
            """, (patient_id, session['user_id']))
            consultations = cursor.fetchall()
            
            # Get symptom logs
            cursor.execute("""
                SELECT * FROM symptom_logs 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (patient_id,))
            symptoms = cursor.fetchall()
            
            try:
                return render_template('patient_details.html',
                                     patient=patient,
                                     assessments=assessments,
                                     consultations=consultations,
                                     symptoms=symptoms)
            except:
                # Fallback
                return f"""
                <h1>Patient: {patient.get('firstname')} {patient.get('lastname')}</h1>
                <p>Email: {patient.get('email')}</p>
                <p>Phone: {patient.get('phone', 'N/A')}</p>
                <p>Expected Delivery: {patient.get('expected_delivery', 'Not set')}</p>
                <p><a href="/doctor/dashboard">Back to Dashboard</a></p>
                """
                
    except Exception as e:
        print(f"View patient error: {traceback.format_exc()}")
        flash(f'Error viewing patient: {str(e)}', 'error')
        return redirect(url_for('doctor_bp.doctor_dashboard'))
    finally:
        if conn:
            conn.close()

# ==============================================================================
# UPDATE CONSULTATION
# ==============================================================================
@doctor_bp.route('/update-consultation/<int:consultation_id>', methods=['POST'])
@doctor_required
def update_consultation(consultation_id):
    """Update consultation with diagnosis and prescription"""
    conn = None
    try:
        diagnosis = request.form.get('diagnosis', '').strip()
        prescription = request.form.get('prescription', '').strip()
        notes = request.form.get('notes', '').strip()
        status = request.form.get('status', 'active')
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE consultations 
                SET diagnosis = %s, prescription = %s, notes = %s, status = %s, updated_at = %s
                WHERE id = %s AND doctor_id = %s
            """, (diagnosis, prescription, notes, status, datetime.now(), consultation_id, session['user_id']))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Consultation updated successfully!'
            })
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Update consultation error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error updating consultation: {str(e)}'
        }), 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# GET CONSULTATION DETAILS (API)
# ==============================================================================
@doctor_bp.route('/api/consultation/<int:consultation_id>')
@doctor_required
def get_consultation_api(consultation_id):
    """API endpoint to get consultation details"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT c.*, u.firstname as patient_name, u.lastname as patient_lastname,
                       u.email as patient_email, u.phone as patient_phone
                FROM consultations c
                JOIN users u ON c.patient_id = u.id
                WHERE c.id = %s AND c.doctor_id = %s
            """, (consultation_id, session['user_id']))
            
            consultation = cursor.fetchone()
            
            if not consultation:
                return jsonify({'success': False, 'message': 'Consultation not found'}), 404
            
            return jsonify({
                'success': True,
                'consultation': consultation
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# GET DOCTOR PROFILE (API)
# ==============================================================================
@doctor_bp.route('/api/profile')
@doctor_required
def get_doctor_profile_api():
    """API endpoint to get doctor profile"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM doctors WHERE user_id = %s
            """, (session['user_id'],))
            
            doctor = cursor.fetchone()
            
            if not doctor:
                return jsonify({'success': False, 'message': 'Profile not found'}), 404
            
            return jsonify({
                'success': True,
                'doctor': doctor
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# MARK MESSAGE AS READ
# ==============================================================================
@doctor_bp.route('/mark-message-read/<int:message_id>', methods=['POST'])
@doctor_required
def mark_message_read(message_id):
    """Mark a message as read"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE messages SET is_read = TRUE 
                WHERE id = %s AND receiver_id = %s
            """, (message_id, session['user_id']))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Message marked as read'
            })
            
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()
