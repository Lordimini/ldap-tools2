from flask import Blueprint, render_template, request, redirect, url_for, flash, session, json, jsonify
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
    Process user updates, handling both full form submissions and AJAX partial updates.
    """
    if request.method != 'POST':
        # Should not happen with route decorator, but good practice
        return redirect(url_for('userupdate.update_user_page'))

    user_dn = request.form.get('user_dn')
    ldap_source = request.form.get('ldap_source') or session.get('ldap_source', 'meta')
    update_section = request.form.get('update_section') # Identifier for AJAX partial updates

    # Update session
    session['ldap_source'] = ldap_source
    session.modified = True

    if not user_dn:
        message = 'No user DN provided'
        if update_section: # AJAX request
            return jsonify({'status': 'error', 'message': message}), 400
        else: # Full form submission
            flash(message, 'error')
            return redirect(url_for('userupdate.update_user_page', source=ldap_source))

    # Initialize data containers
    attributes = {}
    groups_to_add = None
    groups_to_remove = None
    reset_password = None
    expire_password = None
    target_container = None
    associations_to_delete = None # Added for DirXML tab

    # --- Conditionally gather data based on update_section ---
    # If no section specified (old behavior or error), try to update all
    # Otherwise, only gather data for the specific section

    # General Tab
    if not update_section or update_section == 'general':
        # Note: Read-only fields like mail, givenName, sn are not updated here.
        # Only editable fields from the General tab.
        if request.form.get('workforceID') is not None:
             attributes['workforceID'] = request.form.get('workforceID')
        if request.form.get('FavvEmployeeType') is not None:
             attributes['FavvEmployeeType'] = request.form.get('FavvEmployeeType')
        if request.form.get('manager_dn') is not None:
             attributes['FavvHierarMgrDN'] = request.form.get('manager_dn')
        # Add other editable fields from General tab if any

    # Groups Tab
    if not update_section or update_section == 'groups':
        try:
            groups_to_add_json = request.form.get('groups_to_add', '[]')
            groups_to_add = json.loads(groups_to_add_json)
            groups_to_remove_json = request.form.get('groups_to_remove', '[]')
            groups_to_remove = json.loads(groups_to_remove_json)
        except json.JSONDecodeError as e:
            message = f'Error parsing group data: {e}'
            if update_section:
                return jsonify({'status': 'error', 'message': message}), 400
            else:
                flash(message, 'error')
                return redirect(url_for('userupdate.select_user', user_dn=user_dn, source=ldap_source))

    # Security Tab
    if not update_section or update_section == 'security':
        # loginDisabled is always sent by checkbox, check its value
        attributes['loginDisabled'] = 'TRUE' if request.form.get('loginDisabled') == 'true' else 'FALSE'
        reset_password = request.form.get('reset_password') == 'true'
        expire_password = request.form.get('expire_password') == 'true'
        # Add other security fields if needed (minPasswordLength, graceLogins etc.)
        # attributes['minPwdLength'] = request.form.get('minPasswordLength') # Example

    # Container Tab
    if not update_section or update_section == 'container':
        target_container = request.form.get('target_container', '') # Empty string if not provided

    # DirXML Tab
    if not update_section or update_section == 'DirXML':
        try:
            associations_to_delete_json = request.form.get('associations_to_delete', '[]')
            associations_to_delete = json.loads(associations_to_delete_json)
        except json.JSONDecodeError as e:
            message = f'Error parsing DirXML associations data: {e}'
            if update_section:
                return jsonify({'status': 'error', 'message': message}), 400
            else:
                flash(message, 'error')
                return redirect(url_for('userupdate.select_user', user_dn=user_dn, source=ldap_source))

    # Add conditions for other tabs (Account, Restrictions, Protime, Misc) if they have editable fields
    # Example for a hypothetical 'misc' field:
    # if not update_section or update_section == 'misc':
    #     if request.form.get('someMiscField') is not None:
    #         attributes['someMiscLDAPAttr'] = request.form.get('someMiscField')

    # --- Perform Update ---
    ldap_model = LDAPModel(source=ldap_source)
    change_reason = request.form.get('change_reason', f'Update via Web UI - Section: {update_section or "All"}') # Add section to reason

    # --- Construct options dictionary for LDAPUserCRUD.update_user ---
    options = {}
    if groups_to_add is not None:
        options['groups_to_add'] = groups_to_add
    if groups_to_remove is not None:
        options['groups_to_remove'] = groups_to_remove
    if reset_password is not None:
        options['reset_password'] = reset_password
    if expire_password is not None:
        options['expire_password'] = expire_password
    if target_container is not None:
        options['target_container'] = target_container
    if associations_to_delete is not None:
        options['associations_to_delete'] = associations_to_delete
    if change_reason:
        options['change_reason'] = change_reason

    # --- Perform Update ---
    ldap_model = LDAPModel(source=ldap_source)
    success, message = ldap_model.update_user(
        user_dn=user_dn,
        attributes=attributes if attributes else None, # Pass None if no attributes changed
        options=options if options else None # Pass None if no options changed
    )

    # --- Respond ---
    if update_section: # AJAX request
        if success:
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': message}), 400 # Use 400 for client-side errors
    else: # Full form submission (fallback, should not happen with new JS)
        if success:
            flash(message, 'success')
            if target_container: # Moved container
                return redirect(url_for('userupdate.update_user_page', source=ldap_source))
            else: # Refresh same user page
                return redirect(url_for('userupdate.select_user', user_dn=user_dn, source=ldap_source))
        else:
            flash(message, 'error')
            return redirect(url_for('userupdate.select_user', user_dn=user_dn, source=ldap_source))