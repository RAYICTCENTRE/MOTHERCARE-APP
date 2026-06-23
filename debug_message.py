# debug_messages.py
import os
from flask import Blueprint, session, render_template_string, redirect
import mysql.connector

debug_blueprint = Blueprint('debug_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@debug_blueprint.route('/debug-messages')
def debug_messages():
    if 'user_id' not in session:
        return redirect('/static/screen1.html')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 20")
        messages = cursor.fetchall()

        cursor.execute("SELECT id, firstname, lastname, user_type FROM users")
        users = cursor.fetchall()

    except mysql.connector.Error as err:
        return f"Database diagnostic error: {err}", 500
    finally:
        cursor.close()
        conn.close()

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MotherCare - Diagnostic Console</title>
        <style>
            body { font-family: sans-serif; padding: 20px; background-color: #fcfcfc; color: #222; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 30px; background: #fff; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #e67e22; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            h2 { color: #d35400; padding-bottom: 5px; border-bottom: 2px solid #ffe8d4; }
        </style>
    </head>
    <body>
        <h2>💬 Recent Message Debug Rows</h2>
        <table>
            <tr><th>ID</th><th>Sender ID</th><th>Receiver ID</th><th>Sender Type</th><th>Message Snippet</th><th>Created At</th></tr>
            {% for row in messages %}
            <tr>
                <td>{{ row.id }}</td>
                <td>{{ row.sender_id }}</td>
                <td>{{ row.receiver_id }}</td>
                <td>{{ row.sender_type }}</td>
                <td>{{ row.message[:50] }}</td>
                <td>{{ row.created_at }}</td>
            </tr>
            {% else %}
            <tr><td colspan="6" style="text-align:center; color:#999;">No messages logged inside table yet.</td></tr>
            {% endfor %}
        </table>

        <h2>👥 System Registered Users</h2>
        <table>
            <tr><th>User ID</th><th>Full Name</th><th>Account Classification</th></tr>
            {% for u in users %}
            <tr>
                <td>{{ u.id }}</td>
                <td>{{ u.firstname }} {{ u.lastname }}</td>
                <td><strong>{{ u.user_type | upper }}</strong></td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, messages=messages, users=users)
