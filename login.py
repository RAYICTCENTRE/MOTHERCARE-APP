# login.py
import traceback
import pymysql
import os
import re
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
# LOGIN PAGE ROUTE
# ==============================================================================
@login_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    """Handle login page display and authentication"""
    if request.method == 'GET':
        # If already logged in, redirect to appropriate dashboard
        if 'user_id' in session:
            user_type = session.get('user_type')
            if user_type == 'admin':
                return redirect(url_for('admin_bp.admin_dashboard'))
            elif user_type == 'doctor':
                return redirect(url_for('doctor_bp.doctor_dashboard'))
            elif user_type == 'client':
                return redirect(url_for('patient_bp.patient_dashboard'))
        
        # Render login page
        try:
            return render_template('screen2.html')
        except:
            return redirect(url_for('index'))

    # POST request - Process login
    conn = None
    try:
        # Get form data
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '').strip()
        country_code = request.form.get('country_code', '+256')

        # Validate input
        if not login_input or not password:
            return jsonify({
                'success': False,
                'message': 'Please provide both login credentials and password.'
            }), 400

        # Determine if input is email or phone
        is_email = '@' in login_input and '.' in login_input.split('@')[1] if '@' in login_input else False
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            
            if is_email:
                # Login with email
                cursor.execute("""
                    SELECT id, firstname, lastname, email, password, user_type, status
                    FROM users 
                    WHERE email = %s
                """, (login_input,))
            else:
                # Login with phone (clean the phone number)
                phone_number = re.sub(r'\D', '', login_input)
                full_phone = f"{country_code}{phone_number}" if not phone_number.startswith('+') else phone_number
                
                cursor.execute("""
                    SELECT id, firstname, lastname, email, password, user_type, status
                    FROM users 
                    WHERE phone = %s OR phone = %s
                """, (phone_number, full_phone))
            
            user = cursor.fetchone()

            # Verify user exists and password is correct
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials. Please check your login details.'
                }), 401

            # Check password
            if not check_password_hash(user['password'], password):
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials. Please check your login details.'
                }), 401

            # Check account status
            if user.get('status') == 'suspended':
                return jsonify({
                    'success': False,
                    'message': 'Your account has been suspended. Please contact support.'
                }), 403
            
            if user.get('status') == 'pending' and user.get('user_type') == 'doctor':
                return jsonify({
                    'success': False,
                    'message': 'Your doctor account is pending approval. Please wait for admin verification.'
                }), 403

            # Set session variables
            session['user_id'] = user['id']
            session['firstname'] = user['firstname']
            session['lastname'] = user.get('lastname', '')
            session['email'] = user['email']
            session['user_type'] = user['user_type']
            session['logged_in'] = True
            session.permanent = True

            # Update last login timestamp
            cursor.execute("""
                UPDATE users SET last_login = %s WHERE id = %s
            """, (datetime.now(), user['id']))
            conn.commit()

            # Determine redirect URL based on user type
            redirect_map = {
                'admin': '/admin/dashboard',
                'doctor': '/doctor/dashboard',
                'client': '/patient/dashboard'
            }
            
            redirect_url = redirect_map.get(user['user_type'], '/')

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
            'message': 'An error occurred during login. Please try again.'
        }), 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# SIGNUP ROUTE
# ==============================================================================
@login_bp.route('/signup', methods=['POST'])
def signup():
    """Handle user registration"""
    conn = None
    try:
        # Get form data
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        user_type = request.form.get('user_type', 'client')

        # Validate required fields
        if not all([firstname, email, phone, password]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields.'
            }), 400

        # Validate email
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address.'
            }), 400

        # Validate password
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters long.'
            }), 400

        if password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Passwords do not match.'
            }), 400

        # Validate phone
        phone_clean = re.sub(r'\D', '', phone)
        if len(phone_clean) < 10:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid phone number.'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'An account with this email already exists.'
                }), 409

            # Check if phone already exists
            cursor.execute("SELECT id FROM users WHERE phone = %s", (phone_clean,))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'An account with this phone number already exists.'
                }), 409

            # Hash password
            hashed_password = generate_password_hash(password)

            # Determine account status
            status = 'pending' if user_type == 'doctor' else 'active'

            # Insert new user
            cursor.execute("""
                INSERT INTO users (firstname, lastname, email, phone, password, user_type, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (firstname, lastname, email, phone_clean, hashed_password, user_type, status, datetime.now()))
            
            user_id = cursor.lastrowid
            
            # If doctor, also insert into doctors table
            if user_type == 'doctor':
                cursor.execute("""
                    INSERT INTO doctors (user_id, full_name, email, status, created_at)
                    VALUES (%s, %s, %s, 'pending', %s)
                """, (user_id, f"{firstname} {lastname}", email, datetime.now()))
            
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Account created successfully! You can now login.',
                'user_id': user_id
            })

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Signup error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration. Please try again.'
        }), 500
    finally:
        if conn:
            conn.close()

# ==============================================================================
# LOGOUT ROUTE
# ==============================================================================
@login_bp.route('/logout')
def logout():
    """Clear session and logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

# ==============================================================================
# FORGOT PASSWORD ROUTE
# ==============================================================================
@login_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Handle forgot password request"""
    conn = None
    try:
        email = request.form.get('email', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Please provide your email address.'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, firstname FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'No account found with this email address.'
                }), 404

            # Here you would typically:
            # 1. Generate a reset token
            # 2. Save it to database with expiry
            # 3. Send email with reset link
            
            return jsonify({
                'success': True,
                'message': 'Password reset instructions have been sent to your email.'
            })

    except Exception as e:
        print(f"Forgot password error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500
    finally:
        if conn:
            conn.close()
