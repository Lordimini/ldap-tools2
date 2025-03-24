from flask import Blueprint, render_template, request, redirect, url_for, flash, session, json, current_app
from flask_app.models.ldap_model import LDAPModel
from flask_login import login_required, current_user
from flask_app.models.ldap_config_manager import LDAPConfigManager


postcreation_bp = Blueprint('postcreation', __name__)

@postcreation_bp.route('/post_creation', methods=['GET', 'POST'])
@login_required
def post_creation():
    """
    Display the list of pending users in the toprocess container
    and allow selection for completion.
    """
    
    ldap_source = request.args.get('source')
    if request.method == 'POST':
        ldap_source = request.form.get('ldap_source', ldap_source)
    
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    session['ldap_source'] = ldap_source
    session.modified = True
    
    ldap_model = LDAPModel(source=ldap_source)
    
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    # pending_users = ldap_model.get_pending_users()
    
    # Get all pending users
    options = {
                'container': 'toprocess',
                'return_list': True
                }
    all_pending_users = ldap_model.get_user("(objectClass=Person)", options)
    
    # Get role config service from app
    role_config = current_app.role_config
    
    # Get allowed user types for current user's roles
    allowed_types = role_config.get_allowed_user_types(current_user.roles)
    
    # Filter users based on allowed types
    if '*' in allowed_types:
        # Admin can see all users
        pending_users = all_pending_users
    else:
        # Filter users by type
        pending_users = []
        for user in all_pending_users:
            # You'll need to modify get_pending_users to include user type
            # or fetch user details here
            options = {
                'container': 'all',
                }
            user_details = ldap_model.get_user(user['dn'], options)
            
            if user_details and 'title' in user_details:
                user_type = user_details['title']
                if user_type in allowed_types:
                    pending_users.append(user)
    
    
    selected_user = None
    
    # Check if a user_dn is provided in the POST form
    if request.method == 'POST' and 'user_dn' in request.form:
        user_dn = request.form['user_dn']
        if user_dn:
            options = {
                'container': 'toprocess',
                'simplified': True
                }
            selected_user = ldap_model.get_user(user_dn, options)
            
    
    # Check if a user_dn is provided in the URL (after redirect)
    elif request.method == 'GET' and 'user_dn' in request.args:
        user_dn = request.args.get('user_dn')
        if user_dn:
            options = {
                'container': 'toprocess',
                'simplified': True
                }
            selected_user = ldap_model.get_user(user_dn, options)
    
    return render_template('post-creation.html', 
                          pending_users=pending_users,
                          selected_user=selected_user,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)

@postcreation_bp.route('/select_user', methods=['POST'])
@login_required
def select_user():
    """
    Handle the user selection from the dropdown and redirect back to the main form
    """
    user_dn = request.form.get('user_dn', '')
    
    # Get LDAP source from form with fallback
    ldap_source = request.form.get('ldap_source', session.get('ldap_source', 'meta'))
    
    # Update session
    session['ldap_source'] = ldap_source
    session.modified = True
    
    return redirect(url_for('postcreation.post_creation', user_dn=user_dn, source=ldap_source))

@postcreation_bp.route('/complete_user', methods=['POST'])
@login_required
def complete_user():
    """
    Process the form submission to complete the user creation.
    This will move the user to the selected container and set additional attributes.
    """
    if request.method == 'POST':
        user_dn = request.form.get('user_dn')
        target_container = request.form.get('target_container')
        
        # Get LDAP source from form with fallback
        ldap_source = request.form.get('ldap_source', session.get('ldap_source', 'meta'))
        
        # Update session
        session['ldap_source'] = ldap_source
        session.modified = True
        
        # Collect form data for attributes
        attributes = {
            'workforceID': request.form.get('workforceID', ''),
            'title': request.form.get('title', ''),
            'generationQualifier': request.form.get('generationQualifier', ''),
            'ou': request.form.get('ou', ''),
            'FavvEmployeeType': request.form.get('FavvEmployeeType', ''),
            'FavvHierarMgrDN': request.form.get('manager_dn', ''),
            'loginDisabled': 'TRUE' if request.form.get('loginDisabled') else 'FALSE'
        }
        
        # Get and parse selected groups from the form
        groups = []
        try:
            groups_json = request.form.get('selected_groups', '[]')
            print(f"Raw groups JSON: {groups_json}")
            
            # Parse JSON data
            if groups_json:
                groups_data = json.loads(groups_json)
                print(f"Parsed groups data: {groups_data}")
                
                # Process each group entry
                for group in groups_data:
                    if isinstance(group, dict) and 'name' in group:
                        # Group data is already in correct format
                        groups.append(group)
                    elif isinstance(group, str):
                        # Simple string, convert to dict with name
                        groups.append({'name': group})
                    else:
                        print(f"Warning: Unexpected group format: {group}")
            
            print(f"Processed groups to pass to complete_user_creation: {groups}")
            
        except json.JSONDecodeError as e:
            flash(f'Error parsing group data: {str(e)}', 'error')
            return redirect(url_for('postcreation.post_creation', source=ldap_source))
        
        # Set password flag
        set_password = request.form.get('set_password') == 'true'
        
        # Complete the user creation process
        ldap_model = LDAPModel(source=ldap_source)
        
        # Configurer les options pour update_user
        options = {
            'target_container': target_container,
            'groups_to_add': groups,
            'reset_password': set_password,
            'is_completion': True  # Indique qu'il s'agit d'une opération de complétion
        }

        # Appeler update_user avec les mêmes paramètres
        success, message = ldap_model.update_user(
            user_dn=user_dn,
            attributes=attributes,
            options=options
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('postcreation.post_creation', source=ldap_source))
    
    # Default LDAP source from session
    ldap_source = session.get('ldap_source', 'meta')
    return redirect(url_for('postcreation.post_creation', source=ldap_source))

@postcreation_bp.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    """
    Delete a user from the pending container.
    """
    if request.method == 'POST':
        user_dn = request.form.get('user_dn')
        
        # Get LDAP source from form with fallback
        ldap_source = request.form.get('ldap_source', session.get('ldap_source', 'meta'))
        
        # Update session
        session['ldap_source'] = ldap_source
        session.modified = True
        
        if user_dn:
            ldap_model = LDAPModel(source=ldap_source)
            success, message = ldap_model.delete_user(user_dn)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
        
        return redirect(url_for('postcreation.post_creation', source=ldap_source))
    
    # Default LDAP source from session
    ldap_source = session.get('ldap_source', 'meta')
    return redirect(url_for('postcreation.post_creation', source=ldap_source))