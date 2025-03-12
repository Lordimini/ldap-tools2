from flask import Blueprint, render_template, request, flash, session, url_for, redirect
from flask_app.models.edir_model import EDIRModel
from flask_app.utils.ldap_utils import login_required
from flask_app.models.ldap_config_manager import LDAPConfigManager

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_user():
    """
    Main route for user search functionality. Handles both the search form display
    and the actual search functionality.
    """
    result = None
    search_results = None
    prefill_cn = request.args.get('cn', '')
    prefill_workforceID = request.args.get('workforceID', '')
    prefill_FavvNatNr = request.args.get('FavvNatNr', '')
    prefill_fullName = request.args.get('fullName', '')
    
    # Récupérer la source LDAP
    ldap_source = request.args.get('source', 'meta')
    if request.method == 'POST':
        ldap_source = request.form.get('ldap_source', ldap_source)
    
    # Créer une instance du modèle LDAP avec la source spécifiée
    ldap_model = EDIRModel(source=ldap_source)
    
    # Récupérer le nom de la directory depuis la configuration
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    if request.method == 'POST':
        # Get search parameters from form
        search_term = request.form.get('search_term', '')
        search_type = request.form.get('search_type', '')  # 'cn', 'workforceID', 'FavvNatNr', 'fullName'
        
        # Validate input
        if not search_term or not search_type:
            flash('Please provide a search term and type.', 'warning')
            return render_template('search.html', 
                                   result=None,
                                   search_results=None,
                                   prefill_cn=prefill_cn, 
                                   prefill_workforceID=prefill_workforceID, 
                                   prefill_FavvNatNr=prefill_FavvNatNr,
                                   prefill_fullName=prefill_fullName,
                                   ldap_source=ldap_source,
                                   ldap_name=ldap_name)
        
        # Check if wildcard search is needed (for fullName or cn)
        has_wildcard = '*' in search_term and search_type in ['fullName', 'cn']
        
        if has_wildcard:
            # Use return_list=True for wildcard searches to get multiple results
            search_results = ldap_model.search_user_final(search_term, search_type, return_list=True)
            
            # If only one result is found, show it directly
            if len(search_results) == 1:
                result = ldap_model.search_user_final(search_results[0]['dn'])
                search_results = None
            elif len(search_results) == 0:
                flash('No users found matching your criteria.', 'danger')
        else:
            # Regular search for a specific user
            result = ldap_model.search_user_final(search_term, search_type)
            
            # Check result and set appropriate message
            if not result:
                flash('User not found.', 'danger')
    
    # If we have a DN parameter, try to get user details
    elif request.args.get('dn'):
        user_dn = request.args.get('dn')
        result = ldap_model.search_user_final(user_dn)
            
    # Render the template with appropriate data
    return render_template('search.html', 
                           result=result,
                           search_results=search_results,
                           prefill_cn=prefill_cn, 
                           prefill_workforceID=prefill_workforceID, 
                           prefill_FavvNatNr=prefill_FavvNatNr,
                           prefill_fullName=prefill_fullName,
                           ldap_source=ldap_source,
                           ldap_name=ldap_name)