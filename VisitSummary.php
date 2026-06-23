import os
from flask import Flask, redirect, url_for

# ==============================================================================
# BLUEPRINT IMPORTS
# ==============================================================================
from post_symptom_data import post_symptom_blueprint
from consult_doctor import consult_blueprint
from chat_patient import chat_blueprint
from debug_messages import debug_blueprint
from fetch_messages import fetch_msg_blueprint
from get_user_summary import user_summary_blueprint
from update_message import update_msg_blueprint
from check_doctor_reply import check_reply_blueprint
from admin_dashboard import admin_blueprint
from doctor_dashboard import doctor_blueprint
from doctor_messages import doctor_messages_blueprint
from doctor_profile_setup import doc_profile_setup_blueprint
from get_doctor_profile import doc_profile_fetch_blueprint
from get_user_profile import user_profile_blueprint
from patient_dashboard import patient_dashboard_blueprint
from reject_doctor import reject_doctor_blueprint
from save_doctor_profile import save_doctor_profile_blueprint
from send_doctor_reply import send_doctor_reply_blueprint
from send_message import send_msg_blueprint
from send_otp import send_otp_blueprint
from send_reply import send_reply_blueprint
from verify_otp import verify_otp_blueprint
from view_doctors import view_doctors_blueprint
from visit_summary import visit_summary_blueprint          # Import using updated name

app = Flask(__name__)

# ==============================================================================
# PRODUCTION SECURITY & SESSIONS
# ==============================================================================
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-fallback-secure-string-12345')

# ==============================================================================
# BLUEPRINT REGISTRATIONS
# ==============================================================================
app.register_blueprint(post_symptom_blueprint)
app.register_blueprint(consult_blueprint)
app.register_blueprint(chat_blueprint)
app.register_blueprint(debug_blueprint)
app.register_blueprint(fetch_msg_blueprint)
app.register_blueprint(user_summary_blueprint)
app.register_blueprint(update_msg_blueprint)
app.register_blueprint(check_reply_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(doctor_blueprint)
app.register_blueprint(doctor_messages_blueprint)
app.register_blueprint(doc_profile_setup_blueprint)
app.register_blueprint(doc_profile_fetch_blueprint)
app.register_blueprint(user_profile_blueprint)
app.register_blueprint(patient_dashboard_blueprint)
app.register_blueprint(reject_doctor_blueprint)
app.register_blueprint(save_doctor_profile_blueprint)
app.register_blueprint(send_doctor_reply_blueprint)
app.register_blueprint(send_msg_blueprint)
app.register_blueprint(send_otp_blueprint)
app.register_blueprint(send_reply_blueprint)
app.register_blueprint(verify_otp_blueprint)
app.register_blueprint(view_doctors_blueprint)
app.register_blueprint(visit_summary_blueprint)          # Register updated module name tracking


# ==============================================================================
# ROOT REDIRECT
# ==============================================================================
@app.route('/')
def index():
    return redirect(url_for('static', filename='screen1.html'))


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=is_debug)
