from flask import Blueprint, render_template, request, redirect, url_for
from flask_app.models.meta_model import METAModel
from flask_app.utils.export_utils import util_export_group_users_csv
from flask_app.utils.ldap_utils import login_required

group_bp = Blueprint('group', __name__)

@group_bp.route('/group_users', methods=['GET', 'POST'])
@login_required
def group_users():
    prefill_group_name = request.args.get('group_name', '')
    prefill_group_dn = request.args.get('group_dn', '')
    
    if request.method == 'POST' or prefill_group_name:
        # Récupérer les données du formulaire ou des paramètres de requête
        group_name = request.form.get('group_name', '') or prefill_group_name
        group_dn = request.form.get('group_dn', '') or prefill_group_dn
        
        # Utiliser le modèle LDAP pour obtenir les utilisateurs du groupe
        ldap_model = METAModel()
        
        # Si nous avons un DN spécifique, l'utiliser pour la recherche
        if group_dn:
            result = ldap_model.get_group_users_by_dn(group_dn, group_name)
        else:
            # Sinon, utiliser la méthode existante basée sur le CN
            result = ldap_model.get_group_users(group_name)
        
        return render_template('group_users.html', 
                              result=result, 
                              prefill_group_name=group_name, 
                              prefill_group_dn=group_dn)
    
    return render_template('group_users.html', 
                          result=None, 
                          prefill_group_name=prefill_group_name, 
                          prefill_group_dn=prefill_group_dn)
    
@group_bp.route('/export_group_users_csv')
@login_required
def export_group_users_csv():
    group_name = request.args.get('group_name', '')
    group_dn = request.args.get('group_dn', '')
    
    ldap_model = METAModel()
    
    # Si nous avons un DN spécifique, l'utiliser
    if group_dn:
        result = ldap_model.get_group_users_by_dn(group_dn, group_name)
    else:
        # Sinon, utiliser la méthode existante basée sur le CN
        result = ldap_model.get_group_users(group_name)
    
    if result and result['users']:
        return util_export_group_users_csv(result['group_name'], result['users'])
    
    return redirect(url_for('group.group_users'))