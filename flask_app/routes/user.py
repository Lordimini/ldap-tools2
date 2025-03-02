from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_app.models.ldap import LDAPModel
from flask_app.utils.ldap_utils import login_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/user_browser', methods=['GET'])
@login_required
def user_browser():
    try:
        # Get the current DN from the query string (default to the base container)
        current_dn = request.args.get('dn', 'ou=sync,o=copy')
        page_size = 10  # Number of entries per page
        page_cookie = request.args.get('page_cookie', None)  # Cookie for tracking pages
    
        ldap_model = LDAPModel()
        children, total_entries, page_cookie = ldap_model.get_user_children(current_dn)
        return render_template('user_browser.html', current_dn=current_dn, children=children, total_entries=total_entries, page_cookie=page_cookie)
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
