import os
from flask import Blueprint, session, request, jsonify
import mysql.connector

send_doctor_reply_blueprint = Blueprint('send_doctor_reply_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@send_doctor_reply_blueprint.route('/send-doctor-reply', methods=['POST'])
def send_doctor_reply():
    # 1. Enforce Authentication Protection Boundaries
    doctor_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not doctor_id or user_type != 'doctor':
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    # 2. Extract Data Safely (Handles both Form-data and JSON payloads)
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form

    try:
        patient_id = int(data.get('receiver_id', 0))
    except (ValueError, TypeError):
        patient_id = 0

    message = str(data.get('message', '')).strip()

    # 3. Input Validation Check
    if not patient_id or not message:
        return jsonify({"success": False, "message": "Missing data"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 4. Verify target patient profile exists in system tables
        cursor.execute("SELECT id FROM users WHERE id = %s AND LOWER(user_type) = 'client'", (patient_id,))
        patient_exists = cursor.fetchone() is not None

        if not patient_exists:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Patient not found"}), 404

        # 5. Insert the response message row transaction safely
        sql = """
            INSERT INTO messages (sender_id, receiver_id, sender_type, message, status, created_at)
            VALUES (%s, %s, 'doctor', %s, 'sent', NOW())
        """
        cursor.execute(sql, (doctor_id, patient_id, message))
        conn.commit()

        return jsonify({"success": True, "message": "Reply sent successfully"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database processing failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()
