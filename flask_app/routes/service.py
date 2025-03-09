from flask import Blueprint, render_template, request, redirect, url_for
from flask_app.models.meta_model import METAModel
from flask_app.utils.export_utils import util_export_service_users_csv
from flask_app.utils.ldap_utils import login_required

service_bp = Blueprint('service', __name__)

@service_bp.route('/service_users', methods=['GET', 'POST'])
@login_required
def service_users():
    
    prefill_service_name = request.args.get('service_name', '')
    
    if request.method == 'POST' or prefill_service_name:
        # Get the service CN from the form
        service_name = request.form.get('service_name', '') or prefill_service_name        
        ldap_model = METAModel()
        result = ldap_model.get_service_users(service_name)
        return render_template('service_users.html', result=result, prefill_service_name=prefill_service_name)
    return render_template('service_users.html', result=None, prefill_service_name=prefill_service_name)

@service_bp.route('/export_service_users_csv/<service_name>')
@login_required
def export_service_users_csv(service_name):
    ldap_model = METAModel()
    result = ldap_model.get_service_users(service_name)
    if result and result['users']:
        return util_export_service_users_csv(service_name, result['users'])
    return redirect(url_for('service.service_users'))
