import os
from flask import Blueprint, session, render_template, redirect, request, jsonify
import mysql.connector

doctor_blueprint = Blueprint('doctor_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@doctor_blueprint.route('/doctor-dashboard', methods=['GET'])
def doctor_dashboard():
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not user_id or user_type != 'doctor':
        return redirect('/static/screen2.html')

    doctor_name = session.get('firstname', 'Doctor')
    is_approved = False
    is_profile_complete = False
    profile_data = {}

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check approval status
        cursor.execute("SELECT approved FROM users WHERE id = %s", (user_id,))
        user_record = cursor.fetchone()
        is_approved = (user_record and user_record.get('approved') == 1)

        # Check profile status
        cursor.execute("SELECT specialty, facility, dcontact FROM doctors WHERE user_id = %s", (user_id,))
        profile_data = cursor.fetchone() or {}
        
        if profile_data and profile_data.get('specialty') and profile_data.get('facility') and profile_data.get('dcontact'):
            is_profile_complete = True

    except mysql.connector.Error as err:
        return f"Database query failed: {err}", 500
    finally:
        cursor.close()
        conn.close()

    # Determine state string matching your logical flow branches
    if not is_approved:
        current_state = 'pending'
    elif not is_profile_complete:
        current_state = 'setup'
    else:
        current_state = 'active'

    # Single unified HTML file rendering call
    return render_template(
        'doctor_dashboard.html', 
        state=current_state, 
        doctor_name=doctor_name, 
        profile=profile_data
    )
