import os
from flask import Blueprint, session, jsonify
import mysql.connector

doc_profile_fetch_blueprint = Blueprint('doc_profile_fetch_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@doc_profile_fetch_blueprint.route('/get-doctor-profile', methods=['GET'])
def get_doctor_profile():
    # 1. Enforce Authentication Protection Boundaries
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not user_id or user_type != 'doctor':
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Parameterized SQL query to safely pull row records
        sql = "SELECT * FROM doctors WHERE user_id = %s"
        cursor.execute(sql, (user_id,))
        profile = cursor.fetchone()

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database query failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    # 3. Return clean JSON response mapping match framework targets
    return jsonify({
        "success": True,
        "profile": profile if profile else None
    })
