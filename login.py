# login.py
import os
import re
import traceback
import pymysql
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

login_bp = Blueprint('login_bp', __name__)

# ==============================================================================
# DATABASE CONNECTION
# ==============================================================================
def get_db_connection():
    """Create and return database connection"""
    try:
        conn = pymysql.connect(
            host=os.environ.get('MYSQLHOST', 'localhost'),
            user=os.environ.get('MYSQLUSER', 'root'),
            password=os.environ.get('MYSQLPASSWORD', ''),
            database=os.environ.get('MYSQLDATABASE', 'mothercare_db'),
            port=int(os.environ.get('MYSQLPORT', 3306)),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

# ==============================================================================
# LOGIN ROUTES
# ==============================================================================
@login_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    """Handle login - screen2.html"""
    if request.method == 'GET':
        # If user is already logged in, redirect to their dashboard
        if 'user_id' in session:
            user_type = session.get('user_type')
            if user_type == 'admin':
                return redirect('/admin/dashboard')
            elif user_type == 'doctor':
                return redirect('/doctor/dashboard')
            elif user_type == 'client':
                return redirect('/patient/dashboard')
        
        # Render the login page (screen2.html)
        return render_template('screen2.html')

    # ========== POST REQUEST - PROCESS LOGIN ==========
    conn = None
    try:
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '').strip()
        country_code = request.form.get('country_code', '+256')

        # Validate inputs
        if not login_input:
            return jsonify({'success': False, 'message': 'Please enter your phone number or email.'}), 400
        if not password:
            return jsonify({'success': False, 'message': 'Please enter your password.'}), 400

        # Determine if input is email or phone
        is_email = '@' in login_input and '.' in login_input
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            
            if is_email:
                # LOGIN WITH EMAIL
                cursor.execute("""
                    SELECT id, firstname, lastname, email, phone, password, user_type, status 
                    FROM users WHERE email = %s
                """, (login_input,))
            else:
                # LOGIN WITH PHONE
                # Clean phone number
                phone_digits = re.sub(r'\D', '', login_input)
                
                # Try matching with or without country code
                cursor.execute("""
                    SELECT id, firstname, lastname, email, phone, password, user_type, status 
                    FROM users WHERE phone = %s OR phone = %s
                """, (phone_digits, country_code + phone_digits))
            
            user = cursor.fetchone()

            # Check if user exists
            if not user:
                return jsonify({
                    'success': False, 
                    'message': 'No account found. Please check your credentials or sign up.'
                }), 401

            # Verify password
            if not check_password_hash(user['password'], password):
                return jsonify({
                    'success': False, 
                    'message': 'Incorrect password. Please try again.'
                }), 401

            # Check account status
            if user['status'] == 'suspended':
                return jsonify({
                    'success': False, 
                    'message': 'Your account has been suspended. Contact support.'
                }), 403
            
            if user['status'] == 'pending' and user['user_type'] == 'doctor':
                return jsonify({
                    'success': False, 
                    'message': 'Your doctor account is pending approval. Please wait.'
                }), 403

            # === LOGIN SUCCESSFUL ===
            # Set session
            session['user_id'] = user['id']
            session['firstname'] = user['firstname']
            session['lastname'] = user.get('lastname', '')
            session['email'] = user['email']
            session['phone'] = user.get('phone', '')
            session['user_type'] = user['user_type']
            session['logged_in'] = True

            # Update last login
            cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                         (datetime.now(), user['id']))
            conn.commit()

            # Determine redirect based on user type
            redirect_urls = {
                'admin': '/admin/dashboard',
                'doctor': '/doctor/dashboard',
                'client': '/patient/dashboard'
            }
            redirect_url = redirect_urls.get(user['user_type'], '/')

            return jsonify({
                'success': True,
                'message': f'Welcome back, {user["firstname"]}!',
                'redirect': redirect_url,
                'user_type': user['user_type']
            })

    except Exception as e:
        print(f"Login error: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'message': 'Login failed. Please try again.'
        }), 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# SIGNUP ROUTE
# ==============================================================================
@login_bp.route('/signup', methods=['POST'])
def signup():
    """Handle user registration from screen3.html"""
    conn = None
    try:
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        user_type = request.form.get('user_type', 'client')

        # Validation
        if not all([firstname, email, phone, password]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields.'
            }), 400

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address.'
            }), 400

        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters.'
            }), 400

        if password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Passwords do not match.'
            }), 400

        # Clean phone
        phone_clean = re.sub(r'\D', '', phone)
        if len(phone_clean) < 10:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid phone number.'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            
            # Check existing email
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'An account with this email already exists.'
                }), 409

            # Check existing phone
            cursor.execute("SELECT id FROM users WHERE phone = %s", (phone_clean,))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'An account with this phone number already exists.'
                }), 409

            # Hash password
            hashed_password = generate_password_hash(password)

            # Set status based on user type
            status = 'pending' if user_type == 'doctor' else 'active'

            # Insert user
            cursor.execute("""
                INSERT INTO users (firstname, lastname, email, phone, password, user_type, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (firstname, lastname, email, phone_clean, hashed_password, user_type, status, datetime.now()))
            
            user_id = cursor.lastrowid
            
            # If doctor, add to doctors table
            if user_type == 'doctor':
                cursor.execute("""
                    INSERT INTO doctors (user_id, full_name, email, status, created_at)
                    VALUES (%s, %s, %s, 'pending', %s)
                """, (user_id, f"{firstname} {lastname}", email, datetime.now()))
            
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Account created! You can now login.',
                'redirect': '/login'
            })

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Signup error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again.'
        }), 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# LOGOUT ROUTE
# ==============================================================================
@login_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')
