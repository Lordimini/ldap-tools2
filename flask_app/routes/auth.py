from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app, g
from flask_login import login_user, logout_user, login_required, current_user
from flask_app.services.login_manager import authenticate_user
from flask_app.models.user_model import User
from flask_app.models.ldap_config_manager import LDAPConfigManager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login with LDAP authentication and role assignment
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
        
    error = None
    ldap_source = request.args.get('source', session.get('ldap_source', 'meta'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ldap_source = request.form.get('ldap_source', ldap_source)
        
        if not username or not password:
            flash('Please enter both username and password', 'warning')
            return render_template('login.html', ldap_source=ldap_source)
        
        # Authenticate user against LDAP
        user = authenticate_user(username, password, ldap_source)
        
        if user:
            # Check if user has admin or reader role
            if user.has_any_role(['admin', 'reader']):
                # Create session for user and log them in
                login_user(user)
                
                # Store LDAP source in session
                session['ldap_source'] = ldap_source
                
                # Get LDAP name for display
                config = LDAPConfigManager.get_config(ldap_source)
                session['ldap_name'] = config.get('LDAP_name', 'LDAP')
                
                # Flash success message
                flash(f'Welcome {user.name}! You are now logged in.', 'success')
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.dashboard'))
            else:
                flash('You do not have permission to access this application.', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    # For GET requests or failed authentication, render login page
    return render_template('login.html', 
                          ldap_source=ldap_source,
                          available_sources=LDAPConfigManager.get_available_configs())

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Handle user logout and session cleanup
    """
    user_name = current_user.name
    logout_user()
    session.clear()
    flash(f'Goodbye {user_name}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/set_ldap_source', methods=['POST'])
@login_required
def set_ldap_source():
    """
    Set the LDAP source for the current session
    """
    data = request.get_json()
    if data and 'source' in data:
        source_name = data['source']
        
        # Validate that the source exists
        if source_name in current_app.ldap_config_manager.get_available_configs():
            # Set the active config in the manager
            current_app.ldap_config_manager.set_active_config(source_name)
            
            # Update session
            session['ldap_source'] = source_name
            
            # Get LDAP name for display
            config = LDAPConfigManager.get_config(source_name)
            session['ldap_name'] = config.get('LDAP_name', 'LDAP')
            
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Invalid source'}), 400
    
    return jsonify({'success': False, 'error': 'Missing source parameter'}), 400

@auth_bp.route('/user_profile')
@login_required
def user_profile():
    """
    Display the current user's profile and information
    """
    return render_template('user_profile.html', 
                          user=current_user,
                          ldap_source=session.get('ldap_source', 'meta'))

@auth_bp.route('/access_denied')
def access_denied():
    """
    Display access denied page for unauthorized access attempts
    """
    return render_template('access_denied.html')