# flask_app/models/ldap_model.py
from flask_app.models.ldap_config_manager import LDAPConfigManager
from flask_app.models.ldap import (
    LDAPUserMixin,
    LDAPGroupMixin,
    LDAPRoleMixin,
    LDAPServiceMixin,
    LDAPAutocompleteMixin,
    LDAPDashboardMixin,
    LDAPTemplate
)
from ldap3 import Server, Connection, ALL

class LDAPModel(
    LDAPUserMixin,
    LDAPGroupMixin,
    LDAPRoleMixin,
    LDAPServiceMixin,
    LDAPAutocompleteMixin,
    LDAPDashboardMixin,
    LDAPTemplate
):
    def __init__(self, source='meta'):
        """
        Initialise le modèle avec la configuration correspondant à la source demandée.
        
        Args:
            source (str): Identifiant de la source LDAP ('meta','idme', ad-prod, ad-edu ou ad-teste)
        """
        config = LDAPConfigManager.get_config(source)
        self.source = source
        super().__init__(config)
        
    def authenticate(self, username, password):
        # user_dn = f'cn={username},{self.actif_users_dn}'
        user_dn = self.get_user_dn (username)
        try:
            # Set up the server with a timeout
            server = Server(self.ldap_server, get_info=ALL, connect_timeout=10)
            
            # Connect with timeout parameters
            conn = Connection(
                server, 
                user=user_dn, 
                password=password, 
                auto_bind=True,
                check_names=True,
                read_only=False,
                client_strategy='SYNC',
                receive_timeout=10
            )
            
            # If we get here without an exception, authentication succeeded
            return conn
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None
    
    def get_user_dn(self, username):
    
        try:
            # ldap_model = LDAPModel(source=ldap_source)
            conn = self.authenticate_admin(self.bind_dn, self.password)
            if not conn:
                    return None
            user_dn = None
            search_base = self.actif_users_dn
            search_filter = f'(cn={username})'
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn']
            )
            if conn.entries:
                    user_dn = conn.entries[0].entry_dn
            conn.unbind()
            
            if not user_dn:
                print(f"User '{username}' not found in any container")
                return None
            return user_dn    
        
        except Exception as e:
            print(f"Je trouve pas le user: {str(e)}")
            return None
    
    def authenticate_admin(self, username, password):
        try:
            server = Server(self.ldap_server, get_info=ALL)
            conn = Connection(server, username, password=password, auto_bind=True)
            return conn
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None