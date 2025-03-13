# flask_app/models/ldap_config_manager.py
from flask import session
from flask_app.config.meta_config import meta_login_config
from flask_app.config.idme_config import idme_login_config

class LDAPConfigManager:
    def __init__(self):
        self.configs = {
            'meta': meta_login_config,
            'idme': idme_login_config
        }
        self.default_source = 'meta'
    
    def init_app(self, app):
        """
        Initialise le gestionnaire avec l'application Flask
        """
        # Rien de spécial à faire ici pour l'instant
        pass
    
    def get_config(self, source=None):
        """
        Retourne la configuration LDAP appropriée selon la source demandée.
        Si source est None, utilise la source active.
        
        Args:
            source (str, optional): Identifiant de la source LDAP ('meta' ou 'idme')
            
        Returns:
            dict: Configuration LDAP correspondante
        """
        if source is None:
            source = self.get_active_config_name()
        
        source = source.lower()
        
        if source in self.configs:
            return self.configs[source]
        else:
            # Par défaut, retourner la source par défaut
            return self.configs[self.default_source]
    
    def get_available_configs(self):
        """
        Retourne la liste des configurations LDAP disponibles
        
        Returns:
            list: Liste des identifiants de configurations disponibles
        """
        return list(self.configs.keys())
    
    def get_active_config_name(self):
        """
        Retourne l'identifiant de la configuration LDAP active
        
        Returns:
            str: Identifiant de la configuration active
        """
        return session.get('ldap_source', self.default_source)
    
    def set_active_config(self, source):
        """
        Définit la configuration LDAP active
        
        Args:
            source (str): Identifiant de la source LDAP à activer
            
        Returns:
            bool: True si la source existe, False sinon
        """
        if source in self.configs:
            session['ldap_source'] = source
            return True
        return False