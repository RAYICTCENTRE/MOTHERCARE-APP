import os
from flask import Blueprint, session, request, jsonify
from werkzeug.security import generate_password_hash
import mysql.connector

verify_otp_blueprint = Blueprint('verify_otp_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@verify_otp_blueprint.route('/verify-otp', methods=['POST'])
def verify_otp():
    # 1. Extract Data Safely (Handles both Form-data and JSON payloads)
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form

    identifier = str(data.get('identifier', '')).strip()
    otp = str(data.get('otp', '')).strip()
    new_password = str(data.get('new_password', '')).strip()

    # 2. Input Validation Checks
    if not identifier or not otp or not new_password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if len(new_password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 3. Find user by email or phone
        user_sql = "SELECT id, firstname, lastname, email, phone FROM users WHERE email = %s OR phone = %s"
        cursor.execute(user_sql, (identifier, identifier))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404

        user_id = user['id']

        # 4. Verify OTP validity against expiration time stamps
        otp_sql = """
            SELECT * FROM password_resets 
            WHERE user_id = %s AND otp = %s AND expires_at > NOW() 
            ORDER BY created_at DESC LIMIT 1
        """
        cursor.execute(otp_sql, (user_id, otp))
        reset_record = cursor.fetchone()

        if not reset_record:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400

        # 5. Securely Hashing the Password (Matches PHP bcrypt/scrypt defaults)
        hashed_password = generate_password_hash(new_password)

        # 6. Execute password modification update transaction
        update_sql = "UPDATE users SET password = %s WHERE id = %s"
        cursor.execute(update_sql, (hashed_password, user_id))

        # 7. Purge spent/used OTP tokens from the tracking table
        delete_sql = "DELETE FROM password_resets WHERE user_id = %s"
        cursor.execute(delete_sql, (user_id,))
        
        # Finalize the database writes
        conn.commit()

        # 8. Clear transient reset values from Flask dynamic sessions
        session.pop('reset_user_id', None)
        session.pop('reset_otp', None)
        session.pop('reset_expires', None)

        return jsonify({"success": True, "message": "Password reset successful"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database processing failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()
