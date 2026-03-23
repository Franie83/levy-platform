from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, AuditLog
from datetime import datetime
import json

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        # Check if user is suspended
        if current_user.status == 'suspended':
            logout_user()
            flash('Your account has been suspended. Please contact support.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Redirect based on role
        if current_user.role == 'super_admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'enforcer':
            return redirect(url_for('enforcement.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        nin = request.form.get('nin', '').strip()
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Validate input
        if not nin or not password:
            flash('Please enter both NIN and password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Find user by NIN
        user = User.query.filter_by(nin=nin).first()
        
        if not user:
            flash('Invalid NIN or password', 'danger')
            # Log failed login attempt (no user found)
            try:
                audit_log = AuditLog(
                    user_id=None,
                    action='LOGIN_FAILED',
                    resource_type='user',
                    resource_id='unknown',
                    ip_address=request.remote_addr,
                    details=json.dumps({'reason': 'User not found', 'nin': nin[:4] + '***'})
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                print(f"Error logging audit: {e}")
                db.session.rollback()
            
            return redirect(url_for('auth.login'))
        
        # Check if user is suspended
        if user.status == 'suspended':
            flash('Your account has been suspended. Please contact the administrator for assistance.', 'danger')
            
            # Log the suspended login attempt
            try:
                audit_log = AuditLog(
                    user_id=user.id,
                    action='SUSPENDED_LOGIN_ATTEMPT',
                    resource_type='user',
                    resource_id=str(user.id),
                    ip_address=request.remote_addr,
                    details=json.dumps({
                        'attempt_time': datetime.utcnow().isoformat(),
                        'reason': 'Account suspended',
                        'suspended_at': user.suspended_at.isoformat() if hasattr(user, 'suspended_at') and user.suspended_at else None
                    })
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                print(f"Error logging audit: {e}")
                db.session.rollback()
            
            return redirect(url_for('auth.login'))
        
        # Check password
        if user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            
            try:
                db.session.commit()
            except Exception as e:
                print(f"Error updating last login: {e}")
                db.session.rollback()
            
            # Log successful login
            try:
                audit_log = AuditLog(
                    user_id=user.id,
                    action='LOGIN_SUCCESS',
                    resource_type='user',
                    resource_id=str(user.id),
                    ip_address=request.remote_addr,
                    details=json.dumps({'role': user.role})
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                print(f"Error logging audit: {e}")
                db.session.rollback()
            
            # Redirect based on role
            if user.role == 'super_admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'enforcer':
                return redirect(url_for('enforcement.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid NIN or password', 'danger')
            
            # Log failed login attempt (wrong password)
            try:
                audit_log = AuditLog(
                    user_id=user.id,
                    action='LOGIN_FAILED',
                    resource_type='user',
                    resource_id=str(user.id),
                    ip_address=request.remote_addr,
                    details=json.dumps({'reason': 'Invalid password'})
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                print(f"Error logging audit: {e}")
                db.session.rollback()
            
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    user_id = current_user.id
    user_name = current_user.name
    
    # Log logout
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action='LOGOUT',
            resource_type='user',
            resource_id=str(user_id),
            ip_address=request.remote_addr,
            details=json.dumps({'user_name': user_name})
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")
        db.session.rollback()
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/account-status')
@login_required
def account_status():
    """Check account status"""
    if current_user.status == 'suspended':
        return render_template('auth/suspended.html', 
                             reason=getattr(current_user, 'suspension_reason', None),
                             suspended_at=getattr(current_user, 'suspended_at', None))
    
    return redirect(url_for('main.dashboard'))

@bp.route('/api/check-status')
def api_check_status():
    """API endpoint to check if user is suspended"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'status': current_user.status,
            'suspended': current_user.status == 'suspended',
            'suspended_at': current_user.suspended_at.isoformat() if hasattr(current_user, 'suspended_at') and current_user.suspended_at else None,
            'user_id': current_user.id,
            'name': current_user.name
        })
    else:
        return jsonify({
            'authenticated': False,
            'status': 'not_authenticated'
        })