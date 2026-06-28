# verify_otp.py
import traceback
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from login import get_db_connection

verify_otp_blueprint = Blueprint('verify_otp', __name__)

@verify_otp_blueprint.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP code"""
    conn = None
    try:
        otp_code = request.form.get('otp', '').strip()
        phone = request.form.get('phone', session.get('otp_phone', ''))
        email = request.form.get('email', session.get('otp_email', ''))

        if not otp_code:
            return jsonify({
                'success': False,
                'message': 'Please enter the OTP code.'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            
            # Check OTP in database
            cursor.execute("""
                SELECT otp_code, expires_at 
                FROM otp_codes 
                WHERE (phone = %s OR email = %s) 
                AND is_used = FALSE
                ORDER BY created_at DESC 
                LIMIT 1
            """, (phone, email))
            
            otp_record = cursor.fetchone()
            
            if not otp_record:
                # Check session as fallback
                session_otp = session.get('otp_code')
                session_expiry = session.get('otp_expiry')
                
                if session_otp and session_otp == otp_code:
                    if session_expiry and datetime.now().timestamp() < session_expiry:
                        # Valid OTP from session
                        session.pop('otp_code', None)
                        session.pop('otp_phone', None)
                        session.pop('otp_email', None)
                        session.pop('otp_expiry', None)
                        
                        return jsonify({
                            'success': True,
                            'message': 'OTP verified successfully!'
                        })
                
                return jsonify({
                    'success': False,
                    'message': 'Invalid or expired OTP. Please request a new one.'
                }), 400

            # Check if OTP has expired
            if otp_record['expires_at'] < datetime.now():
                return jsonify({
                    'success': False,
                    'message': 'OTP has expired. Please request a new one.'
                }), 400

            # Verify OTP
            if otp_record['otp_code'] != otp_code:
                return jsonify({
                    'success': False,
                    'message': 'Invalid OTP. Please try again.'
                }), 400

            # Mark OTP as used
            cursor.execute("""
                UPDATE otp_codes 
                SET is_used = TRUE, verified_at = %s 
                WHERE otp_code = %s AND (phone = %s OR email = %s)
            """, (datetime.now(), otp_code, phone, email))
            
            conn.commit()
            
            # Clear session OTP
            session.pop('otp_code', None)
            session.pop('otp_phone', None)
            session.pop('otp_email', None)
            session.pop('otp_expiry', None)
            
            # Set phone verified in session
            session['phone_verified'] = True
            
            return jsonify({
                'success': True,
                'message': 'Phone number verified successfully!'
            })

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Verify OTP error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'OTP verification failed. Please try again.'
        }), 500
    finally:
        if conn:
            conn.close()
