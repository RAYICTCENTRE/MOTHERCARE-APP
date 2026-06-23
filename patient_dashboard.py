import os
import json
from datetime import datetime
from flask import Blueprint, render_template, session, redirect
import mysql.connector

patient_dashboard_blueprint = Blueprint('patient_dashboard_blueprint', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@patient_dashboard_blueprint.route('/patient-dashboard', methods=['GET'])
def patient_dashboard():
    # 1. Enforce Authentication Protection Boundaries
    user_id = session.get('user_id')
    user_type = str(session.get('user_type', '')).strip().lower()
    
    if not user_id or user_type != 'client':
        return redirect('/static/screen1.html')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Fetch User Profile Basics
        cursor.execute("SELECT id, firstname, lastname, email, phone FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone() or {}

        # 3. Fetch Comprehensive Maternity Metrics Info
        cursor.execute("""
            SELECT age, nationality, district, sub_county, parish, village, nearest_health, 
                   kin_name, kin_relationship, kin_contact, last_period, expected_delivery, created_at 
            FROM user_profiles 
            WHERE user_id = %s
        """, (user_id,))
        profile = cursor.fetchone() or {}

        # 4. Fetch Historical Telemedicine Record History Logs
        cursor.execute("""
            SELECT id, input_type, symptoms, blood_pressure, systolic_bp, diastolic_bp, 
                   proteinuria, risk, risk_level, message, created_at 
            FROM symptoms_records 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        records = cursor.fetchall()

    except mysql.connector.Error as err:
        return f"Database data aggregation broke: {err}", 500
    finally:
        cursor.close()
        conn.close()

    # 5. Process Analytical Statistical Variables Natively in Python
    total_visits = len(records)
    latest_risk = records[0]['risk_level'] if total_visits > 0 else 'No Data'
    
    avg_risk = 0
    risk_counts = {'Low': 0, 'Moderate': 0, 'High': 0, 'Critical': 0}
    risk_map = {'Low': 1, 'Moderate': 2, 'High': 3, 'Critical': 4}

    for record in records:
        # Standardize date types to simple strings for clean UI processing loop arrays
        if isinstance(record.get('created_at'), datetime):
            record['created_at'] = record['created_at'].strftime("%Y-%m-%d %H:%M:%S")

        r_level = str(record['risk_level']).capitalize()
        if r_level in risk_counts:
            risk_counts[r_level] += 1
        
        avg_risk += risk_map.get(r_level, 0)

    avg_risk = round(avg_risk / total_visits, 1) if total_visits > 0 else 0

    # 6. Parse chart coordinates array pipelines into clean JSON payloads
    risk_labels = list(risk_counts.keys())
    risk_values = list(risk_counts.values())

    trend_labels = []
    trend_risks = []
    
    # Reversing historical entries directly using Python slicing blocks to display a left-to-right temporal flow
    for record in reversed(records):
        try:
            dt_obj = datetime.strptime(record['created_at'], "%Y-%m-%d %H:%M:%S")
            trend_labels.append(dt_obj.strftime('%b %d'))
        except (ValueError, TypeError):
            trend_labels.append('Unknown')
            
        r_level = str(record['risk_level']).capitalize()
        trend_risks.append(risk_map.get(r_level, 0))

    return render_template(
        'patient_dashboard.html',
        user=user,
        profile=profile,
        records=records,
        total_visits=total_visits,
        latest_risk=latest_risk,
        avg_risk=avg_risk,
        risk_labels=json.dumps(risk_labels),
        risk_values=json.dumps(risk_values),
        trend_labels=json.dumps(trend_labels),
        trend_risks=json.dumps(trend_risks)
    )
