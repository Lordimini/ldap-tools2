from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from flask_app.models.ldap_model import LDAPModel
from flask_login import login_required  # Nouvel import depuis Flask-Login
from flask_app.config.meta_config import meta_login_config
from flask_app.services.login_manager import authenticate_user, current_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user_password = request.form['password']
        
        # Utilisation de la fonction d'authentification de login_manager.py
        user = authenticate_user(username, user_password, ldap_source='meta')
        
        if user:
            # Utiliser la méthode login_user de Flask-Login
            from flask_login import login_user
            login_user(user)
            
            # Garder aussi la méthode session pour la compatibilité
            session['logged_in'] = True
            session['username'] = username
            session['role'] = 'admin' if user.is_admin else 'reader'
            
            # Set the active LDAP source to META by default
            session['ldap_source'] = 'meta'
            session['ldap_name'] = meta_login_config.get('LDAP_name', 'META')
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()  # Déconnecte l'utilisateur avec Flask-Login
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

@auth_bp.route('/user_profile')
@login_required
def user_profile():
    return render_template('user_profile.html', user=current_user)