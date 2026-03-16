from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

bp = Blueprint('simple', __name__, url_prefix='/simple')

@bp.route('/test-login', methods=['GET', 'POST'])
def test_login():
    if request.method == 'POST':
        nin = request.form.get('nin')
        password = request.form.get('password')
        user = User.query.filter_by(nin=nin).first()
        if user and user.check_password(password):
            login_user(user)
            return f"Login successful! Welcome {user.name}. <a href='/simple/test-dashboard'>Go to dashboard</a>"
        else:
            return "Login failed. Invalid credentials."
    return '''
<!DOCTYPE html>
<html>
<head><title>Test Login</title></head>
<body>
    <h2>Test Login</h2>
    <form method="post">
        <div>
            <label>NIN:</label>
            <input type="text" name="nin" value="00000000001">
        </div>
        <div>
            <label>Password:</label>
            <input type="password" name="password" value="Admin@123">
        </div>
        <button type="submit">Test Login</button>
    </form>
</body>
</html>'''

@bp.route('/test-dashboard')
@login_required
def test_dashboard():
    return f'''
<!DOCTYPE html>
<html>
<head><title>Test Dashboard</title></head>
<body>
    <h2>Test Dashboard</h2>
    <p>Welcome {current_user.name}!</p>
    <p>Role: {current_user.role}</p>
    <p>Category: {current_user.category}</p>
    <p>NIN: {current_user.nin}</p>
    <a href='/simple/test-logout'>Logout</a>
</body>
</html>'''

@bp.route('/test-logout')
@login_required
def test_logout():
    logout_user()
    return "Logged out. <a href='/simple/test-login'>Login again</a>"
