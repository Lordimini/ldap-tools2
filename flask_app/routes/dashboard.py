from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required  # Nouvel import depuis Flask-Login
from flask_app.models.ldap_model import LDAPModel
from flask_app.models.ldap_config_manager import LDAPConfigManager

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard route displaying statistics from LDAP.
    Properly handles LDAP source from different input methods.
    """
    # Step 1: Get LDAP source with proper fallback sequence
    ldap_source = request.args.get('source')
    
    # If not in query params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Step 2: Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Step 3: Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    # Step 4: Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    # Récupérer les statistiques
    stats = ldap_model.get_dashboard_stats()
    
    disabled_accounts = stats.get('disabled_accounts', 0)
    inactive_users = ldap_model.get_inactive_users_count(months=3)
    expired_password_users = ldap_model.get_expired_password_users_count()
    never_logged_in_users = ldap_model.get_never_logged_in_users_count()
    
    # Step 5: Always include ldap_source in template context
    return render_template('dashboard.html', 
                          disabled_accounts=disabled_accounts,
                          inactive_users=inactive_users,
                          expired_password_users=expired_password_users,
                          never_logged_in_users=never_logged_in_users,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)