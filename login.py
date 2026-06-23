import re
import os
import pymysql
from flask import Blueprint, request, jsonify, session, redirect, url_for

# ==============================================================================
# BLUEPRINT INITIALIZATION
# ==============================================================================
login_bp = Blueprint('login_bp', __name__)

# ==============================================================================
# DATABASE CONFIGURATION - HARDCODED FOR RAILWAY
# ==============================================================================
db_host = "reseau.proxy.rlwy.net"
db_port = 15442
db_user = "root"
db_password = "LMaZTqGYVPifqVIdnxJaOZWGXytgIRyC"
db_name = "mothercare"

def get_db_connection():
    """Create and return a database connection using hardcoded Railway credentials"""
    try:
        print(f"Connecting to: {db_host}:{db_port}/{db_name} as {db_user}")
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=30,
            autocommit=True
        )
        print("Connection successful!")
        return connection
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def normalize_phone(phone, country_code):
    """Normalize phone number with the selected country code."""
    if not phone:
        return phone
    phone = re.sub(r'[\s\-\(\)\.]', '', phone.strip())
    if phone.startswith('0'):
        phone = country_code + phone[1:]
    if not phone.startswith('+'):
        if phone.isdigit() and len(phone) >= 7:
            phone = country_code + phone
    return phone

def verify_password(stored_password, plain_password):
    """
    Verify password against stored password.
    Supports plain text and bcrypt hashes.
    """
    if not stored_password or not plain_password:
        return False
    
    # 1. Check if it's plain text (direct comparison)
    if stored_password == plain_password:
        return True
    
    # 2. Check if it's a bcrypt hash ($2y$ or $2b$)
    if stored_password.startswith('$2y$') or stored_password.startswith('$2b$'):
        try:
            import bcrypt
            return bcrypt.checkpw(plain_password.encode('utf-8'), stored_password.encode('utf-8'))
        except:
            return False
    
    # 3. Check if it's a werkzeug hash
    try:
        from werkzeug.security import check_password_hash
        if check_password_hash(stored_password, plain_password):
            return True
    except:
        pass
    
    return False

# ==============================================================================
# LOGIN ROUTE
# ==============================================================================
@login_bp.route('/login', methods=['POST'])
def login():
    """Handle user login with phone OR email - both work!"""
    conn = None
    try:
        conn = get_db_connection()
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Database connection failed: {str(e)}"
        })

    try:
        # Get form data
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')
        country_code = request.form.get('country_code', '+256')

        # Validate input
        if not login_input or not password:
            return jsonify({
                "success": False, 
                "message": "Please fill in all fields."
            })

        # Check if input is email or phone
        is_email = bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", login_input))

        with conn.cursor() as cursor:
            if is_email:
                # Email login
                sql = """
                    SELECT id, firstname, lastname, email, phone, password, 
                           user_type, approved, status 
                    FROM users 
                    WHERE email = %s
                """
                cursor.execute(sql, (login_input,))
            else:
                # Phone login
                normalized_phone = normalize_phone(login_input, country_code)
                digits_only = re.sub(r'[^0-9]', '', normalized_phone)
                phone_pattern = f"%{digits_only[-7:]}%" if len(digits_only) >= 7 else f"%{digits_only}%"
                
                sql = """
                    SELECT id, firstname, lastname, email, phone, password, 
                           user_type, approved, status 
                    FROM users 
                    WHERE phone = %s OR phone LIKE %s
                """
                cursor.execute(sql, (normalized_phone, phone_pattern))
            
            row = cursor.fetchone()

            # Check if user exists
            if not row:
                return jsonify({
                    "success": False, 
                    "message": "Account not found. Please check your phone number or email."
                })

            # Check if user status is active
            if row.get('status') != 'active':
                return jsonify({
                    "success": False, 
                    "message": "Your account is inactive. Please contact support."
                })

            # Verify password
            stored_password = row.get('password', '')
            
            if not verify_password(stored_password, password):
                return jsonify({
                    "success": False, 
                    "message": "Invalid password. Please try again."
                })

            # Set up session
            session['user_id'] = row['id']
            session['firstname'] = row['firstname']
            session['lastname'] = row['lastname']
            session['email'] = row['email']
            session['phone'] = row['phone']
            session['user_type'] = row['user_type']
            session['logged_in'] = True

            # ==============================================================
            # ✅ ROLE-BASED REDIRECTION - UPDATED FOR FLASK BLUEPRINTS
            # ==============================================================
            user_type = row['user_type']
            redirect_page = ""
            message_suffix = ""

            if user_type == "admin":
                # Redirect to admin dashboard (Flask blueprint route)
                redirect_page = url_for('admin.admin_dashboard')
                message_suffix = "Welcome Admin!"
                
            elif user_type == "doctor":
                # Check if doctor is approved
                if row.get('approved') == 0:
                    return jsonify({
                        "success": False, 
                        "message": "Your account is pending admin approval."
                    })
                
                # Check if doctor has complete profile
                sql_doctor = """
                    SELECT id, specialty, facility, dcontact 
                    FROM doctors 
                    WHERE user_id = %s
                """
                cursor.execute(sql_doctor, (row['id'],))
                doctor_profile = cursor.fetchone()

                if not doctor_profile or not doctor_profile.get('specialty') or not doctor_profile.get('facility') or not doctor_profile.get('dcontact'):
                    # Incomplete profile - redirect to profile setup
                    redirect_page = url_for('doctor_profile_setup_bp.doctor_profile_setup')
                    message_suffix = "Please complete your profile"
                else:
                    # Redirect to doctor dashboard (Flask blueprint route)
                    redirect_page = url_for('doctor_bp.doctor_dashboard')
                    message_suffix = "Welcome Doctor!"
                    
            elif user_type == "client":
                # Check if patient has complete profile
                sql_check = """
                    SELECT id, age, last_period 
                    FROM user_profiles 
                    WHERE user_id = %s
                """
                cursor.execute(sql_check, (row['id'],))
                profile = cursor.fetchone()
                
                if profile and profile.get('age') and profile.get('last_period'):
                    # Redirect to patient dashboard (Flask blueprint route)
                    redirect_page = url_for('patient_bp.patient_dashboard')
                    message_suffix = "Welcome Patient!"
                else:
                    # Incomplete profile - redirect to profile setup
                    redirect_page = url_for('patient_dashboard.patient_dashboard')  # Or your profile setup page
                    message_suffix = "Please complete your profile"
                    
            else:
                # Default fallback
                redirect_page = url_for('login_bp.login_page')
                message_suffix = "Unknown user type"

            return jsonify({
                "success": True, 
                "message": f"Login successful! {message_suffix}",
                "redirect": redirect_page,
                "user_type": user_type,
                "firstname": row['firstname']
            })

    except pymysql.Error as e:
        print(f"Database error: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "A database error occurred. Please try again."
        })
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"An error occurred: {str(e)}"
        })
    finally:
        if conn:
            conn.close()

# ==============================================================================
# LOGOUT ROUTE
# ==============================================================================
@login_bp.route('/logout')
def logout():
    session.clear()
    return jsonify({
        "success": True, 
        "message": "You have been logged out."
    })

# ==============================================================================
# LOGIN PAGE ROUTE (GET)
# ==============================================================================
@login_bp.route('/login', methods=['GET'])
def login_page():
    """Serve the login page"""
    return render_template('login.html')  # You'll need to create this
