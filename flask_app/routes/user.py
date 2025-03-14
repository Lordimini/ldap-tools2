from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_app.models.edir_model import EDIRModel
from flask_app.utils.ldap_utils import login_required
from flask_app.models.ldap_config_manager import LDAPConfigManager

user_bp = Blueprint('user', __name__)

@user_bp.route('/user_browser', methods=['GET'])
@login_required
def user_browser():
    try:
        # Get the current DN from the query string (default to the base container)
        current_dn = request.args.get('dn', 'ou=sync,o=copy')
        page_size = 10  # Number of entries per page
        page_cookie = request.args.get('page_cookie', None)  # Cookie for tracking pages
        
        # Get LDAP source with proper fallback sequence
        ldap_source = request.args.get('source')
        
        # If not in query params, get from session with default fallback
        if not ldap_source:
            ldap_source = session.get('ldap_source', 'meta')
        
        # Make sure session is updated with current source
        session['ldap_source'] = ldap_source
        session.modified = True
        
        # Create EDIR model with the appropriate source
        ldap_model = EDIRModel(source=ldap_source)
        
        # Get LDAP name for display purposes
        config = LDAPConfigManager.get_config(ldap_source)
        ldap_name = config.get('LDAP_name', 'META')
        
        children, total_entries, page_cookie = ldap_model.get_user_children(current_dn)
        
        return render_template('user_browser.html', 
                               current_dn=current_dn, 
                               children=children, 
                               total_entries=total_entries, 
                               page_cookie=page_cookie,
                               ldap_source=ldap_source,
                               ldap_name=ldap_name)
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('dashboard.dashboard', source=ldap_source))