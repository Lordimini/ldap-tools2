from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_app.models.ldap import LDAPModel
from flask_app.utils.export_utils import util_export_role_users_csv, util_export_role_users_pdf
from flask_app.utils.ldap_utils import login_required

role_bp = Blueprint('role', __name__)

@role_bp.route('/role_users', methods=['GET', 'POST'])
@login_required
def role_users():
    prefill_role_name = request.args.get('role_cn', '')
    if request.method == 'POST' or prefill_role_name:
        # Get the role CN from the form
        role_cn = request.form.get('role_cn', '') or prefill_role_name
        
        # Use the LDAPModel to get role users            
        ldap_model = LDAPModel()
        result = ldap_model.get_role_users(role_cn)
        
        return render_template('role_users.html', result=result, prefill_role_name=prefill_role_name)
        
    return render_template('role_users.html', result=None, prefill_role_name= prefill_role_name)

@role_bp.route('/role_groups', methods=['GET', 'POST'])
@login_required
def role_groups():
    prefill_role_name = request.args.get('role_cn', '')
    if request.method == 'POST' or prefill_role_name:
        # Get the role CN from the form
        role_cn = request.form.get('role_cn', '') or prefill_role_name
        
        # Use the LDAPModel to get role groups or resources
        ldap_model = LDAPModel()
        result = ldap_model.get_role_groups(role_cn)
    
        return render_template('role_groups.html', result=result, prefill_role_cn=role_cn)
    return render_template('role_groups.html', result=None, prefill_role_cn='')


@role_bp.route('/export_role_users_csv/<role_cn>')
@login_required
def export_role_users_csv(role_cn):
    ldap_model = LDAPModel()
    result = ldap_model.get_role_users(role_cn)
    if result and result['users']:
        return util_export_role_users_csv(role_cn, result['users'])
    return redirect(url_for('role.role_users'))

@role_bp.route('/export_role_users_pdf/<role_cn>')
@login_required
def export_role_users_pdf(role_cn):
    ldap_model = LDAPModel()
    result = ldap_model.get_role_users(role_cn)
    if result and result['users']:
        return util_export_role_users_pdf(role_cn, result['users'])
    return redirect(url_for('role.role_users'))

@role_bp.route('/view_role/<path:dn>')
@login_required
def view_role(dn):
    try:
        ldap_model = LDAPModel()
        data = ldap_model.view_role(dn)
        if not data:
            flash('Role not found.', 'danger')
            return redirect(url_for('ldap.ldap_browser'))
        return render_template('view_role.html', **data)
    except Exception as e:
        print(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('ldap.ldap_browser'))

  