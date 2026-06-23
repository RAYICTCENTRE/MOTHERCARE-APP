from flask import request, redirect, session

@app.route('/update-profile', methods=['POST'])
def update_profile():
    # 1. Redirect if not logged in
    if 'user_id' not in session:
        return redirect('/screen2.html')
        
    user_id = session['user_id']

    # ========== GET FORM DATA (POST) ==========
    # Phone number
    phone_country_code = request.form.get('phoneCountryCode', '+256')
    phone_number = request.form.get('phone', '')
    full_phone = f"{phone_country_code}{phone_number}" if phone_number else ""

    # Profile data
    age_raw = request.form.get('age', '')
    age = int(age_raw) if age_raw.isdigit() else None
    
    nationality = request.form.get('nationality', '')
    district = request.form.get('district', '')
    sub_county = request.form.get('subCounty', '')
    parish = request.form.get('parish', '')
    village = request.form.get('village', '')
    nearest_health = request.form.get('nearestHealth', '')
    kin_name = request.form.get('kinName', '')
    kin_relationship = request.form.get('kinRelationship', '')
    kin_country_code = request.form.get('kinCountryCode', '+256')
    kin_contact = request.form.get('kinContact', '')
    full_kin_contact = f"{kin_country_code}{kin_contact}" if kin_contact else ""
    
    # Handle empty date strings safely as None (SQL NULL)
    last_period = request.form.get('lastPeriod') or None
    expected_delivery = request.form.get('expectedDelivery') or None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ========== 1. UPDATE USERS TABLE (PHONE NUMBER) ==========
        if phone_number:
            cursor.execute("UPDATE users SET phone = %s WHERE id = %s", (full_phone, user_id))

        # ========== 2. CHECK IF PROFILE EXISTS IN USER_PROFILES ==========
        cursor.execute("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
        profile_exists = cursor.fetchone() is not None

        # ========== 3. SAVE/UPDATE USER_PROFILES TABLE ==========
        if profile_exists:
            # UPDATE existing profile
            update_query = """
                UPDATE user_profiles SET 
                    age = %s, nationality = %s, district = %s, sub_county = %s, 
                    parish = %s, village = %s, nearest_health = %s, kin_name = %s, 
                    kin_relationship = %s, kin_contact = %s, kin_country_code = %s,
                    last_period = %s, expected_delivery = %s, updated_at = NOW()
                WHERE user_id = %s
            """
            cursor.execute(update_query, (
                age, nationality, district, sub_county, parish, village, 
                nearest_health, kin_name, kin_relationship, full_kin_contact, 
                kin_country_code, last_period, expected_delivery, user_id
            ))
        else:
            # INSERT new profile
            insert_query = """
                INSERT INTO user_profiles (
                    user_id, age, nationality, district, sub_county, parish, 
                    village, nearest_health, kin_name, kin_relationship, 
                    kin_contact, kin_country_code, last_period, expected_delivery
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_id, age, nationality, district, sub_county, parish, 
                village, nearest_health, kin_name, kin_relationship, 
                full_kin_contact, kin_country_code, last_period, expected_delivery
            ))

        # Explicitly commit changes for write transactions
        conn.commit()
        
    except mysql.connector.Error as err:
        return f"Database process failed: {err}", 500
    finally:
        cursor.close()
        conn.close()

    # ========== 4. REDIRECT BACK TO PROFILE PAGE ==========
    return redirect('/screen4.html')
