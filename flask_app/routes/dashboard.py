from flask import Blueprint, render_template, request
from flask_app.utils.ldap_utils import login_required
from flask_app.models.edir_model import EDIRModel
from flask_app.models.ldap_config_manager import LDAPConfigManager

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Récupérer la source LDAP depuis les paramètres de requête
    ldap_source = request.args.get('source', 'meta')
    
    # Créer une instance du modèle LDAP avec la source spécifiée
    ldap_model = EDIRModel(source=ldap_source)
    
    # Récupérer le nom de la directory depuis la configuration
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    # Récupérer les statistiques
    disabled_accounts = ldap_model.get_disabled_accounts_count()
    inactive_users = ldap_model.get_inactive_users_count(months=3)
    expired_password_users = ldap_model.get_expired_password_users_count()
    never_logged_in_users = ldap_model.get_never_logged_in_users_count()
    
    # Passer les statistiques et les informations LDAP au template
    return render_template('dashboard.html', 
                          disabled_accounts=disabled_accounts,
                          inactive_users=inactive_users,
                          expired_password_users=expired_password_users,
                          never_logged_in_users=never_logged_in_users,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)