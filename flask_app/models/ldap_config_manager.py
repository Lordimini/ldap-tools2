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
        pass
    
    def init_app(self, app):
        pass
    
    @classmethod
    def get_config(cls, source=None):
        if source is None:
            source = cls.get_active_config_name()
        
        source = source.lower()
        
        if source in cls.configs:
            return cls.configs[source]
        else:
            return cls.configs[cls.default_source]
    
    @classmethod
    def get_available_configs(cls):
        return list(cls.configs.keys())
    
    @classmethod
    def get_active_config_name(cls):
        return session.get('ldap_source', cls.default_source)
    
    @classmethod
    def set_active_config(cls, source):
        if source in cls.configs:
            session['ldap_source'] = source
            return True
        return False