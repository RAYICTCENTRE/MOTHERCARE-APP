import os
from flask import Flask, render_template

# ================= BLUEPRINT IMPORTS =================
from post_symptom_data import post_symptom_blueprint
from consult_doctor import consult_blueprint
from view_doctors import view_doctors_blueprint
from chat_patient import chat_blueprint
from send_message import send_msg_blueprint
from fetch_messages import fetch_msg_blueprint
from edit_message import update_msg_blueprint
from send_doctor_reply import send_doctor_reply_blueprint
from send_reply import send_reply_blueprint

from admin_dashboard import admin_bp
from reject_doctor import reject_doctor_blueprint
from patient_dashboard import patient_bp
from doctor_dashboard import doctor_bp

from get_user_profile import user_profile_blueprint
from get_doctor_profile import doc_profile_fetch_blueprint
from doctor_profile_setup import doc_profile_setup_blueprint
from save_doctor_profile import save_doctor_profile_blueprint

from send_otp import send_otp_blueprint
from verify_otp import verify_otp_blueprint

from login import login_bp

# ================= APP INIT =================
app = Flask(__name__)

# 🔥 REQUIRED FOR RAILWAY SESSION STABILITY
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "mothercare-production-secure-key-9988"
)

# 🔥 SESSION FIX (THIS IS WHAT YOU WERE MISSING)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True

# ================= BLUEPRINT REGISTRATION =================
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
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)

app.register_blueprint(user_profile_blueprint)
app.register_blueprint(doc_profile_fetch_blueprint)
app.register_blueprint(doc_profile_setup_blueprint)
app.register_blueprint(save_doctor_profile_blueprint)

app.register_blueprint(send_otp_blueprint)
app.register_blueprint(verify_otp_blueprint)

app.register_blueprint(login_bp)

# ================= ROUTES =================
@app.route('/')
def index():
    return render_template('screen1.html')

@app.route('/test-db')
def test_db():
    try:
        from login import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db = cursor.fetchone()
        conn.close()
        return f"DB OK: {db}"
    except Exception as e:
        return f"DB ERROR: {str(e)}"

# ================= RUN =================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
