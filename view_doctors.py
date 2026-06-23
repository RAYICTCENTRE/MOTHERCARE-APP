import os
from flask import Blueprint, render_template, session, redirect
import mysql.connector

view_doctors_blueprint = Blueprint('view_doctors_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@view_doctors_blueprint.route('/view-doctors', methods=['GET'])
def view_doctors():
    # Optional Session Security: Uncomment if only logged-in users can view this list
    # if 'user_id' not in session:
    #     return redirect('/static/screen1.html')

    doctors = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch doctor profiles matching your original query
        sql = "SELECT id, photo_path, specialty, facility, qualifications, created_at FROM doctors ORDER BY created_at DESC"
        cursor.execute(sql)
        doctors = cursor.fetchall()
        
    except mysql.connector.Error as err:
        return f"Database query failed: {err}", 500
    finally:
        cursor.close()
        conn.close()

    return render_template('view_doctors.html', doctors=doctors)
