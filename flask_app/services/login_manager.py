from flask_login import LoginManager, current_user
from flask import g, session, flash, redirect, url_for, request
from flask_app.models.user_model import User
from flask_app.models.ldap_model import LDAPModel
import functools

login_manager = LoginManager()

def init_login_manager(app):
    """Initialize the login manager with the Flask app"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Set up the user loader
    @login_manager.user_loader
    def load_user(username):
        """Load user from session"""
        if not username:
            return None
        
        # Store user in g for easy access
        if 'user_data' in session:
            user_data = session['user_data']
            ldap_source = session.get('ldap_source', 'meta')
            user = User.from_ldap_data(username, user_data, ldap_source)
            return user
        
        return None
    
    # Before request handler to set up g.user
    @app.before_request
    def before_request():
        g.user = current_user
        # Add LDAP source to g
        g.ldap_source = session.get('ldap_source', 'meta')
        
        # If user is logged in, ensure LDAP config is set for current user
        if current_user.is_authenticated:
            g.user_roles = current_user.roles
            
            # Set LDAP name for display
            ldap_source = current_user.ldap_source
            g.ldap_name = app.ldap_config_manager.get_config(ldap_source).get('LDAP_name', 'LDAP')

def authenticate_user(username, password, ldap_source='meta'):
    """Authenticate a user against LDAP and create User object"""
    try:
        # Create LDAP model for the specified source
        ldap_model = LDAPModel(source=ldap_source)
        
        # Authenticate against LDAP
        conn = ldap_model.authenticate(username, password)
        if not conn:
            return None
        
        # Check for role-specific group memberships
        is_admin_member = False
        is_reader_member = False
        is_oci_admin_member = False
        is_stag_admin_member = False
        
        # Get group DNs from LDAP model or config
        admin_group_dn = ldap_model.admin_group_dn
        reader_group_dn = ldap_model.reader_group_dn
        oci_admin_group_dn = ldap_model.oci_admin_group_dn  # You'll need to add these
        # stag_admin_group_dn = ldap_model.stag_admin_group_dn  # properties to LDAPModel
        
        # Check admin group membership
        if admin_group_dn:
            conn.search(admin_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_admin_member = True
        
        # Check reader group membership
        if reader_group_dn:
            conn.search(reader_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_reader_member = True
        
        # Check OCI admin group membership
        if oci_admin_group_dn:
            conn.search(oci_admin_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_oci_admin_member = True
        
        # Get user details
        options = {
            'search_type': 'cn',
            'container': 'active',
            'simplified': True 
        }
        user_data = ldap_model.get_user(username, options)
        
        
        if not user_data:
            return None
            
        # Add group membership information
        user_data['is_admin_member'] = is_admin_member
        user_data['is_reader_member'] = is_reader_member
        user_data['is_oci_admin_member'] = is_oci_admin_member
        user_data['is_stag_admin_member'] = is_stag_admin_member
        user_data['admin_group_dn'] = admin_group_dn
        user_data['reader_group_dn'] = reader_group_dn
        user_data['oci_admin_group_dn'] = oci_admin_group_dn
        # user_data['stag_admin_group_dn'] = stag_admin_group_dn
        
        # Store user data in session for later retrieval
        session['user_data'] = user_data
        session['ldap_source'] = ldap_source
        
        # Create and return user
        user = User.from_ldap_data(username, user_data, ldap_source)
        
        return user
    
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None