import os
import time
from flask import Blueprint, session, request, jsonify, current_app
from werkzeug.utils import secure_filename
import mysql.connector

save_doctor_profile_blueprint = Blueprint('save_doctor_profile_blueprint', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@save_doctor_profile_blueprint.route('/save-doctor-profile', methods=['POST'])
def save_doctor_profile():
    # 1. Enforce Authentication Protection Boundaries
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not user_id or user_type != 'doctor':
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    # 2. Extract Data Safely from form payload
    country_code = request.form.get('countryCode', '+256').strip()
    dcontact_raw = request.form.get('dContact', '').strip()
    full_contact = f"{country_code}{dcontact_raw}"
    qualifications = request.form.get('qualifications', '').strip()
    specialty = request.form.get('specialty', '').strip()
    facility = request.form.get('facility', '').strip()

    # 3. Validation Check
    if not dcontact_raw or not qualifications or not specialty or not facility:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    # 4. Optional Photo Upload Pipeline handling
    photo_path = ''
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '' and allowed_file(file.filename):
            clean_filename = secure_filename(file.filename)
            file_extension = clean_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"doctor_{user_id}_{int(time.time())}.{file_extension}"
            
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'doctors')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, mode=0o755)
                
            full_dest_path = os.path.join(upload_dir, unique_filename)
            file.save(full_dest_path)
            photo_path = f"uploads/doctors/{unique_filename}"

    # 5. Database Writing Transaction Block
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if profile already exists
        cursor.execute("SELECT id FROM doctors WHERE user_id = %s", (user_id,))
        profile_exists = cursor.fetchone() is not None

        if profile_exists:
            if photo_path:
                sql = """
                    UPDATE doctors SET 
                        photo_path = %s, country_code = %s, dcontact = %s, 
                        qualifications = %s, specialty = %s, facility = %s, updated_at = NOW()
                    WHERE user_id = %s
                """
                cursor.execute(sql, (photo_path, country_code, full_contact, qualifications, specialty, facility, user_id))
            else:
                sql = """
                    UPDATE doctors SET 
                        country_code = %s, dcontact = %s, 
                        qualifications = %s, specialty = %s, facility = %s, updated_at = NOW()
                    WHERE user_id = %s
                """
                cursor.execute(sql, (country_code, full_contact, qualifications, specialty, facility, user_id))
        else:
            sql = """
                INSERT INTO doctors (user_id, photo_path, country_code, dcontact, qualifications, specialty, facility, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(sql, (user_id, photo_path, country_code, full_contact, qualifications, specialty, facility))

        conn.commit()
        return jsonify({"success": True, "message": "Profile saved successfully"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database interaction failed: {err}"}), 500
    finally:
        cursor.close()
        conn.close()
