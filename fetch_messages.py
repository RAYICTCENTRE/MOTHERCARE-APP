import os
from flask import Blueprint, session, request, jsonify
import mysql.connector

fetch_msg_blueprint = Blueprint('fetch_msg_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@fetch_msg_blueprint.route('/fetch-messages', methods=['GET'])
def fetch_messages():
    # 1. Session and Authentication Verification
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({"error": "Not logged in"}), 401

    # 2. Extract incoming parameters (Checks doctor_id first, then patient_id)
    other_user_id_raw = request.args.get('doctor_id') or request.args.get('patient_id') or 0
    try:
        other_user_id = int(other_user_id_raw)
    except ValueError:
        other_user_id = 0

    if not other_user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 3. Retrieve conversation thread history
        sql = """
            SELECT id, sender_id, receiver_id, sender_type, message, status, created_at
            FROM messages
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at ASC
        """
        cursor.execute(sql, (current_user_id, other_user_id, other_user_id, current_user_id))
        rows = cursor.fetchall()

        messages = []
        unread_message_ids = []

        # 4. Process payload rows and isolate unread indices
        for row in rows:
            # Safely handle native Python datetime objects for JSON encoding consistency
            created_at_str = row['created_at'].strftime("%Y-%m-%d %H:%M:%S") if row['created_at'] else ""
            
            # If the current user is the receiver and the message status is 'sent', track it to mark as read
            if int(row['receiver_id']) == int(current_user_id) and row['status'] == 'sent':
                unread_message_ids.append(row['id'])
                row['status'] = 'read'  # Update locally for the immediate API response

            messages.append({
                "id": row['id'],
                "sender_id": row['sender_id'],
                "receiver_id": row['receiver_id'],
                "sender": row['sender_type'],
                "message": row['message'],
                "status": row['status'],
                "created_at": created_at_str
            })

        # 5. Bulk update unread records to 'read' status in a single transaction
        if unread_message_ids:
            # Creates placeholder format string structure (e.g., %s, %s, %s) dynamically
            format_placeholders = ', '.join(['%s'] * len(unread_message_ids))
            update_sql = f"""
                UPDATE messages 
                SET status = 'read', read_at = NOW() 
                WHERE id IN ({format_placeholders})
            """
            cursor.execute(update_sql, tuple(unread_message_ids))
            conn.commit()

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database processing failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(messages)
