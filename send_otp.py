import os
import re
import smtplib
from email.mime.text import MIMEText
from flask import Blueprint, session, request, jsonify

send_otp_blueprint = Blueprint('send_otp_blueprint', __name__)

def send_sms_via_carrier(phone, message_text):
    # 1. Clean phone number (Keep only numeric digits)
    phone_clean = re.sub(r'[^0-9]', '', str(phone))
    
    if not phone_clean:
        return False
        
    # 2. Detect carrier based on suffix (Simplified for Uganda)
    # Extracts the 3 digits right before the final 6 numbers
    prefix = phone_clean[-9:-6]
    
    carrier = 'mtn' # Default fallback state
    if prefix in ['77', '78', '76', '70', '71']:  # Added common MTN prefixes
        carrier = 'mtn'
    elif prefix in ['75', '74', '70']: # Added common Airtel prefixes
        carrier = 'airtel'
        
    gateways = {
        'mtn': '@sms.mtn.co.ug',
        'airtel': '@sms.airtel.co.ug'
    }
    
    # 3. Construct the unique SMS-to-Email address
    gateway_domain = gateways.get(carrier, '@sms.mtn.co.ug')
    to_email = f"{phone_clean}{gateway_domain}"
    
    # 4. Compile MIME Structural Headers
    msg = MIMEText(message_text)
    msg['Subject'] = "MotherCare OTP"
    msg['From'] = os.environ.get('SMTP_FROM', 'noreply@mothercare.com')
    msg['To'] = to_email
    
    # 5. Connect and stream transmission via SMTP network servers
    try:
        # Pull mail provider environment secrets assigned on Railway
        smtp_host = os.environ.get('SMTP_HOST', 'localhost')
        smtp_port = int(os.environ.get('SMTP_PORT', 25))
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_pass = os.environ.get('SMTP_PASSWORD', '')
        
        # Use secure connections if explicit credentials exist, fallback locally for testing
        if smtp_user and smtp_pass:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port) if smtp_port == 465 else smtplib.SMTP(smtp_host, smtp_port)
            if smtp_port != 465:
                server.starttls()
            server.login(smtp_user, smtp_pass)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            
        server.sendmail(msg['From'], [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP SMS Relay Delivery failure exception: {e}")
        return False

@send_otp_blueprint.route('/send-otp-action', methods=['POST'])
def send_otp_action():
    # Example processing controller to capture your incoming OTP requests
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form

    method = data.get('method', '').strip().lower()
    otp = data.get('otp', '123456') # Generated dynamically elsewhere in your auth pipeline
    
    # Mock user dictionary matching your data fetch patterns
    user_phone = data.get('phone', '') 
    
    if method == 'sms':
        success = send_sms_via_carrier(user_phone, f"Your MotherCare OTP is: {otp}")
        if success:
            return jsonify({"success": True, "message": "OTP sent to your phone"})
        else:
            return jsonify({"success": False, "message": "Failed to send SMS. Please try email instead."}), 500
            
    return jsonify({"success": False, "message": "Invalid delivery method selected"}), 400
