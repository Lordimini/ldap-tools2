from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_app.models.edir_model import EDIRModel
from flask_app.models.ldap_config_manager import LDAPConfigManager
from flask_app.utils.export_utils import util_export_group_users_csv
from flask_app.utils.ldap_utils import login_required

group_bp = Blueprint('group', __name__)

@group_bp.route('/group_users', methods=['GET', 'POST'])
@login_required
def group_users():
    prefill_group_name = request.args.get('group_name', '')
    prefill_group_dn = request.args.get('group_dn', '')
    
    # Récupérer la source LDAP depuis les paramètres de requête - à définir avant les conditions
    ldap_source = request.args.get('source', 'meta')
    if request.method == 'POST':
        # Si la méthode est POST, prendre la source du formulaire si elle existe
        ldap_source = request.form.get('ldap_source', ldap_source)
    
    # Créer une instance du modèle LDAP avec la source spécifiée
    ldap_model = EDIRModel(source=ldap_source)
    
    # Récupérer le nom de la directory depuis la configuration
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    if request.method == 'POST' or prefill_group_name:
        # Récupérer les données du formulaire ou des paramètres de requête
        group_name = request.form.get('group_name', '') or prefill_group_name
        group_dn = request.form.get('group_dn', '') or prefill_group_dn
        
        # Si nous avons un DN spécifique, l'utiliser pour la recherche
        if group_dn:
            result = ldap_model.get_group_users_by_dn(group_dn, group_name)
        else:
            # Sinon, utiliser la méthode existante basée sur le CN
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
    
    ldap_model = EDIRModel()
    
    # Si nous avons un DN spécifique, l'utiliser
    if group_dn:
        result = ldap_model.get_group_users_by_dn(group_dn, group_name)
    else:
        # Sinon, utiliser la méthode existante basée sur le CN
        result = ldap_model.get_group_users(group_name)
    
    if result and result['users']:
        return util_export_group_users_csv(result['group_name'], result['users'])
    
    return redirect(url_for('group.group_users'))

@group_bp.route('/add_users_to_group', methods=['GET', 'POST'])
@login_required
def add_users_to_group():
    """Route pour la page d'ajout d'utilisateurs à un groupe"""
    prefill_group_name = request.args.get('group_name', '')
    prefill_group_dn = request.args.get('group_dn', '')
    group_info = None
    selected_users = []
    
    if request.method == 'POST':
        # Récupérer les informations du groupe depuis le formulaire
        group_name = request.form.get('group_name', '')
        group_dn = request.form.get('group_dn', '')
        
        # Récupérer les utilisateurs sélectionnés, si présents
        selected_users_json = request.form.get('selected_users_json', '[]')
        try:
            import json
            selected_users = json.loads(selected_users_json)
            print(f"POST add_users_to_group - selected_users: {selected_users}")
        except Exception as e:
            print(f"Error parsing selected_users_json: {e}")
            selected_users = []
        
        ldap_model = EDIRModel()
        
        # Si nous avons un DN spécifique, l'utiliser pour la recherche
        if group_dn:
            group_info = ldap_model.get_group_users_by_dn(group_dn, group_name)
        else:
            # Sinon, utiliser la méthode existante basée sur le CN
            group_info = ldap_model.get_group_users(group_name)
        
        if not group_info:
            flash('Group not found. Please try again.', 'danger')
            return render_template('add_user_list_group.html', 
                                  prefill_group_name=group_name, 
                                  prefill_group_dn=group_dn)
        
        # Stocker les informations du groupe en session pour les futures requêtes
        session['current_group'] = {
            'name': group_info['group_name'],
            'dn': group_info['group_dn']
        }
        
        # Stocker également les utilisateurs sélectionnés
        session['selected_users'] = selected_users
        
        return render_template('add_user_list_group.html', 
                              group_info=group_info,
                              prefill_group_name=group_name, 
                              prefill_group_dn=group_dn,
                              selected_users=selected_users)
    
    # En cas de GET, si on a des informations en session, les restaurer
    if 'current_group' in session:
        ldap_model = EDIRModel()
        group_data = session['current_group']
        group_info = ldap_model.get_group_users_by_dn(group_data['dn'], group_data['name'])
        selected_users = session.get('selected_users', [])
        print(f"GET add_users_to_group - selected_users from session: {selected_users}")
    
    return render_template('add_user_list_group.html', 
                          group_info=group_info,
                          prefill_group_name=prefill_group_name, 
                          prefill_group_dn=prefill_group_dn,
                          selected_users=selected_users)

@group_bp.route('/search_users_for_group', methods=['POST'])
@login_required
def search_users_for_group():
    """Route pour rechercher des utilisateurs à ajouter au groupe"""
    group_name = request.form.get('group_name', '')
    group_dn = request.form.get('group_dn', '')
    search_type = request.form.get('search_type', 'fullName')
    search_term = request.form.get('search_term', '')
    
    # Récupérer les utilisateurs déjà sélectionnés du formulaire
    selected_users_json = request.form.get('selected_users_json', '[]')
    
    import json
    try:
        selected_users = json.loads(selected_users_json)
    except Exception as e:
        print(f"Error parsing selected_users_json: {e}")
        selected_users = []
    
    # Sauvegarder dans la session
    session['selected_users'] = selected_users
    
    if not group_name or not group_dn or not search_term:
        flash('Missing required parameters.', 'danger')
        return redirect(url_for('group.add_users_to_group'))
    
    ldap_model = EDIRModel()
    
    # Récupérer les informations du groupe
    group_info = ldap_model.get_group_users_by_dn(group_dn, group_name)
    
    if not group_info:
        flash('Group not found.', 'danger')
        return redirect(url_for('group.add_users_to_group'))
    
    # Rechercher les utilisateurs actifs
    search_results = ldap_model.search_user_final(search_term, search_type, search_active_only=True, return_list=True)
    
    if not search_results:
        flash('No users found matching your search criteria.', 'info')
    
    # Filtrer les utilisateurs qui sont déjà membres du groupe
    if search_results and group_info and 'users' in group_info:
        existing_users_cn = [user['CN'] for user in group_info['users']]
        search_results = [user for user in search_results if user['cn'] not in existing_users_cn]
    
    # Filtrer également les utilisateurs déjà sélectionnés
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
                          selected_users=selected_users)

@group_bp.route('/confirm_add_users', methods=['POST'])
@login_required
def confirm_add_users():
    """Route pour confirmer l'ajout des utilisateurs sélectionnés au groupe"""
    group_name = request.form.get('group_name', '')
    group_dn = request.form.get('group_dn', '')
    selected_users_json = request.form.get('selected_users', '[]')
    
    import json
    try:
        selected_users = json.loads(selected_users_json)
        print(f"confirm_add_users - Processing users: {selected_users}")
    except Exception as e:
        print(f"Error parsing selected_users: {e}")
        selected_users = []
    
    # Vider la liste des utilisateurs sélectionnés dans la session
    session.pop('selected_users', None)
    
    if not group_name or not group_dn or not selected_users:
        flash('No users selected or group information missing.', 'warning')
        return redirect(url_for('group.add_users_to_group'))
    
    ldap_model = EDIRModel()
    
    # Compter les succès et les échecs
    success_count = 0
    failures = []
    
    # Ajouter chaque utilisateur au groupe
    for user in selected_users:
        user_dn = user.get('dn')
        if user_dn:
            result = ldap_model.add_user_to_group(user_dn, group_dn)
            if result:
                success_count += 1
            else:
                failures.append(f"Failed to add user {user.get('cn')} ({user.get('fullName')})")
    
    # Construire un message de succès/échec
    if success_count > 0:
        flash(f'Successfully added {success_count} users to group {group_name}.', 'success')
    
    if failures:
        for failure in failures:
            flash(failure, 'danger')
    
    # Rediriger vers la page du groupe pour voir les changements
    return redirect(url_for('group.group_users', group_name=group_name, group_dn=group_dn))

@group_bp.route('/validate_bulk_cns', methods=['POST'])
@login_required
def validate_bulk_cns():
    """Valide une liste de CNs et retourne les utilisateurs trouvés"""
    # Récupérer les données JSON de la requête
    data = request.get_json()
    if not data or 'cn_list' not in data or 'group_dn' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    cn_list = data.get('cn_list', [])
    group_dn = data.get('group_dn', '')
    
    if not cn_list or not group_dn:
        return jsonify({'error': 'Empty CN list or group DN'}), 400
    
    ldap_model = EDIRModel()
    
    # Récupérer les informations du groupe pour vérifier les membres existants
    group_info = ldap_model.get_group_users_by_dn(group_dn)
    existing_cns = []
    if group_info and 'users' in group_info:
        existing_cns = [user['CN'].upper() for user in group_info['users']]
    
    valid_users = []
    invalid_users = []
    
    # Pour chaque CN dans la liste, vérifier s'il existe
    for cn in cn_list:
        # Convertir le CN en majuscules pour être cohérent avec le format LDAP
        cn = cn.strip().upper()
        
        # Vérifier si l'utilisateur est déjà membre du groupe
        if cn in existing_cns:
            invalid_users.append(cn)
            continue
        
        # Rechercher l'utilisateur dans le LDAP
        user_info = ldap_model.search_user_final(cn, 'cn', simplified=True)
        
        if user_info:
            # Utilisateur trouvé, ajouter aux utilisateurs valides
            valid_users.append({
                'dn': user_info['dn'],
                'cn': user_info['cn'],
                'fullName': user_info['fullName']
            })
        else:
            # Utilisateur non trouvé, ajouter aux CNs invalides
            invalid_users.append(cn)
    
    return jsonify({
        'valid_users': valid_users,
        'invalid_users': invalid_users
    })