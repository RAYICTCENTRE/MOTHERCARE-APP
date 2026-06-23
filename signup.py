import pymysql
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

# Create the Blueprint container
signup_bp = Blueprint('signup_bp', __name__)

# Helper function to get database connection
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="mothercare",
        cursorclass=pymysql.cursors.DictCursor
    )

@signup_bp.route('/signup', methods=['POST'])
def signup():
    try:
        conn = get_db_connection()
    except Exception as e:
        return jsonify({"success": False, "message": "Database connection failed"})

    # Get and clean POST data from form inputs
    firstname = request.form.get('firstname', '').strip()
    lastname = request.form.get('lastname', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    user_type = request.form.get('user_type', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Validation
    if not firstname or not lastname or not email or not password or not user_type:
        conn.close()
        return jsonify({"success": False, "message": "All required fields must be filled"})

    if password != confirm_password:
        conn.close()
        return jsonify({"success": False, "message": "Passwords do not match"})

    if len(password) < 6:
        conn.close()
        return jsonify({"success": False, "message": "Password must be at least 6 characters"})

    if user_type not in ['client', 'doctor']:
        conn.close()
        return jsonify({"success": False, "message": "Invalid user type"})

    try:
        with conn.cursor() as cursor:
            # Check if email already exists
            check_sql = "SELECT id FROM users WHERE email = %s"
            cursor.execute(check_sql, (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Email already registered"})

            # Securely hash the password (generates standard pbkdf2 or bcrypt compatible hashes)
            hashed_password = generate_password_hash(password)

            # Assign approval status: Doctors need approval (0), clients auto-approved (1)
            approved = 0 if user_type == 'doctor' else 1

            # Insert new user record into database
            insert_user_sql = """
                INSERT INTO users (firstname, lastname, email, phone, password, user_type, approved, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_user_sql, (firstname, lastname, email, phone, hashed_password, user_type, approved))
            
            # Fetch the generated user ID (equivalent to PHP's $stmt->insert_id)
            user_id = cursor.lastrowid

            # Create an empty profile structure for the newly registered user
            insert_profile_sql = "INSERT INTO user_profiles (user_id) VALUES (%s)"
            cursor.execute(insert_profile_sql, (user_id,))
            
            # Commit the database transaction to apply all changes safely
            conn.commit()

            message = (
                "Account created! Your application is pending admin approval."
                if user_type == 'doctor'
                else "Account created successfully! Please login."
            )

            return jsonify({
                "success": True, 
                "message": message,
                "redirect": "screen2.html"
            })

    except Exception as e:
        # Roll back changes if an operational database crash occurs mid-execution
        conn.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"})

    finally:
        conn.close()
