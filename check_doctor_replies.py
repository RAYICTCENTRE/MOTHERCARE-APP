import os
from flask import Blueprint, session, render_template_string, redirect
import mysql.connector

check_reply_blueprint = Blueprint('check_reply_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@check_reply_blueprint.route('/check-doctor-reply')
def check_doctor_reply():
    # 1. Security Check: Only allow logged-in users to access diagnostic information
    if 'user_id' not in session:
        return redirect('/static/screen1.html')

    # Hardcoded test case targets matching your precise PHP testing setup
    doctor_id = 8
    patient_id = 10
    messages = []
    has_doctor_replies = False

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. SQL execution targeting message history
        sql = """
            SELECT id, sender_id, receiver_id, sender_type, message, status, created_at
            FROM messages
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at ASC
        """
        cursor.execute(sql, (patient_id, doctor_id, doctor_id, patient_id))
        messages = cursor.fetchall()

        # Check if doctor replies exist inside the query result matrix
        for row in messages:
            if row['sender_type'] == 'doctor':
                has_doctor_replies = True

    except mysql.connector.Error as err:
        return f"Database query failed: {err}", 500
    finally:
        cursor.close()
        conn.close()

    # 3. Dynamic layout configuration script
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MotherCare - Reply Diagnostics</title>
        <style>
            body { font-family: sans-serif; padding: 20px; background-color: #fcfcfc; }
            h2 { color: #2c3e50; border-bottom: 2px solid #ddd; padding-bottom: 8px; }
            table { border-collapse: collapse; width: 100%; margin-top: 15px; background: #fff; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #333; color: white; }
            .status-container { margin-top: 20px; padding: 15px; border-radius: 8px; font-weight: bold; }
            .success-box { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error-box { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <h2>Check Doctor Replies (Doctor ID 8, Patient ID 10)</h2>
        
        <table>
            <tr>
                <th>ID</th>
                <th>Sender ID</th>
                <th>Receiver ID</th>
                <th>Sender Type</th>
                <th>Message</th>
                <th>Status</th>
                <th>Created</th>
            </tr>
            {% for row in messages %}
            <tr style="background: {{ '#d4edda' if row.sender_type == 'doctor' else '#fff3cd' }};">
                <td>{{ row.id }}</td>
                <td>{{ row.sender_id }}</td>
                <td>{{ row.receiver_id }}</td>
                <td><strong>{{ row.sender_type }}</strong></td>
                <td>{{ row.message }}</td>
                <td>{{ row.status }}</td>
                <td>{{ row.created_at }}</td>
            </tr>
            {% else %}
            <tr><td colspan="7" style="text-align:center; color:#999;">No message records found between these users.</td></tr>
            {% endfor %}
        </table>

        {% if not has_doctor_replies %}
        <div class="status-container error-box">
            <p>⚠️ NO DOCTOR REPLIES FOUND in the database!</p>
            <p style="font-weight: normal; font-size: 14px; margin-top: 5px;">
                This means the doctor's replies are not being saved correctly.
            </p>
        </div>
        {% else %}
        <div class="status-container success-box">
            <p>✅ Doctor replies found in database!</p>
            <p style="font-weight: normal; font-size: 14px; margin-top: 5px;">
                If doctor replies exist but are not showing in the chat interface, the issue is with fetch_messages.py.
            </p>
        </div>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(
        html_template, 
        messages=messages, 
        has_doctor_replies=has_doctor_replies
    )
