from flask import Blueprint, render_template, request, flash, session
from flask_login import login_required
from flask_app.models.ldap_config_manager import LDAPConfigManager
from flask_app.models.ldap.users import LDAPUserCRUD
# from flask_app.models.ldap.users import LDAPUserUtils

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
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    
    ldap_name = config.get('LDAP_name', 'META')
    
    user_crud = LDAPUserCRUD(config)
    
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
            
            options = {
                'search_type': search_type,
                'return_list': True,
                'container': 'active'  
            }
            search_results = user_crud.get_user(search_term, options)
            
            if len(search_results) == 1:
                
                options = {
                    'container': 'all'  
                }
                result = user_crud.get_user(search_results[0]['dn'], options)
                search_results = None
            elif len(search_results) == 0:
                flash('No users found matching your criteria.', 'danger')
        else:
            
            
            # REFACTORISATION #3: Recherche standard d'un utilisateur spécifique
            options = {
                'search_type': search_type,
                'container': 'all'  # Rechercher dans tous les conteneurs (actif, inactif)
            }
            result = user_crud.get_user(search_term, options)
            
            # Check result and set appropriate message
            if not result:
                flash('User not found.', 'danger')
    
    # If we have a DN parameter, try to get user details
    elif request.args.get('dn'):
        user_dn = request.args.get('dn')
        
        options = {
            'container': 'all'  # Rechercher dans tous les conteneurs (actif, inactif)
        }
        result = user_crud.get_user(user_dn, options)
    
    return render_template('search.html', 
                           result=result,
                           search_results=search_results,
                           prefill_cn=prefill_cn, 
                           prefill_workforceID=prefill_workforceID, 
                           prefill_FavvNatNr=prefill_FavvNatNr,
                           prefill_fullName=prefill_fullName,
                           ldap_source=ldap_source,
                           ldap_name=ldap_name)