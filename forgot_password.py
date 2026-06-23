from flask import Flask, redirect, url_for
from routes.login import login_bp
from routes.signup import signup_bp
from routes.forgot_password import forgot_password_bp  # Import the upcoming blueprint

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_change_this_later'

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(signup_bp)
app.register_blueprint(forgot_password_bp)  # Register the upcoming blueprint

@app.route('/')
def index():
    return redirect(url_for('static', filename='screen1.html'))

if __name__ == '__main__':
    app.run(debug=True)
