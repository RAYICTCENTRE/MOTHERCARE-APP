import os
from flask import Flask, session, redirect, render_template
import mysql.connector

app = Flask(__name__)

# Use environment variables for production security
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-fallback-key')

def get_db_connection():
    # Railway will provide these environment variables once you link your MySQL service
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'mothercare'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@app.route('/dashboard')
def client_dashboard():
    if 'user_id' not in session or session.get('user_type', '').lower() != 'client':
        return redirect('/screen1.html')
        
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
    except mysql.connector.Error as err:
        return f"Database connection failed: {err}", 500

    # User details
    cursor.execute("SELECT firstname, lastname, email, phone FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # Profile details
    cursor.execute("SELECT age, last_period, expected_delivery FROM user_profiles WHERE user_id = %s", (user_id,))
    profile = cursor.fetchone() or {}

    # Symptoms history
    cursor.execute("SELECT * FROM symptoms_records WHERE user_id = %s ORDER BY created_at DESC LIMIT 10", (user_id,))
    symptoms = cursor.fetchall()

    # Statistics
    cursor.execute("SELECT COUNT(*) as count FROM symptoms_records WHERE user_id = %s", (user_id,))
    total_visits = cursor.fetchone()['count']

    # Average risk
    cursor.execute("""
        SELECT AVG(risk) as avg_risk, COUNT(*) as count 
        FROM symptoms_records 
        WHERE user_id = %s AND risk IS NOT NULL
    """, (user_id,))
    risk_avg_data = cursor.fetchone()
    
    avg_risk = f"{risk_avg_data['avg_risk']:.1f}" if risk_avg_data['avg_risk'] is not None else 'no data'
    risk_count = risk_avg_data['count'] if risk_avg_data['count'] else 0

    # Latest risk level
    cursor.execute("SELECT risk_level, created_at, risk FROM symptoms_records WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
    latest = cursor.fetchone() or {}
    latest_risk = latest.get('risk_level', 'no data')
    
    color_map = {'low': '#2e7d32', 'moderate': '#ffc107', 'high': '#fd7e14', 'critical': '#dc3545'}
    latest_risk_color = color_map.get(latest_risk, 'gray')

    edd = profile.get('expected_delivery', 'not set')

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        user=user, profile=profile, symptoms=symptoms, total_visits=total_visits,
        avg_risk=avg_risk, risk_count=risk_count, latest_risk=latest_risk,
        latest_risk_color=latest_risk_color, edd=edd
    )

if __name__ == '__main__':
    # Railway passes a dynamic PORT variable. Bind to 0.0.0.0 so external traffic can reach it.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
