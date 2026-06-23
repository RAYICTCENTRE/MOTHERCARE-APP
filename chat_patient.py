import os
from flask import Blueprint, render_template, session, redirect, request, abort
import mysql.connector

chat_blueprint = Blueprint('chat_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@chat_blueprint.route('/chat-patient')
def chat_patient():
    # 1. Access Controls Check (Only active client sessions allowed)
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not user_id or user_type != 'client':
        return redirect('/static/screen1.html')

    # 2. Extract and cast incoming URL doctor_id safely
    try:
        doctor_id = int(request.args.get('doctor_id', 0))
    except ValueError:
        doctor_id = 0

    if not doctor_id:
        return "Doctor not specified", 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 3. Query secure target indicators
        sql = "SELECT firstname, lastname FROM users WHERE id = %s AND user_type = 'doctor'"
        cursor.execute(sql, (doctor_id,))
        doctor = cursor.fetchone()

        if not doctor:
            return "Doctor not found", 404

    except mysql.connector.Error as err:
        return f"Database query failed: {err}", 500
    finally:
        cursor.close()
        conn.close()

    # 4. Bind view layout metrics over Jinja placeholders
    return render_template('chat_patient.html', doctor=doctor, doctor_id=doctor_id)
