from flask import Blueprint, render_template
from flask_app.utils.ldap_utils import login_required
from flask_app.models.ldap import LDAPModel

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Créer une instance du modèle LDAP
    ldap_model = LDAPModel()
    
    # Récupérer les statistiques
    disabled_accounts = ldap_model.get_disabled_accounts_count()
    inactive_users = ldap_model.get_inactive_users_count(months=3)
    expired_password_users = ldap_model.get_expired_password_users_count()
    never_logged_in_users = ldap_model.get_never_logged_in_users_count()
    
    # Passer les statistiques au template
    return render_template('dashboard.html', 
                          disabled_accounts=disabled_accounts,
                          inactive_users=inactive_users,
                          expired_password_users=expired_password_users,
                          never_logged_in_users=never_logged_in_users)