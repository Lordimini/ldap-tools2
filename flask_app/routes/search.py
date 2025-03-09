from flask import Blueprint, render_template, request, flash, session, url_for, redirect
from flask_app.models.meta_model import METAModel
from flask_app.utils.ldap_utils import login_required

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_user():
    """
    Main route for user search functionality. Handles both the search form display
    and the actual search functionality.
    """
    result = None
    prefill_cn = request.args.get('cn', '')
    prefill_workforceID = request.args.get('workforceID', '')
    prefill_FavvNatNr = request.args.get('FavvNatNr', '')
    prefill_fullName = request.args.get('fullName', '')
    
    if request.method == 'POST':
        # Get search parameters from form
        search_term = request.form.get('search_term', '')
        search_type = request.form.get('search_type', '')  # 'cn', 'workforceID', 'FavvNatNr', 'fullName'
        
        # Validate input
        if not search_term or not search_type:
            flash('Please provide a search term and type.', 'warning')
            return render_template('search.html', 
                                   result=None, 
                                   prefill_cn=prefill_cn, 
                                   prefill_workforceID=prefill_workforceID, 
                                   prefill_FavvNatNr=prefill_FavvNatNr,
                                   prefill_fullName=prefill_fullName)
        
        # Perform the search
        ldap_model = METAModel()
        result = ldap_model.search_user(search_term, search_type)
        
        # Check result and set appropriate message
        if not result:
            flash('User not found.', 'danger')
    
    # If we have a DN parameter, try to get user details
    elif request.args.get('dn'):
        ldap_model = METAModel()
        user_dn = request.args.get('dn')
        result = ldap_model.search_user_by_dn(user_dn)
            
    # Render the template with appropriate data
    return render_template('search.html', 
                           result=result, 
                           prefill_cn=prefill_cn, 
                           prefill_workforceID=prefill_workforceID, 
                           prefill_FavvNatNr=prefill_FavvNatNr,
                           prefill_fullName=prefill_fullName)