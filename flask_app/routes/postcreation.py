from flask import Blueprint, render_template, request, redirect, url_for, flash, session, json
from flask_app.models.ldap import LDAPModel
from flask_app.utils.ldap_utils import login_required

postcreation_bp = Blueprint('postcreation', __name__)

@postcreation_bp.route('/post_creation', methods=['GET', 'POST'])
@login_required
def post_creation():
    """
    Display the list of pending users in the to-process container
    and allow selection for completion.
    """
    ldap_model = LDAPModel()
    pending_users = ldap_model.get_pending_users()
    
    selected_user = None
    
    # Vérifier si un user_dn est fourni dans le formulaire POST
    if request.method == 'POST' and 'user_dn' in request.form:
        user_dn = request.form['user_dn']
        if user_dn:
            selected_user = ldap_model.get_user_details(user_dn)
    
    # Vérifier si un user_dn est fourni dans l'URL (après redirection)
    elif request.method == 'GET' and 'user_dn' in request.args:
        user_dn = request.args.get('user_dn')
        if user_dn:
            selected_user = ldap_model.get_user_details(user_dn)
    
    return render_template('post-creation.html', 
                          pending_users=pending_users,
                          selected_user=selected_user)

@postcreation_bp.route('/select_user', methods=['POST'])
@login_required
def select_user():
    """
    Handle the user selection from the dropdown and redirect back to the main form
    """
    user_dn = request.form.get('user_dn', '')
    return redirect(url_for('postcreation.post_creation', user_dn=user_dn))

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
            return redirect(url_for('postcreation.post_creation'))
        
        # Set password flag
        set_password = request.form.get('set_password') == 'true'
        
        # Complete the user creation process
        ldap_model = LDAPModel()
        success, message = ldap_model.complete_user_creation(
            user_dn=user_dn,
            target_container=target_container,
            attributes=attributes,
            groups=groups,
            set_password=set_password
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('postcreation.post_creation'))
    
    return redirect(url_for('postcreation.post_creation'))

@postcreation_bp.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    """
    Delete a user from the pending container.
    """
    if request.method == 'POST':
        user_dn = request.form.get('user_dn')
        
        if user_dn:
            ldap_model = LDAPModel()
            success, message = ldap_model.delete_user(user_dn)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
        
        return redirect(url_for('postcreation.post_creation'))
    
    return redirect(url_for('postcreation.post_creation'))