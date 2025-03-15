from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from flask_app.models.edir_model import EDIRModel
from flask_app.utils.ldap_utils import login_required
from flask_app.config.meta_config import meta_login_config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user_password = request.form['password']
        
        # Always use META for authentication
        ldap_model = EDIRModel(source='meta')

        # Construct the full user DN
        user_dn = f'cn={username},{ldap_model.actif_users_dn}'
        
        # Capture the connection object returned by authenticate
        conn = ldap_model.authenticate(username, user_password)

        if conn:
            # Check if the user is a member of the admin group or reader group
            is_admin = False
            is_reader = False
            
            # Check membership in admin_group_dn
            admin_group_dn = ldap_model.admin_group_dn
            reader_group_dn = ldap_model.reader_group_dn
            
            # Check if user is in admin group
            conn.search(admin_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_admin = True

            # If not admin, check if user is in reader group
            if not is_admin:
                conn.search(reader_group_dn, f'(member={conn.user})', search_scope='BASE')
                if conn.entries:
                    is_reader = True
                    
            # Grant access if the user is a member of either group
            if is_admin or is_reader:
                session['logged_in'] = True
                session['username'] = username
                session['role'] = 'admin' if is_admin else 'reader'  # Store role in session
                
                # Set the active LDAP source to META by default
                session['ldap_source'] = 'meta'
                session['ldap_name'] = meta_login_config.get('LDAP_name', 'META')
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('You are not authorized to access this application.', 'danger')
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/set_ldap_source', methods=['POST'])
@login_required
def set_ldap_source():
    data = request.get_json()
    if data and 'source' in data:
        source_name = data['source']
        
        # Validate that the source exists
        if source_name in current_app.ldap_config_manager.get_available_configs():
            # Set the active config in the manager
            current_app.ldap_config_manager.set_active_config(source_name)
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Invalid source'}), 400
    
    return jsonify({'success': False, 'error': 'Missing source parameter'}), 400