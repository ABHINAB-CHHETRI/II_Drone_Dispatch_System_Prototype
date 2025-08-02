import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'defaultsecretkey')  # Change for production!

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple user store — replace this with a real DB for production
USERS = {
    'admin': {'password': 'adminpass', 'role': 'admin'},
    'user': {'password': 'userpass', 'role': 'user'}
}

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    user_info = USERS.get(user_id)
    if user_info:
        return User(user_id, user_info['role'])
    return None

# 6 Medical Boxes
MEDICAL_BOXES = [
    "Emergency Food",
    "A+ Blood",
    "Surgical Kit",
    "Specialized Vaccine",
    "PPE Kit",
    "First Aid Kit"
]

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_info = USERS.get(username)
        if user_info and user_info['password'] == password:
            user = User(username, user_info['role'])
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('index'))
    return render_template('admin_dashboard.html', boxes=MEDICAL_BOXES)

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    if current_user.role != 'user':
        flash("Access denied: Users only.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        selected_box = request.form.get('box')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            if selected_box not in MEDICAL_BOXES:
                flash("Invalid box selected.", "danger")
                return redirect(url_for('user_dashboard'))
            else:
                coord = {'lat': lat_float, 'lon': lon_float, 'box': selected_box}
                # In a real app, save this to DB or session to accumulate multiple coords/deliveries
                return render_template(
                    'map_view.html',
                    coords=[coord],
                    box=selected_box,
                    mapbox_token=os.environ.get('MAPBOX_ACCESS_TOKEN')  # Pass token securely from env
                )
        except (ValueError, TypeError):
            flash("Please enter valid latitude and longitude.", "danger")

    return render_template('dashboard.html', boxes=MEDICAL_BOXES)

# Optional: add error handlers, etc.

if __name__ == '__main__':
    # For local debug only; in Render use gunicorn
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
