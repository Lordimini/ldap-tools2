from flask import Blueprint, render_template, request, redirect, url_for, flash, session, json
from flask_app.models.ldap_model import LDAPModel
from flask_login import login_required  # Nouvel import depuis Flask-Login
from flask_app.models.ldap_config_manager import LDAPConfigManager
from ldap3 import MODIFY_REPLACE, MODIFY_DELETE, MODIFY_ADD

userupdate_bp = Blueprint('userupdate', __name__)

@userupdate_bp.route('/update_user', methods=['GET', 'POST'])
@login_required
def update_user_page():
    """
    Main route for the Update User page
    """
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
    
    # Render the form initially without any data - use empty strings instead of None
    search_type = ""
    search_term = ""
    search_results = None
    selected_user = None

    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')

    # Check if a user_dn parameter is provided in the URL (after redirecting from search results)
    if request.args.get('user_dn'):
        user_dn = request.args.get('user_dn')
        options = {
            'container': 'all'  # Rechercher dans tous les conteneurs
        }
        user_info = ldap_model.get_user(user_dn, options)
        if user_info:
            selected_user = user_info

    return render_template('update-user.html', 
                           search_type=search_type,
                           search_term=search_term,
                           search_results=search_results,
                           selected_user=selected_user,
                           ldap_source=ldap_source,
                           ldap_name=ldap_name)

@userupdate_bp.route('/search_user', methods=['POST'])
@login_required
def search_user():
    """
    Handle the user search form
    """
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        search_term = request.form.get('search_term')
        
        # Get LDAP source with proper fallback sequence
        ldap_source = request.form.get('ldap_source')
        
        # If not in form params, get from session with default fallback
        if not ldap_source:
            ldap_source = session.get('ldap_source', 'meta')
        
        # Make sure session is updated with current source
        session['ldap_source'] = ldap_source
        session.modified = True
        
        if not search_term or not search_type:
            flash('Please provide a search term and type', 'error')
            return redirect(url_for('userupdate.update_user_page', source=ldap_source))
        
        # Create LDAP model with the appropriate source
        ldap_model = LDAPModel(source=ldap_source)
        
        # Get LDAP name for display purposes
        config = LDAPConfigManager.get_config(ldap_source)
        ldap_name = config.get('LDAP_name', 'META')
        
        options = {
            'search_type': search_type,
            'container': 'active',
            'return_list': True
        }
        search_results = ldap_model.get_user(search_term, options)
        
        return render_template('update-user.html', 
                              search_type=search_type,
                              search_term=search_term,
                              search_results=search_results,
                              selected_user=None,
                              ldap_source=ldap_source,
                              ldap_name=ldap_name)
    
    return redirect(url_for('userupdate.update_user_page'))

@userupdate_bp.route('/select_user', methods=['GET'])
@login_required
def select_user():
    """
    Select a user from search results for editing
    """
    user_dn = request.args.get('user_dn')
    
    # Get LDAP source with proper fallback sequence
    ldap_source = request.args.get('source')
    
    # If not in query params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    if not user_dn:
        flash('No user selected', 'error')
        return redirect(url_for('userupdate.update_user_page', source=ldap_source))
    
    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    options = {
    'container': 'all'  
    }

    user_info = ldap_model.get_user(user_dn, options)
    
    if not user_info:
        flash('User not found', 'error')
        return redirect(url_for('userupdate.update_user_page', source=ldap_source))
    
    return render_template('update-user.html',
                           search_results=None,
                           selected_user=user_info,
                           ldap_source=ldap_source,
                           ldap_name=ldap_name)

@userupdate_bp.route('/update_user', methods=['POST'])
@login_required
def update_user():
    """
    Process user updates
    """
    if request.method != 'POST':
        return redirect(url_for('userupdate.update_user_page'))
    
    user_dn = request.form.get('user_dn')
    
    # Get LDAP source with proper fallback sequence
    ldap_source = request.form.get('ldap_source')
    
    # If not in form params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    if not user_dn:
        flash('No user DN provided', 'error')
        return redirect(url_for('userupdate.update_user_page', source=ldap_source))
    
    # Collect form data for user attributes
    attributes = {}
    
    # Basic information updates
    if request.form.get('mail'):
        attributes['mail'] = request.form.get('mail')
    
    if request.form.get('workforceID'):
        attributes['workforceID'] = request.form.get('workforceID')
    
    if request.form.get('title'):
        attributes['title'] = request.form.get('title')
    
    if request.form.get('ou'):
        attributes['ou'] = request.form.get('ou')
    
    if request.form.get('FavvEmployeeType'):
        attributes['FavvEmployeeType'] = request.form.get('FavvEmployeeType')
    
    if request.form.get('manager_dn'):
        attributes['FavvHierarMgrDN'] = request.form.get('manager_dn')
    
    # Process login disabled status
    if request.form.get('loginDisabled') == 'true':
        attributes['loginDisabled'] = 'TRUE'
    else:
        attributes['loginDisabled'] = 'FALSE'
    
    # Process groups to add
    groups_to_add = []
    try:
        groups_to_add_json = request.form.get('groups_to_add', '[]')
        groups_to_add = json.loads(groups_to_add_json)
    except json.JSONDecodeError:
        flash('Error parsing groups to add data', 'error')
    
    # Process groups to remove
    groups_to_remove = []
    try:
        groups_to_remove_json = request.form.get('groups_to_remove', '[]')
        groups_to_remove = json.loads(groups_to_remove_json)
    except json.JSONDecodeError:
        flash('Error parsing groups to remove data', 'error')
    
    # Check for password reset option
    reset_password = request.form.get('reset_password') == 'true'
    
    # Check for password expiration option
    expire_password = request.form.get('expire_password') == 'true'
    
    # Check for container move option
    target_container = request.form.get('target_container', '')
    
    # Record reason for changes
    change_reason = request.form.get('change_reason', '')
    
    # Call the LDAP model to update the user
    ldap_model = LDAPModel(source=ldap_source)
    success, message = ldap_model.update_user(
        user_dn=user_dn,
        attributes=attributes,
        groups_to_add=groups_to_add,
        groups_to_remove=groups_to_remove,
        reset_password=reset_password,
        expire_password=expire_password,
        target_container=target_container,
        change_reason=change_reason
    )
    
    if success:
        flash(message, 'success')
        
        # If the user was moved to a different container, redirect to the base page
        # since the original DN is no longer valid
        if target_container:
            return redirect(url_for('userupdate.update_user_page', source=ldap_source))
        
        # Otherwise, refresh the user's information with the new values
        return redirect(url_for('userupdate.select_user', user_dn=user_dn, source=ldap_source))
    else:
        flash(message, 'error')
        # Return to the form with the previously selected user
        return redirect(url_for('userupdate.select_user', user_dn=user_dn, source=ldap_source))