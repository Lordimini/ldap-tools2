# flask_app/models/ldap_config_manager.py
from flask import session
from flask_app.config.meta_config import meta_login_config
from flask_app.config.idme_config import idme_login_config

class LDAPConfigManager:
    # Class-level configs dictionary to be accessible from static methods
    configs = {
        'meta': meta_login_config,
        'idme': idme_login_config
    }
    default_source = 'meta'
    
    def __init__(self):
        # Instance initialization can remain empty as we're using class variables
        pass
    
    def init_app(self, app):
        """
        Initialise le gestionnaire avec l'application Flask
        """
        # Rien de spécial à faire ici pour l'instant
        pass
    
    @classmethod
    def get_config(cls, source=None):
        """
        Retourne la configuration LDAP appropriée selon la source demandée.
        Si source est None, utilise la source active.
        
        Args:
            source (str, optional): Identifiant de la source LDAP ('meta' ou 'idme')
            
        Returns:
            dict: Configuration LDAP correspondante
        """
        if source is None:
            source = cls.get_active_config_name()
        
        source = source.lower()
        
        if source in cls.configs:
            return cls.configs[source]
        else:
            # Par défaut, retourner la source par défaut
            return cls.configs[cls.default_source]
    
    @classmethod
    def get_available_configs(cls):
        """
        Retourne la liste des configurations LDAP disponibles
        
        Returns:
            list: Liste des identifiants de configurations disponibles
        """
        return list(cls.configs.keys())
    
    @classmethod
    def get_active_config_name(cls):
        """
        Retourne l'identifiant de la configuration LDAP active
        
        Returns:
            str: Identifiant de la configuration active
        """
        return session.get('ldap_source', cls.default_source)
    
    @classmethod
    def set_active_config(cls, source):
        """
        Définit la configuration LDAP active
        
        Args:
            source (str): Identifiant de la source LDAP à activer
            
        Returns:
            bool: True si la source existe, False sinon
        """
        if source in cls.configs:
            session['ldap_source'] = source
            return True
        return False