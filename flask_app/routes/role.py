from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_app.models.meta_model import METAModel
from flask_app.utils.export_utils import util_export_role_users_csv, util_export_role_users_pdf
from flask_app.utils.ldap_utils import login_required

role_bp = Blueprint('role', __name__)

@role_bp.route('/role_users', methods=['GET', 'POST'])
@login_required
def role_users():
    prefill_role_name = request.args.get('role_cn', '')
    search_results = None
    result = None

    if request.method == 'POST' or prefill_role_name:
        # Get the role CN from the form
        role_cn = request.form.get('role_cn', '') or prefill_role_name
        
        # Check if wildcard search is needed (contains *)
        has_wildcard = '*' in role_cn
        
        # Use the METAModel for searching
        ldap_model = METAModel()
        
        if has_wildcard:
            # For wildcard searches, get multiple matching roles
            search_results = ldap_model.autocomplete_role(role_cn)
            
            # If only one role is found, get its users directly
            if len(search_results) == 1:
                exact_role_cn = search_results[0]['value']
                result = ldap_model.get_role_users(exact_role_cn)
                search_results = None
            elif len(search_results) == 0:
                flash('No roles found matching your criteria.', 'warning')
        else:
            # Direct search for a specific role
            result = ldap_model.get_role_users(role_cn)
            
            if not result:
                flash('Role not found.', 'warning')
        
        return render_template('role_users.html', 
                              result=result, 
                              search_results=search_results, 
                              prefill_role_name=role_cn)
        
    return render_template('role_users.html', 
                          result=None, 
                          search_results=None, 
                          prefill_role_name=prefill_role_name)

@role_bp.route('/role_groups', methods=['GET', 'POST'])
@login_required
def role_groups():
    prefill_role_name = request.args.get('role_cn', '')
    if request.method == 'POST' or prefill_role_name:
        # Get the role CN from the form
        role_cn = request.form.get('role_cn', '') or prefill_role_name
        
        # Use the LDAPModel to get role groups or resources
        ldap_model = METAModel()
        result = ldap_model.get_role_groups(role_cn)
    
        return render_template('role_groups.html', result=result, prefill_role_cn=role_cn)
    return render_template('role_groups.html', result=None, prefill_role_cn='')


@role_bp.route('/export_role_users_csv/<role_cn>')
@login_required
def export_role_users_csv(role_cn):
    ldap_model = METAModel()
    result = ldap_model.get_role_users(role_cn)
    if result and result['users']:
        return util_export_role_users_csv(role_cn, result['users'])
    return redirect(url_for('role.role_users'))

@role_bp.route('/export_role_users_pdf/<role_cn>')
@login_required
def export_role_users_pdf(role_cn):
    ldap_model = METAModel()
    result = ldap_model.get_role_users(role_cn)
    if result and result['users']:
        return util_export_role_users_pdf(role_cn, result['users'])
    return redirect(url_for('role.role_users'))

@role_bp.route('/view_role/<path:dn>')
@login_required
def view_role(dn):
    try:
        ldap_model = METAModel()
        data = ldap_model.view_role(dn)
        if not data:
            flash('Role not found.', 'danger')
            return redirect(url_for('ldap.ldap_browser'))
        return render_template('view_role.html', **data)
    except Exception as e:
        print(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('ldap.ldap_browser'))