import re
import pymysql
from flask import Blueprint, request, jsonify, session, render_template, url_for

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
    if stored == plain:
        return True
    return False

# ================= LOGIN =================
@login_bp.route('/login', methods=['POST'])
def login():
    conn = get_db_connection()
    cursor = conn.cursor()

    login_input = request.form.get("login_input")
    password = request.form.get("password")
    country_code = request.form.get("country_code", "+256")

    if not login_input or not password:
        return jsonify({"success": False, "message": "Missing fields"})

    is_email = "@" in login_input

    if is_email:
        cursor.execute("SELECT * FROM users WHERE email=%s", (login_input,))
    else:
        phone = re.sub(r"\D", "", login_input)
        cursor.execute("SELECT * FROM users WHERE phone LIKE %s", (f"%{phone[-7:]}",))

    user = cursor.fetchone()

    if not user:
        return jsonify({"success": False, "message": "User not found"})

    if user["status"] != "active":
        return jsonify({"success": False, "message": "Account inactive"})

    if not verify_password(user["password"], password):
        return jsonify({"success": False, "message": "Wrong password"})

    # ================= SESSION =================
    session.clear()
    session["user_id"] = user["id"]
    session["firstname"] = user["firstname"]
    session["user_type"] = user["user_type"]

    role = user["user_type"]

    # ================= REDIRECT FIX =================
    if role == "admin":
        redirect_url = url_for("admin.admin_dashboard")

    elif role == "doctor":
        redirect_url = url_for("doctor_bp.doctor_dashboard")

    elif role == "client":
        redirect_url = url_for("patient_bp.patient_dashboard")

    else:
        redirect_url = url_for("login_bp.login_page")

    return jsonify({
        "success": True,
        "redirect": redirect_url
    })

# ================= LOGIN PAGE =================
@login_bp.route('/login', methods=['GET'])
def login_page():
    return render_template("login.html")

# ================= LOGOUT =================
@login_bp.route('/logout')
def logout():
    session.clear()
    return jsonify({"success": True})
