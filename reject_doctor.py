import os
from flask import Blueprint, session, request, redirect
import mysql.connector

reject_doctor_blueprint = Blueprint('reject_doctor_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@reject_doctor_blueprint.route('/reject-doctor-action', methods=['GET'])
def reject_doctor_action():
    # 1. Access Control Check: Verify user is a logged-in Administrator
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    role = str(session.get('role', '')).strip().lower()

    if not user_id or (user_type != 'admin' and role != 'admin'):
        return redirect('/static/screen1.html')

    # 2. Extract and cast the target account ID parameter securely
    target_id_raw = request.args.get('id', 0)
    try:
        target_id = int(target_id_raw)
    except ValueError:
        target_id = 0

    # 3. If ID is valid, execute the status modification update
    if target_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                UPDATE users 
                SET approved = 2, status = 'rejected' 
                WHERE id = %s AND (LOWER(user_type) = 'doctor' OR LOWER(role) = 'doctor')
            """
            cursor.execute(sql, (target_id,))
            conn.commit()

        except mysql.connector.Error as err:
            return f"Database update action transaction failed: {err}", 500
        finally:
            cursor.close()
            conn.close()

    # 4. Redirect cleanly back to your master control dashboard view
    return redirect('/admin-dashboard')
