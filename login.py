import os
import re
import pymysql
from flask import Blueprint, request, session, render_template, jsonify, url_for

login_bp = Blueprint("login_bp", __name__)

# ================= DATABASE =================

DB_HOST = os.getenv("DB_HOST", "reseau.proxy.rlwy.net")
DB_PORT = int(os.getenv("DB_PORT", "15442"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "LMaZTqGYVPifqVIdnxJaOZWGXytgIRyC")
DB_NAME = os.getenv("DB_NAME", "mothercare")


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


# ================= PASSWORD =================

def verify_password(stored_password, entered_password):
    return stored_password == entered_password


# ================= LOGIN PAGE =================

@login_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("screen2.html")


# ================= LOGIN =================

@login_bp.route("/login", methods=["POST"])
def login():

    login_input = request.form.get("login_input", "").strip()
    password = request.form.get("password", "").strip()

    if login_input == "" or password == "":
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        })

    conn = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        if "@" in login_input:

            cursor.execute(
                "SELECT * FROM users WHERE email=%s",
                (login_input,)
            )

        else:

            phone = re.sub(r"\D", "", login_input)

            cursor.execute(
                "SELECT * FROM users WHERE phone LIKE %s",
                (f"%{phone[-7:]}",)
            )

        user = cursor.fetchone()

        cursor.close()

        if not user:

            return jsonify({
                "success": False,
                "message": "User not found."
            })

        if user.get("status") != "active":

            return jsonify({
                "success": False,
                "message": "Your account is inactive."
            })

        if not verify_password(user["password"], password):

            return jsonify({
                "success": False,
                "message": "Wrong password."
            })

        session.clear()

        session["user_id"] = user["id"]
        session["firstname"] = user["firstname"]
        session["user_type"] = user["user_type"]

        role = user["user_type"]

        if role == "admin":

            redirect_url = url_for("admin_bp.admin_dashboard")

        elif role == "doctor":

            redirect_url = url_for("doctor_bp.doctor_dashboard")

        elif role == "client":

            redirect_url = url_for("patient_bp.patient_dashboard")

        else:

            return jsonify({
                "success": False,
                "message": "Invalid account role."
            })

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "redirect": redirect_url
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        })

    finally:

        if conn:
            conn.close()


# ================= LOGOUT =================

@login_bp.route("/logout")
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "redirect": "/login"
    })
