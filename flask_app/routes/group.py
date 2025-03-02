from flask import Blueprint, render_template, request, redirect, url_for
from flask_app.models.ldap import LDAPModel
from flask_app.utils.export_utils import util_export_group_users_csv
from flask_app.utils.ldap_utils import login_required

group_bp = Blueprint('group', __name__)

@group_bp.route('/group_users', methods=['GET', 'POST'])
@login_required
def group_users():
    prefill_group_name = request.args.get('group_name', '')
    if request.method == 'POST' or prefill_group_name:
        # Use the group_name from the form or the query parameter
        group_name = request.form.get('group_name', '') or prefill_group_name
        
        # Use the LDAPModel to get group users
        ldap_model = LDAPModel()
        result = ldap_model.get_group_users(group_name)
        
        return render_template('group_users.html', result=result, prefill_group_name=prefill_group_name)
    return render_template('group_users.html', result=None, prefill_group_name=prefill_group_name)

@group_bp.route('/export_group_users_csv/<group_name>')
@login_required
def export_group_users_csv(group_name):
    ldap_model = LDAPModel()
    result = ldap_model.get_group_users(group_name)
    if result and result['users']:
        return util_export_group_users_csv(group_name, result['users'])
    return redirect(url_for('group.group_users'))