from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_app.models.edir_model import EDIRModel
from flask_app.utils.export_utils import util_export_service_users_csv
from flask_login import login_required  # Nouvel import depuis Flask-Login
from flask_app.models.ldap_config_manager import LDAPConfigManager

service_bp = Blueprint('service', __name__)

@service_bp.route('/service_users', methods=['GET', 'POST'])
@login_required
def service_users():
    # Get LDAP source with proper fallback sequence
    ldap_source = request.args.get('source')
    if request.method == 'POST':
        ldap_source = request.form.get('ldap_source', ldap_source)
    
    # If not in query or form params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    prefill_service_name = request.args.get('service_name', '')
    
    if request.method == 'POST' or prefill_service_name:
        # Get the service CN from the form
        service_name = request.form.get('service_name', '') or prefill_service_name        
        ldap_model = EDIRModel(source=ldap_source)
        result = ldap_model.get_service_users(service_name)
        return render_template('service_users.html', 
                              result=result, 
                              prefill_service_name=prefill_service_name,
                              ldap_source=ldap_source,
                              ldap_name=ldap_name)
    
    return render_template('service_users.html', 
                          result=None, 
                          prefill_service_name=prefill_service_name,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)

@service_bp.route('/export_service_users_csv/<service_name>')
@login_required
def export_service_users_csv(service_name):
    # Get LDAP source with proper fallback sequence
    ldap_source = request.args.get('source')
    
    # If not in query params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    ldap_model = EDIRModel(source=ldap_source)
    result = ldap_model.get_service_users(service_name)
    if result and result['users']:
        return util_export_service_users_csv(service_name, result['users'])
    return redirect(url_for('service.service_users', source=ldap_source))