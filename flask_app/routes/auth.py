from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_app.models.meta_model import METAModel


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        user_password = request.form['password']
        ldap_model = METAModel()

        # Capture the connection object returned by authenticate
        conn = ldap_model.authenticate(username, user_password)

        if conn:
            
            # Check if the user is a member of the admin group or reader group
            is_admin = False
            is_reader = False
            # Check membership in admin_group_dn
            admin_group_dn = ldap_model.admin_group_dn
            reader_group_dn = ldap_model.reader_group_dn
            conn.search(admin_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_admin = True

            # Check membership in reader_group_dn
            conn.search(reader_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_reader = True
                        
            # Grant access if the user is a member of either group
            if is_admin or is_reader:
                session['logged_in'] = True
                session['username'] = username
                session['role'] = 'admin' if is_admin else 'reader'  # Store role in session
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('You are not authorized to access this application.', 'danger')
        else:
            flash('Invalid username or password!!!!', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))