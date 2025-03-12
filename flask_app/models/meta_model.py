# flask_app/models/meta_model.py
#from flask_app.config.meta_config import meta_login_config
from flask_app.models.ldap_config_manager import LDAPConfigManager
from flask_app.models.meta import (
    METAUserMixin,
    METAGroupMixin,
    METARoleMixin,
    METAServiceMixin,
    METAAutocompleteMixin,
    METADashboardMixin,
    METATemplate
)
from ldap3 import Server, Connection, ALL

class METAModel(
    METAUserMixin,
    METAGroupMixin,
    METARoleMixin,
    METAServiceMixin,
    METAAutocompleteMixin,
    METADashboardMixin,
    METATemplate
):
    def __init__(self, source='meta'):
        """
        Initialise le modèle avec la configuration correspondant à la source demandée.
        
        Args:
            source (str): Identifiant de la source LDAP ('meta' ou 'idme')
        """
        config = LDAPConfigManager.get_config(source)
        self.source = source
        super().__init__(config)
        
    def authenticate(self, username, password):
        user_dn = f'cn={username},{self.actif_users_dn}'
        try:
            # Set up the server with a timeout
            server = Server(self.meta_server, get_info=ALL, connect_timeout=10)
            
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
    
    def authenticate_admin(self, username, password):
        try:
            server = Server(self.meta_server, get_info=ALL)
            conn = Connection(server, username, password=password, auto_bind=True)
            return conn
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None