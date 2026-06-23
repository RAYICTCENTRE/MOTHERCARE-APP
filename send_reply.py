import os
from flask import Blueprint, session, request, jsonify
import mysql.connector

send_reply_blueprint = Blueprint('send_reply_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@send_reply_blueprint.route('/send-reply', methods=['POST'])
def send_reply():
    doctor_id = session.get('user_id')
    data = request.get_json() or {}
    
    try:
        message_id = int(data.get('message_id', 0))
        patient_id = int(data.get('patient_id', 0))
    except (ValueError, TypeError):
        message_id = 0
        patient_id = 0
        
    reply = str(data.get('reply', '')).strip()

    if not doctor_id or not message_id or not patient_id or not reply:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO message_replies (message_id, doctor_id, patient_id, reply_text, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(sql, (message_id, doctor_id, patient_id, reply))
        conn.commit()
        return jsonify({"success": True})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Failed to save reply: {err}"}), 500
    finally:
        cursor.close()
        conn.close()
