# app.py
import os
from flask import Flask, render_template, session, redirect, url_for
from datetime import timedelta

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

from login import login_bp, get_db_connection

# ================= APP INIT =================
app = Flask(__name__)

# 🔥 REQUIRED FOR RAILWAY SESSION STABILITY
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "mothercare-production-secure-key-9988"
)

# 🔥 SESSION CONFIGURATION
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# ================= BLUEPRINT REGISTRATION =================
# Symptom & Consultation Blueprints
app.register_blueprint(post_symptom_blueprint)
app.register_blueprint(consult_blueprint)
app.register_blueprint(view_doctors_blueprint)

# Messaging Blueprints
app.register_blueprint(chat_blueprint)
app.register_blueprint(send_msg_blueprint)
app.register_blueprint(fetch_msg_blueprint)
app.register_blueprint(update_msg_blueprint)
app.register_blueprint(send_doctor_reply_blueprint)
app.register_blueprint(send_reply_blueprint)

# Dashboard Blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(reject_doctor_blueprint)
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)

# Profile Blueprints
app.register_blueprint(user_profile_blueprint)
app.register_blueprint(doc_profile_fetch_blueprint)
app.register_blueprint(doc_profile_setup_blueprint)
app.register_blueprint(save_doctor_profile_blueprint)

# Authentication Blueprints
app.register_blueprint(send_otp_blueprint)
app.register_blueprint(verify_otp_blueprint)
app.register_blueprint(login_bp)

# ================= ROUTES =================
@app.route('/')
def index():
    """Main landing page"""
    # If user is already logged in, redirect to their dashboard
    if 'user_id' in session:
        user_type = session.get('user_type')
        if user_type == 'admin':
            return redirect(url_for('admin_bp.admin_dashboard'))
        elif user_type == 'doctor':
            return redirect(url_for('doctor_bp.doctor_dashboard'))
        elif user_type == 'client':
            return redirect(url_for('patient_bp.patient_dashboard'))
    
    return render_template('screen1.html')

@app.route('/screen1')
def screen1():
    """Alias for landing page"""
    return redirect(url_for('index'))

@app.route('/screen2')
def screen2():
    """Login page alias"""
    return redirect(url_for('login_bp.login_page'))

@app.route('/screen3')
def screen3():
    """Signup page"""
    try:
        return render_template('screen3.html')
    except:
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard_redirect():
    """Redirect to appropriate dashboard based on user type"""
    if 'user_id' not in session:
        return redirect(url_for('login_bp.login_page'))
    
    user_type = session.get('user_type')
    if user_type == 'admin':
        return redirect(url_for('admin_bp.admin_dashboard'))
    elif user_type == 'doctor':
        return redirect(url_for('doctor_bp.doctor_dashboard'))
    elif user_type == 'client':
        return redirect(url_for('patient_bp.patient_dashboard'))
    else:
        return redirect(url_for('index'))

@app.route('/test-db')
def test_db():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE() as db_name")
        db = cursor.fetchone()
        cursor.close()
        conn.close()
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Database Test</title>
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f0f4f8; }}
            .card {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; }}
            .success {{ color: #28a745; font-size: 48px; }}
            h1 {{ color: #1e3a8a; }}
        </style>
        </head>
        <body>
            <div class="card">
                <div class="success">✅</div>
                <h1>Database Connected Successfully!</h1>
                <p>Database: <strong>{db['db_name'] if db else 'Unknown'}</strong></p>
                <p style="color: #6c757d;">MotherCare App is running correctly.</p>
                <a href="/" style="color: #e67e22; text-decoration: none;">← Back to Home</a>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Database Error</title>
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f0f4f8; }}
            .card {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; }}
            .error {{ color: #dc3545; font-size: 48px; }}
            h1 {{ color: #dc3545; }}
        </style>
        </head>
        <body>
            <div class="card">
                <div class="error">❌</div>
                <h1>Database Connection Failed</h1>
                <p style="color: #dc3545;"><strong>Error:</strong> {str(e)}</p>
                <p style="color: #6c757d;">Please check your database configuration.</p>
                <a href="/" style="color: #e67e22; text-decoration: none;">← Back to Home</a>
            </div>
        </body>
        </html>
        """

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "app": "MotherCare",
        "version": "1.0.0"
    }

# ================= ERROR HANDLERS =================
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('screen1.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Server Error</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f0f4f8; text-align: center; }
        .card { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        h1 { color: #dc3545; }
        a { color: #e67e22; text-decoration: none; }
    </style>
    </head>
    <body>
        <div class="card">
            <h1>500 - Server Error</h1>
            <p>Something went wrong. Please try again later.</p>
            <a href="/">← Back to Home</a>
        </div>
    </body>
    </html>
    """, 500

# ================= RUN =================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
