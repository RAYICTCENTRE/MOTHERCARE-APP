import os
from flask import Blueprint, session, request, jsonify
import mysql.connector

# Create the blueprint module cleanly
update_msg_blueprint = Blueprint('update_msg_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@update_msg_blueprint.route('/update-message', methods=['POST'])
def update_message():
    # 1. Access Control Check
    patient_id = session.get('user_id')
    if not patient_id:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    # 2. Extract Data Safely (Handles both Form-data and JSON payloads)
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form

    try:
        message_id = int(data.get('message_id', 0))
    except (ValueError, TypeError):
        message_id = 0

    new_msg = str(data.get('message', '')).strip()

    # 3. Input Validation Check
    if not message_id or not new_msg:
        return jsonify({"success": False, "message": "Invalid input"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 4. Secure Parameterized Execution
        # Restricts the update so users can only edit their own messages
        query = "UPDATE messages SET message = %s WHERE id = %s AND sender_id = %s"
        cursor.execute(query, (new_msg, message_id, patient_id))
        conn.commit()
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database transaction failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"success": True, "message": "Message updated successfully"})
