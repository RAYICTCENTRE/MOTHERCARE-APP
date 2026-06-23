import os
from datetime import datetime
from flask import Blueprint, session, jsonify
import mysql.connector

user_summary_blueprint = Blueprint('user_summary_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@user_summary_blueprint.route('/get-user-summary', methods=['GET'])
def get_user_summary():
    # 1. Access Control Check
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Unified SQL Query combining user data and profiles
        query = """
            SELECT 
                u.firstname, u.lastname, u.email, u.phone,
                p.age, p.kin_contact, p.last_period
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = %s
        """
        cursor.execute(query, (user_id,))
        record = cursor.fetchone()

        if not record:
            return jsonify({"success": False, "message": "User records not found"}), 404

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database interaction failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    # 3. Dynamic Gestational Age Calculations 
    gestational_age_weeks = None
    last_period_raw = record.get('last_period')
    
    if last_period_raw:
        try:
            # Convert raw date string/object into a Python datetime structure safely
            last_period_date = datetime.strptime(str(last_period_raw), "%Y-%m-%d")
            delta = datetime.now() - last_period_date
            calculated_weeks = delta.days // 7
            
            # Enforce your custom logical boundary criteria checks (4 to 42 weeks)
            if 4 <= calculated_weeks <= 42:
                gestational_age_weeks = int(calculated_weeks)
        except (ValueError, TypeError):
            pass  # Fallback to None if string parsing experiences structural breaks

    # 4. Construct consistent JSON responses
    return jsonify({
        "success": True,
        "firstname": record.get('firstname') or '',
        "lastname": record.get('lastname') or '',
        "email": record.get('email') or '',
        "phone": record.get('phone') or '',
        "age": int(record['age']) if record.get('age') else None,
        "gestational_age_weeks": gestational_age_weeks,
        "last_period": str(last_period_raw) if last_period_raw else None
    })
