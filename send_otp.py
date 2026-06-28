# send_otp.py
import random
import os
import traceback
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from login import get_db_connection

send_otp_blueprint = Blueprint('send_otp', __name__)

@send_otp_blueprint.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to user's phone or email"""
    conn = None
    try:
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        if not phone and not email:
            return jsonify({
                'success': False,
                'message': 'Phone number or email is required.'
            }), 400

        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Set expiry (10 minutes from now)
        expiry = datetime.now() + timedelta(minutes=10)
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            
            # Store OTP in database
            cursor.execute("""
                INSERT INTO otp_codes (phone, email, otp_code, expires_at, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (phone, email, otp, expiry, datetime.now()))
            
            conn.commit()
            
            # Store OTP in session as backup
            session['otp_code'] = otp
            session['otp_phone'] = phone
            session['otp_email'] = email
            session['otp_expiry'] = expiry.timestamp()
            
            # In production, you would integrate with SMS gateway (Twilio, Africa's Talking, etc.)
            # For now, we'll just return success (in development, you can log the OTP)
            
            print(f"[DEV] OTP for {phone or email}: {otp}")  # Remove in production
            
            return jsonify({
                'success': True,
                'message': 'OTP sent successfully. Please check your phone.',
                'otp': otp if os.environ.get('FLASK_ENV') == 'development' else None  # Only return OTP in dev
            })

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Send OTP error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'Failed to send OTP. Please try again.'
        }), 500
    finally:
        if conn:
            conn.close()
