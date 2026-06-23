import os
from flask import Flask, render_template, redirect, url_for

# ==============================================================================
# 1. BLUEPRINT CORE MODULE IMPORTS
# ==============================================================================
from post_symptom_data import post_symptom_blueprint
from consult_doctor import consult_blueprint
from view_doctors import view_doctors_blueprint
from chat_patient import chat_blueprint
from send_message import send_msg_blueprint
from fetch_messages import fetch_msg_blueprint
from edit_message import update_msg_blueprint 
from send_doctor_reply import send_doctor_reply_blueprint
from send_reply import send_reply_blueprint

# Dashboard Framework Workspaces & Administrator Action Pipelines
from admin_dashboard import admin_bp  
from reject_doctor import reject_doctor_blueprint
from patient_dashboard import patient_bp  # Fixed import name
from doctor_dashboard import doctor_bp  # Fixed import name

# User Profile Maintenance & Async Summary Payload Blueprints
from get_user_profile import user_profile_blueprint
from get_doctor_profile import doc_profile_fetch_blueprint
from doctor_profile_setup import doc_profile_setup_blueprint
from save_doctor_profile import save_doctor_profile_blueprint

# Security, Gateways, Messaging Relays & OTP Verification Pipelines
from send_otp import send_otp_blueprint
from verify_otp import verify_otp_blueprint

# Login Blueprint
from login import login_bp

# ==============================================================================
# 2. INITIALIZATION & PRODUCTION SECURITY
# ==============================================================================
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'mothercare-production-secure-key-9988')

# ==============================================================================
# 3. GLOBAL BLUEPRINT REGISTER PIPELINE
# ==============================================================================
app.register_blueprint(post_symptom_blueprint)
app.register_blueprint(consult_blueprint)
app.register_blueprint(view_doctors_blueprint)
app.register_blueprint(chat_blueprint)
app.register_blueprint(send_msg_blueprint)
app.register_blueprint(fetch_msg_blueprint)
app.register_blueprint(update_msg_blueprint) 
app.register_blueprint(send_doctor_reply_blueprint)
app.register_blueprint(send_reply_blueprint)

app.register_blueprint(admin_bp)
app.register_blueprint(reject_doctor_blueprint)
app.register_blueprint(patient_bp)  # Fixed
app.register_blueprint(doctor_bp)  # Fixed

app.register_blueprint(user_profile_blueprint)
app.register_blueprint(doc_profile_fetch_blueprint)
app.register_blueprint(doc_profile_setup_blueprint)
app.register_blueprint(save_doctor_profile_blueprint)

app.register_blueprint(send_otp_blueprint)
app.register_blueprint(verify_otp_blueprint)

# Register Login Blueprint
app.register_blueprint(login_bp)

# ==============================================================================
# 4. SYSTEM ENTRY & ROOT REDIRECT
# ==============================================================================
@app.route('/')
def index():
    return render_template('screen1.html')

# ==============================================================================
# 5. TEST DATABASE CONNECTION ROUTE
# ==============================================================================
@app.route('/test-db')
def test_db():
    conn = None
    try:
        from login import get_db_connection
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE() as db_name, NOW() as server_time")
            result = cursor.fetchone()
            return f"✅ Connected successfully!<br>Database: {result['db_name']}<br>Server Time: {result['server_time']}"
    except Exception as e:
        return f"❌ Connection failed: {str(e)}"
    finally:
        if conn is not None:
            conn.close()

# ==============================================================================
# 6. SERVER LAUNCH ENGINE
# ==============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=is_debug)
