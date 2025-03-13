# flask_app/models/ldap_config_manager.py
from flask_app.config.meta_config import meta_login_config
from flask_app.config.idme_config import idme_login_config

class LDAPConfigManager:
    @staticmethod
    def get_config(source='meta'):
        """
        Retourne la configuration LDAP appropriée selon la source demandée.
        
        Args:
            source (str): Identifiant de la source LDAP ('meta' ou 'idme')
            
        Returns:
            dict: Configuration LDAP correspondante
        """
        source = source.lower()
        
        if source == 'meta':
            return meta_login_config
        elif source == 'idme':
            return idme_login_config
        else:
            # Par défaut, retourner META
            return meta_login_config
    