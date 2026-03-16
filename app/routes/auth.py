from flask import Blueprint, render_template, redirect, url_for, flash, request 
from flask_login import login_user, logout_user, login_required, current_user 
from app import db 
from app.models import User 
 
bp = Blueprint('auth', __name__, url_prefix='/auth') 
 
@bp.route('/register', methods=['GET', 'POST']) 
def register(): 
    if request.method == 'POST': 
        name = request.form.get('name') 
        email = request.form.get('email') 
        phone = request.form.get('phone') 
        nin = request.form.get('nin') 
        password = request.form.get('password') 
        confirm_password = request.form.get('confirm_password') 
        role = request.form.get('role') 
        category = request.form.get('category') if role == 'payee' else None 
 
        print(f"Registration - Name: {name}, Role: {role}, Category: {category}") 
 
        if password != confirm_password: 
            flash('Passwords do not match', 'danger') 
            return redirect(url_for('auth.register')) 
 
        if User.query.filter_by(nin=nin).first(): 
            flash('NIN already registered', 'danger') 
            return redirect(url_for('auth.register')) 
 
        if User.query.filter_by(email=email).first(): 
            flash('Email already registered', 'danger') 
            return redirect(url_for('auth.register')) 
 
        user = User( 
            name=name, 
            email=email, 
            phone=phone, 
            nin=nin, 
            role=role, 
            category=category, 
            status='active' 
        ) 
        user.set_password(password) 
 
        db.session.add(user) 
        db.session.commit() 
        print(f"User created: {name} with category: {category}") 
 
        flash('Registration successful! Please login.', 'success') 
        return redirect(url_for('auth.login')) 
 
    return render_template('auth/register.html') 
 
@bp.route('/login', methods=['GET', 'POST']) 
def login(): 
    if request.method == 'POST': 
        nin = request.form.get('nin') 
        password = request.form.get('password') 
        remember = True if request.form.get('remember') else False 
 
        user = User.query.filter_by(nin=nin).first() 
 
        if not user or not user.check_password(password): 
            flash('Invalid NIN or password', 'danger') 
            return redirect(url_for('auth.login')) 
 
        if user.status != 'active': 
            flash('Your account is suspended. Contact admin.', 'danger') 
            return redirect(url_for('auth.login')) 
 
        login_user(user, remember=remember) 
 
        return redirect(url_for('main.dashboard')) 
 
    return render_template('auth/login.html') 
 
@bp.route('/logout') 
@login_required 
def logout(): 
    logout_user() 
    flash('You have been logged out.', 'info') 
    return redirect(url_for('auth.login')) 
