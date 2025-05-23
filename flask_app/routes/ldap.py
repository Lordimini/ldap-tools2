from flask import Blueprint, render_template, request
from flask_app.models.ldap_model import LDAPModel
from flask_login import login_required

ldap_bp = Blueprint('ldap', __name__)

@ldap_bp.route('/ldap_browser', methods=['GET'])
@login_required
def ldap_browser():
    current_dn = request.args.get('dn', 'cn=RoleDefs,cn=RoleConfig,cn=AppConfig,cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY')
    ldap_model = LDAPModel()
    children, parent_dn = ldap_model.get_ldap_children(current_dn)
    return render_template('ldap_browser.html', current_dn=current_dn, children=children, parent_dn=parent_dn)