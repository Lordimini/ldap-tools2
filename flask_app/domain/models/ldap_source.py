# flask_app/domain/models/ldap_source.py
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LDAPSource:
    """
    Modèle représentant une source LDAP configurée.
    """
    name: str
    display_name: str
    server: str
    bind_dn: str
    bind_password: str
    base_dn: str
    actif_users_dn: str
    out_users_dn: str
    all_users_dn: str
    template_dn: str
    usercreation_dn: str
    toprocess_users_dn: str
    admin_group_dn: str
    reader_group_dn: str
    role_base_dn: str
    resource_base_dn: str
    app_base_dn: str
    is_default: bool = False
    
    @classmethod
    def from_config(cls, name: str, config: Dict[str, Any], is_default: bool = False) -> 'LDAPSource':
        """
        Crée une instance LDAPSource à partir d'une configuration.
        
        Args:
            name: Nom de la source LDAP
            config: Configuration LDAP
            is_default: Si cette source est la source par défaut
            
        Returns:
            Instance LDAPSource
        """
        return cls(
            name=name,
            display_name=config.get('LDAP_name', name.upper()),
            server=config.get('ldap_server', ''),
            bind_dn=config.get('bind_dn', ''),
            bind_password=config.get('bind_password', ''),
            base_dn=config.get('base_dn', ''),
            actif_users_dn=config.get('actif_users_dn', ''),
            out_users_dn=config.get('out_users_dn', ''),
            all_users_dn=config.get('all_users_dn', ''),
            template_dn=config.get('template_dn', ''),
            usercreation_dn=config.get('usercreation_dn', ''),
            toprocess_users_dn=config.get('toprocess_users_dn', ''),
            admin_group_dn=config.get('admin_group_dn', ''),
            reader_group_dn=config.get('reader_group_dn', ''),
            role_base_dn=config.get('role_base_dn', ''),
            resource_base_dn=config.get('resource_base_dn', ''),
            app_base_dn=config.get('app_base_dn', ''),
            is_default=is_default
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit la source LDAP en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données de la source LDAP
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'server': self.server,
            'bind_dn': self.bind_dn,
            'base_dn': self.base_dn,
            'actif_users_dn': self.actif_users_dn,
            'out_users_dn': self.out_users_dn,
            'all_users_dn': self.all_users_dn,
            'template_dn': self.template_dn,
            'usercreation_dn': self.usercreation_dn,
            'toprocess_users_dn': self.toprocess_users_dn,
            'admin_group_dn': self.admin_group_dn,
            'reader_group_dn': self.reader_group_dn,
            'role_base_dn': self.role_base_dn,
            'resource_base_dn': self.resource_base_dn,
            'app_base_dn': self.app_base_dn,
            'is_default': self.is_default
        }