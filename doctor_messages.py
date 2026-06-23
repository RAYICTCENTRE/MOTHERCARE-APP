import os
from flask import Blueprint, session, jsonify
import mysql.connector

# Name the blueprint to match your file structure
doctor_messages_blueprint = Blueprint('doctor_messages_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@doctor_messages_blueprint.route('/fetch-doctor-chats', methods=['GET'])
def fetch_doctor_chats():
    # 1. Enforce Authentication Protection Boundaries
    if 'user_id' not in session:
        return jsonify([]), 401

    doctor_id = session['user_id']  # Logged in doctor
    messages = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Parameterized SQL query to prevent injection
        sql = """
            SELECT m.id, m.message, m.sender, m.created_at, u.firstname, u.lastname 
            FROM messages m 
            JOIN users u ON m.patient_id = u.id
            WHERE m.doctor_id = %s 
            ORDER BY m.created_at ASC
        """
        cursor.execute(sql, (doctor_id,))
        rows = cursor.fetchall()

        # 3. Handle data conversions smoothly
        for row in rows:
            # Safely format native Python datetime objects for clean JSON string conversion
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            messages.append(row)

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database interaction failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    # 4. Return clean JSON array matching your original front-end expectations
    return jsonify(messages)
