# app.py
from flask import Flask, redirect, url_for
import os

# Import all blueprints
from post_symptom_data import post_symptom_blueprint
from consult_doctor import consult_blueprint
from chat_patient import chat_blueprint  # New chat module import

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-fallback-secure-string-12345')

# Register your routing structures
app.register_blueprint(post_symptom_blueprint)
app.register_blueprint(consult_blueprint)
app.register_blueprint(chat_blueprint)      # New blueprint tracking register

@app.route('/')
def index():
    return redirect(url_for('static', filename='screen1.html'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
