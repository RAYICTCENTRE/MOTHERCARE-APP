import os
from flask import Blueprint, render_template, session, redirect, url_for
import mysql.connector

# Create blueprint for doctor consultations
consult_blueprint = Blueprint('consult_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@consult_blueprint.route('/consult-doctor')
def consult_doctor():
    # 1. Secure Access Check - Client validation matching PHP trimmings
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not user_id or user_type != 'client':
        return redirect('/screen2.html')

    doctors = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 2. SQL execution targeting approved doctors
        sql = """
            SELECT 
                u.id, u.firstname, u.lastname,
                d.photo_path, d.specialty, d.facility,
                d.dcontact, d.qualifications
            FROM users u
            LEFT JOIN doctors d ON u.id = d.user_id
            WHERE LOWER(u.user_type) = 'doctor' AND u.approved = 1
            ORDER BY u.firstname ASC
        """
        cursor.execute(sql)
        doctors = cursor.fetchall()
        
    except mysql.connector.Error as err:
        return f"Database query failed: {err}", 500
    finally:
        cursor.close()
        conn.close()

    # 3. Render HTML UI while passing doctors collection data natively
    return render_template('consult_doctor.html', doctors=doctors)
