import os
from flask import Blueprint, session, jsonify
import mysql.connector

user_profile_blueprint = Blueprint('user_profile_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@user_profile_blueprint.route('/get-user-profile', methods=['GET'])
def get_user_profile():
    # 1. Get user_id from active session
    user_id = session.get('user_id')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Session Fallback matching your exact PHP logic (seeds user_id if missing)
        if not user_id:
            cursor.execute("SELECT id FROM users LIMIT 1")
            fallback_row = cursor.fetchone()
            if fallback_row:
                user_id = fallback_row['id']
                session['user_id'] = user_id
            else:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "error": "No users found"}), 404

        # 3. Optimized Query combining user metrics and profiles using a single JOIN
        sql = """
            SELECT 
                u.firstname, u.lastname,
                p.age, p.last_period, p.nearest_health
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = %s
        """
        cursor.execute(sql, (user_id,))
        record = cursor.fetchone()

        if not record:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "User entry records not found"}), 404

        # 4. Construct separated dictionaries to perfectly match your frontend expectations
        user_data = {
            "firstname": record.get('firstname'),
            "lastname": record.get('lastname')
        }

        # Convert date safely to prevent native Python datetime string execution breaks
        last_period_raw = record.get('last_period')
        last_period_str = str(last_period_raw) if last_period_raw else None

        profile_data = {
            "age": record.get('age'),
            "last_period": last_period_str,
            "nearest_health": record.get('nearest_health')
        }

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database processing break: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    # 5. Output exact JSON matching format structures expected by screens
    return jsonify({
        "success": True,
        "profile": profile_data,
        "user": user_data,
        "user_id": user_id
    })
