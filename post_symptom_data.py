import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session
import pymysql

# Create Blueprint
post_symptom_blueprint = Blueprint('post_symptom_blueprint', __name__)

# Optional AI engine
try:
    from predict_ai import run_ai_prediction
    USE_AI = True
except ImportError:
    USE_AI = False


# ======================================================
# DATABASE CONNECTION (PYMYSQL FIXED)
# ======================================================
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


# ======================================================
# ROUTE: POST SYMPTOM DATA
# ======================================================
@post_symptom_blueprint.route('/post-symptom-data', methods=['POST'])
def post_symptom_data():

    user_id = session.get('user_id')

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database connection failed: {str(e)}"
        }), 500

    # --------------------------------------------------
    # Ensure user exists
    # --------------------------------------------------
    if not user_id:
        cursor.execute("SELECT id FROM users LIMIT 1")
        row = cursor.fetchone()

        if row:
            user_id = row['id']
            session['user_id'] = user_id
        else:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "No users found"}), 400

    # --------------------------------------------------
    # Get request data
    # --------------------------------------------------
    data = request.get_json()
    if not data:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": "No data received"}), 400

    mode = data.get('mode', 'home')
    input_type = data.get('input_type', 'checkbox')
    symptoms = data.get('symptoms', '')

    if isinstance(symptoms, list):
        symptoms_arr = symptoms
        symptoms_str = ", ".join(symptoms)
    else:
        symptoms_str = str(symptoms)
        symptoms_arr = [s.strip() for s in symptoms_str.split(',') if s.strip()]

    if not symptoms_str.strip():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": "Please add symptoms"}), 400

    # --------------------------------------------------
    # Medical inputs
    # --------------------------------------------------
    systolic_bp = int(data.get('systolic_bp', 0) or 0)
    diastolic_bp = int(data.get('diastolic_bp', 0) or 0)
    proteinuria = data.get('proteinuria', 'None')
    gestational_age_weeks = float(data.get('gestational_age_weeks', 0) or 0)
    maternal_age_yrs = int(data.get('maternal_age_yrs', 0) or 0)
    diabetes = int(data.get('diabetes', 0) or 0)
    previous_pe = int(data.get('previous_pe', 0) or 0)
    multiple_pregnancy = int(data.get('multiple_pregnancy', 0) or 0)
    hypertension = int(data.get('hypertension', 0) or 0)

    # --------------------------------------------------
    # User profile
    # --------------------------------------------------
    cursor.execute(
        "SELECT last_period, age, nearest_health FROM user_profiles WHERE user_id = %s",
        (user_id,)
    )
    profile = cursor.fetchone() or {}

    if gestational_age_weeks <= 0 and profile.get('last_period'):
        try:
            last_period_date = datetime.strptime(str(profile['last_period']), "%Y-%m-%d")
            delta = datetime.now() - last_period_date
            gestational_age_weeks = float(delta.days // 7)
        except:
            pass

    if maternal_age_yrs <= 0 and profile.get('age'):
        maternal_age_yrs = int(profile['age'])

    facility = profile.get('nearest_health') or "your nearest health facility"

    # --------------------------------------------------
    # AI ENGINE
    # --------------------------------------------------
    risk = None
    level = None
    advice = None
    engine_used = "Python Fallback"

    if USE_AI:
        ai_data = {
            "mode": mode,
            "input_type": input_type,
            "symptoms": symptoms_arr,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
            "proteinuria": proteinuria,
            "gestational_age_weeks": gestational_age_weeks,
            "maternal_age_yrs": maternal_age_yrs,
            "diabetes": diabetes,
            "previous_pe": previous_pe,
            "multiple_pregnancy": multiple_pregnancy,
            "hypertension": hypertension,
            "user_profile": {"nearest_health": facility}
        }

        ai_response = run_ai_prediction(ai_data)

        if ai_response and ai_response.get("success"):
            risk = ai_response.get("risk")
            level = ai_response.get("level")
            advice = ai_response.get("note")
            engine_used = "AI"

    # --------------------------------------------------
    # FALLBACK ENGINE
    # --------------------------------------------------
    if engine_used != "AI":
        risk = 0
        s = symptoms_str.lower()

        if "headache" in s: risk += 15
        if "blurred" in s: risk += 20
        if "swelling" in s: risk += 12
        if "abdominal" in s: risk += 12
        if "nausea" in s: risk += 8

        if systolic_bp >= 160 or diastolic_bp >= 110:
            risk += 30
        elif systolic_bp >= 140 or diastolic_bp >= 90:
            risk += 20
        elif systolic_bp >= 130 or diastolic_bp >= 85:
            risk += 10

        if diabetes: risk += 8
        if previous_pe: risk += 10
        if multiple_pregnancy: risk += 8
        if hypertension: risk += 8
        if maternal_age_yrs >= 35: risk += 8
        if gestational_age_weeks >= 20: risk += 5

        risk = min(risk, 100)

        if risk < 25:
            level = "Low"
            advice = f"LOW RISK\n\nRisk Score: {risk}%\n\nContinue routine care."
        elif risk < 50:
            level = "Moderate"
            advice = f"MODERATE RISK\n\nRisk Score: {risk}%\n\nVisit {facility} if symptoms persist."
        else:
            level = "High"
            advice = f"HIGH RISK\n\nRisk Score: {risk}%\n\nURGENT: Go to {facility}"

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------
    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "risk": risk,
        "level": level,
        "advice": advice,
        "engine_used": engine_used
    })
