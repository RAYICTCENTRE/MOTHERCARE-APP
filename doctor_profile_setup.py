import os
import time
from flask import Blueprint, session, request, jsonify, redirect, current_app
from werkzeug.utils import secure_filename
import mysql.connector

doc_profile_setup_blueprint = Blueprint('doc_profile_setup_blueprint', __name__)

# Define permissible upload structures matching standard browser graphics
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

@doc_profile_setup_blueprint.route('/submit-doctor-profile-setup', methods=['POST'])
def submit_doctor_profile_setup():
    # 1. Enforce Authentication Protection Boundaries
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not user_id or user_type != 'doctor':
        return jsonify({"success": False, "message": "Unauthorized session context"}), 401

    # 2. Extract Data Safely from standard Form enc-types
    qualifications = request.form.get('qualifications', '').strip()
    specialty = request.form.get('specialty', '').strip()
    facility = request.form.get('facility', '').strip()
    country_code = request.form.get('countryCode', '').strip()
    d_contact_raw = request.form.get('dContact', '').strip()
    dcontact = f"{country_code}{d_contact_raw}"

    # 3. Input validation validation checks
    if not qualifications or not specialty or not facility or not d_contact_raw:
        return jsonify({"success": False, "message": "Please fill in all required fields."}), 400

    # 4. Secure Async File Upload Processing Pipeline
    photo_path = ''
    if 'photo' not in request.files:
        return jsonify({"success": False, "message": "Please upload a valid profile photo."}), 400
        
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file stream selected."}), 400

    if file and allowed_file(file.filename):
        # Prevent injection using Werkzeug naming validation structures
        clean_filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{clean_filename}"
        
        # Configure a permanent location directory target inside your application workspace
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, mode=0o755)
            
        full_dest_path = os.path.join(upload_dir, unique_filename)
        file.save(full_dest_path)
        
        # Store relative file path reference inside SQL text cells for easier delivery
        photo_path = f"uploads/{unique_filename}"
    else:
        return jsonify({"success": False, "message": "Invalid file format extension profile type."}), 400

    # 5. Database Writing Transaction Block
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Parameterized query automatically escapes fields securely
        sql = """
            INSERT INTO doctors (user_id, photo_path, qualifications, specialty, facility, dcontact)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                photo_path = VALUES(photo_path),
                qualifications = VALUES(qualifications),
                specialty = VALUES(specialty),
                facility = VALUES(facility),
                dcontact = VALUES(dcontact)
        """
        cursor.execute(sql, (user_id, photo_path, qualifications, specialty, facility, dcontact))
        conn.commit()
        
        return jsonify({"success": True, "message": "Doctor profile setup completed successfully!"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database transaction broke: {err}"}), 500
    finally:
        cursor.close()
        conn.close()
