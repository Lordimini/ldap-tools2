from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_app.models.ldap_model import LDAPModel
from flask_app.models.ldap_config_manager import LDAPConfigManager
from flask_app.utils.export_utils import util_export_group_users_csv
from flask_login import login_required  # Nouvel import depuis Flask-Login

group_bp = Blueprint('group', __name__)

@group_bp.route('/group_users', methods=['GET', 'POST'])
@login_required
def group_users():
    # Get prefill values from query parameters
    prefill_group_name = request.args.get('group_name', '')
    prefill_group_dn = request.args.get('group_dn', '')
    
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
    
    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    if request.method == 'POST' or prefill_group_name:
        # Get data from form or request parameters
        group_name = request.form.get('group_name', '') or prefill_group_name
        group_dn = request.form.get('group_dn', '') or prefill_group_dn
        
        # If we have a specific DN, use it for the search
        if group_dn:
            result = ldap_model.get_group_users_by_dn(group_dn, group_name)
        else:
            # Otherwise, use the existing method based on the CN
            result = ldap_model.get_group_users(group_name)
        
        return render_template('group_users.html', 
                              result=result, 
                              prefill_group_name=group_name, 
                              prefill_group_dn=group_dn,
                              ldap_source=ldap_source,
                              ldap_name=ldap_name)
    
    return render_template('group_users.html', 
                          result=None, 
                          prefill_group_name=prefill_group_name, 
                          prefill_group_dn=prefill_group_dn,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)
    
@group_bp.route('/export_group_users_csv')
@login_required
def export_group_users_csv():
    group_name = request.args.get('group_name', '')
    group_dn = request.args.get('group_dn', '')
    
    # Get LDAP source with proper fallback
    ldap_source = request.args.get('source')
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    # If we have a specific DN, use it
    if group_dn:
        result = ldap_model.get_group_users_by_dn(group_dn, group_name)
    else:
        # Otherwise, use the existing method based on the CN
        result = ldap_model.get_group_users(group_name)
    
    if result and result['users']:
        return util_export_group_users_csv(result['group_name'], result['users'])
    
    return redirect(url_for('group.group_users', source=ldap_source))

@group_bp.route('/add_users_to_group', methods=['GET', 'POST'])
@login_required
def add_users_to_group():
    """Route pour la page d'ajout d'utilisateurs à un groupe"""
    prefill_group_name = request.args.get('group_name', '')
    prefill_group_dn = request.args.get('group_dn', '')
    
    # Get LDAP source with proper fallback
    ldap_source = request.args.get('source')
    if request.method == 'POST':
        ldap_source = request.form.get('ldap_source', ldap_source)
    
    # If not in query or form params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    group_info = None
    selected_users = []
    
    if request.method == 'POST':
        # Get group information from the form
        group_name = request.form.get('group_name', '')
        group_dn = request.form.get('group_dn', '')
        
        # Get selected users, if any
        selected_users_json = request.form.get('selected_users_json', '[]')
        try:
            import json
            selected_users = json.loads(selected_users_json)
            print(f"POST add_users_to_group - selected_users: {selected_users}")
        except Exception as e:
            print(f"Error parsing selected_users_json: {e}")
            selected_users = []
        
        # If we have a specific DN, use it for the search
        if group_dn:
            group_info = ldap_model.get_group_users_by_dn(group_dn, group_name)
        else:
            # Otherwise, use the existing method based on the CN
            group_info = ldap_model.get_group_users(group_name)
        
        if not group_info:
            flash('Group not found. Please try again.', 'danger')
            return render_template('add_user_list_group.html', 
                                  prefill_group_name=group_name, 
                                  prefill_group_dn=group_dn,
                                  ldap_source=ldap_source,
                                  ldap_name=ldap_name)
        
        # Store group information in session for future requests
        session['current_group'] = {
            'name': group_info['group_name'],
            'dn': group_info['group_dn']
        }
        
        # Also store selected users and LDAP source
        session['selected_users'] = selected_users
        session['ldap_source'] = ldap_source
        
        return render_template('add_user_list_group.html', 
                              group_info=group_info,
                              prefill_group_name=group_name, 
                              prefill_group_dn=group_dn,
                              selected_users=selected_users,
                              ldap_source=ldap_source,
                              ldap_name=ldap_name)
    
    # In case of GET, if we have information in session, restore it
    if 'current_group' in session:
        # Get LDAP source from session if available
        ldap_source = session.get('ldap_source', ldap_source)
        
        # Reinitialize the model with the correct source
        ldap_model = LDAPModel(source=ldap_source)
        
        # Get LDAP name for display purposes
        config = LDAPConfigManager.get_config(ldap_source)
        ldap_name = config.get('LDAP_name', 'META')
        
        group_data = session['current_group']
        group_info = ldap_model.get_group_users_by_dn(group_data['dn'], group_data['name'])
        selected_users = session.get('selected_users', [])
        print(f"GET add_users_to_group - selected_users from session: {selected_users}")
    
    return render_template('add_user_list_group.html', 
                          group_info=group_info,
                          prefill_group_name=prefill_group_name, 
                          prefill_group_dn=prefill_group_dn,
                          selected_users=selected_users,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)

@group_bp.route('/search_users_for_group', methods=['POST'])
@login_required
def search_users_for_group():
    """Route pour rechercher des utilisateurs à ajouter au groupe"""
    group_name = request.form.get('group_name', '')
    group_dn = request.form.get('group_dn', '')
    search_type = request.form.get('search_type', 'fullName')
    search_term = request.form.get('search_term', '')
    
    # Get LDAP source from form with fallback
    ldap_source = request.form.get('ldap_source', 'meta')
    
    # Make sure session is updated
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    # Get already selected users from the form
    selected_users_json = request.form.get('selected_users_json', '[]')
    
    import json
    try:
        selected_users = json.loads(selected_users_json)
    except Exception as e:
        print(f"Error parsing selected_users_json: {e}")
        selected_users = []
    
    # Save in session
    session['selected_users'] = selected_users
    session['ldap_source'] = ldap_source
    
    if not group_name or not group_dn or not search_term:
        flash('Missing required parameters.', 'danger')
        return redirect(url_for('group.add_users_to_group', source=ldap_source))
    
    # Get group information
    group_info = ldap_model.get_group_users_by_dn(group_dn, group_name)
    
    if not group_info:
        flash('Group not found.', 'danger')
        return redirect(url_for('group.add_users_to_group', source=ldap_source))
    
    # Search active users
    search_results = ldap_model.search_user_final(search_term, search_type, search_active_only=True, return_list=True)
    
    if not search_results:
        flash('No users found matching your search criteria.', 'info')
    
    # Filter users who are already members of the group
    if search_results and group_info and 'users' in group_info:
        existing_users_cn = [user['CN'] for user in group_info['users']]
        search_results = [user for user in search_results if user['cn'] not in existing_users_cn]
    
    # Also filter users who are already selected
    if search_results and selected_users:
        selected_users_dn = [user.get('dn') for user in selected_users]
        search_results = [user for user in search_results if user['dn'] not in selected_users_dn]
    
    return render_template('add_user_list_group.html',
                          group_info=group_info,
                          search_results=search_results,
                          search_type=search_type,
                          search_term=search_term,
                          prefill_group_name=group_name,
                          prefill_group_dn=group_dn,
                          selected_users=selected_users,
                          ldap_source=ldap_source,
                          ldap_name=ldap_name)

@group_bp.route('/confirm_add_users', methods=['POST'])
@login_required
def confirm_add_users():
    """Route pour confirmer l'ajout des utilisateurs sélectionnés au groupe"""
    group_name = request.form.get('group_name', '')
    group_dn = request.form.get('group_dn', '')
    selected_users_json = request.form.get('selected_users', '[]')
    
    # Get LDAP source from form with fallback
    ldap_source = request.form.get('ldap_source', 'meta')
    
    # Make sure session is updated
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    import json
    try:
        selected_users = json.loads(selected_users_json)
        print(f"confirm_add_users - Processing users: {selected_users}")
    except Exception as e:
        print(f"Error parsing selected_users: {e}")
        selected_users = []
    
    # Clear selected users list in session
    session.pop('selected_users', None)
    
    if not group_name or not group_dn or not selected_users:
        flash('No users selected or group information missing.', 'warning')
        return redirect(url_for('group.add_users_to_group', source=ldap_source))
    
    # Count successes and failures
    success_count = 0
    failures = []
    
    # Add each user to the group
    for user in selected_users:
        user_dn = user.get('dn')
        if user_dn:
            result = ldap_model.add_user_to_group(user_dn, group_dn)
            if result:
                success_count += 1
            else:
                failures.append(f"Failed to add user {user.get('cn')} ({user.get('fullName')})")
    
    # Build success/failure message
    if success_count > 0:
        flash(f'Successfully added {success_count} users to group {group_name}.', 'success')
    
    if failures:
        for failure in failures:
            flash(failure, 'danger')
    
    # Redirect to group page to see changes
    return redirect(url_for('group.group_users', group_name=group_name, group_dn=group_dn, source=ldap_source))

@group_bp.route('/validate_bulk_cns', methods=['POST'])
@login_required
def validate_bulk_cns():
    """Valide une liste de CNs et retourne les utilisateurs trouvés"""
    # Get JSON data from request
    data = request.get_json()
    if not data or 'cn_list' not in data or 'group_dn' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    cn_list = data.get('cn_list', [])
    group_dn = data.get('group_dn', '')
    
    # Get LDAP source from JSON data with fallback
    ldap_source = data.get('ldap_source', 'meta')
    
    # Make sure session is updated
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Create LDAP model with the appropriate source
    ldap_model = LDAPModel(source=ldap_source)
    
    if not cn_list or not group_dn:
        return jsonify({'error': 'Empty CN list or group DN'}), 400
    
    # Get group information to check existing members
    group_info = ldap_model.get_group_users_by_dn(group_dn)
    existing_cns = []
    if group_info and 'users' in group_info:
        existing_cns = [user['CN'].upper() for user in group_info['users']]
    
    valid_users = []
    invalid_users = []
    
    # For each CN in the list, check if it exists
    for cn in cn_list:
        # Convert CN to uppercase to be consistent with LDAP format
        cn = cn.strip().upper()
        
        # Check if user is already a member of the group
        if cn in existing_cns:
            invalid_users.append(cn)
            continue
        
        # Search for user in LDAP
        user_info = ldap_model.search_user_final(cn, 'cn', simplified=True)
        
        if user_info:
            # User found, add to valid users
            valid_users.append({
                'dn': user_info['dn'],
                'cn': user_info['cn'],
                'fullName': user_info['fullName']
            })
        else:
            # User not found, add to invalid CNs
            invalid_users.append(cn)
    
    return jsonify({
        'valid_users': valid_users,
        'invalid_users': invalid_users
    })