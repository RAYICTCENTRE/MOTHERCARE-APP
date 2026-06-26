import re
import pymysql
from flask import Blueprint, request, session, render_template, url_for, redirect, flash

# Make sure this matches the name string used in app.py blueprint registration
login_bp = Blueprint('login_bp', __name__)

# ================= DB =================
db_host = "reseau.proxy.rlwy.net"
db_port = 15442
db_user = "root"
db_password = "LMaZTqGYVPifqVIdnxJaOZWGXytgIRyC"
db_name = "mothercare"

def get_db_connection():
    return pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# ================= PASSWORD =================
def verify_password(stored, plain):
    return stored == plain

# ================= LOGIN PROCESS =================
@login_bp.route('/login', methods=['POST'])
def login():
    conn = get_db_connection()
    cursor = conn.cursor()

    login_input = request.form.get("login_input")
    password = request.form.get("password")
    
    if not login_input or not password:
        flash("Missing fields", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("login_bp.login_page"))

    is_email = "@" in login_input

    if is_email:
        cursor.execute("SELECT * FROM users WHERE email=%s", (login_input,))
    else:
        phone = re.sub(r"\D", "", login_input)
        cursor.execute("SELECT * FROM users WHERE phone LIKE %s", (f"%{phone[-7:]}",))

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("login_bp.login_page"))

    if user["status"] != "active":
        flash("Account inactive", "error")
        return redirect(url_for("login_bp.login_page"))

    if not verify_password(user["password"], password):
        flash("Wrong password", "error")
        return redirect(url_for("login_bp.login_page"))

    # ================= SESSION =================
    session.clear()
    session["user_id"] = user["id"]
    session["firstname"] = user["firstname"]
    session["user_type"] = user["user_type"]

    role = user["user_type"]

    # ================= REDIRECT LOGIC =================
    # Blueprints resolve to 'blueprint_variable_name.function_name'
    if role == "admin":
        return redirect(url_for("admin_bp.admin_dashboard"))

    elif role == "doctor":
        return redirect(url_for("doctor_bp.doctor_dashboard"))

    elif role == "client":
        return redirect(url_for("patient_bp.patient_dashboard"))

    else:
        flash("Invalid role assignment.", "error")
        return redirect(url_for("login_bp.login_page"))

# ================= LOGIN PAGE =================
@login_bp.route('/login', methods=['GET'])
def login_page():
    return render_template("login.html")

# ================= LOGOUT =================
@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login_bp.login_page"))
