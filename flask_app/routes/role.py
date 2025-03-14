from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_app.models.edir_model import EDIRModel
from flask_app.models.ldap_config_manager import LDAPConfigManager
from flask_app.utils.export_utils import util_export_role_users_csv, util_export_role_users_pdf
from flask_app.utils.ldap_utils import login_required

role_bp = Blueprint('role', __name__)

@role_bp.route('/role_users', methods=['GET', 'POST'])
@login_required
def role_users():
    # Get prefill values from query parameters
    prefill_role_name = request.args.get('role_cn', '')
    
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
    
    # Create EDIR model with the appropriate source
    ldap_model = EDIRModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    search_results = None
    result = None

    if request.method == 'POST' or prefill_role_name:
        # Get the role CN from the form
        role_cn = request.form.get('role_cn', '') or prefill_role_name
        
        # Check if wildcard search is needed (contains *)
        has_wildcard = '*' in role_cn
        
        # Use the EDIRModel for searching
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
                              prefill_role_name=role_cn,
                              ldap_source=ldap_source,
                              ldap_name=ldap_name)
        
    return render_template('role_users.html', 
                          result=None, 
                          search_results=None, 
                          prefill_role_name=prefill_role_name,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)

@role_bp.route('/role_groups', methods=['GET', 'POST'])
@login_required
def role_groups():
    prefill_role_name = request.args.get('role_cn', '')
    
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
    
    # Create EDIR model with the appropriate source
    ldap_model = EDIRModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    if request.method == 'POST' or prefill_role_name:
        # Get the role CN from the form
        role_cn = request.form.get('role_cn', '') or prefill_role_name
        
        # Use the LDAPModel to get role groups or resources
        result = ldap_model.get_role_groups(role_cn)
    
        return render_template('role_groups.html', 
                              result=result, 
                              prefill_role_cn=role_cn,
                              ldap_source=ldap_source,
                              ldap_name=ldap_name)
    
    return render_template('role_groups.html', 
                          result=None, 
                          prefill_role_cn='',
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)


@role_bp.route('/export_role_users_csv/<role_cn>')
@login_required
def export_role_users_csv(role_cn):
    # Get LDAP source with proper fallback
    ldap_source = request.args.get('source')
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Create EDIR model with the appropriate source
    ldap_model = EDIRModel(source=ldap_source)
    
    result = ldap_model.get_role_users(role_cn)
    if result and result['users']:
        return util_export_role_users_csv(role_cn, result['users'])
    
    return redirect(url_for('role.role_users', source=ldap_source))

@role_bp.route('/export_role_users_pdf/<role_cn>')
@login_required
def export_role_users_pdf(role_cn):
    # Get LDAP source with proper fallback
    ldap_source = request.args.get('source')
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Create EDIR model with the appropriate source
    ldap_model = EDIRModel(source=ldap_source)
    
    result = ldap_model.get_role_users(role_cn)
    if result and result['users']:
        return util_export_role_users_pdf(role_cn, result['users'])
    
    return redirect(url_for('role.role_users', source=ldap_source))

@role_bp.route('/view_role/<path:dn>')
@login_required
def view_role(dn):
    # Get LDAP source with proper fallback
    ldap_source = request.args.get('source')
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Create EDIR model with the appropriate source
    ldap_model = EDIRModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    try:
        data = ldap_model.view_role(dn)
        if not data:
            flash('Role not found.', 'danger')
            return redirect(url_for('ldap.ldap_browser', source=ldap_source))
        
        # Add LDAP source information to template context
        data['ldap_source'] = ldap_source
        data['ldap_name'] = ldap_name
        
        return render_template('view_role.html', **data)
    except Exception as e:
        print(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('ldap.ldap_browser', source=ldap_source))