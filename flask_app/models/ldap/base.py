# flask_app/models/ldap/base.py
from ldap3 import Server, Connection, ALL


class LDAPBase:
    def __init__(self, config):
        self.ldap_server = config['ldap_server']
        self.bind_dn = config['bind_dn']
        self.password = config['bind_password']
        self.base_dn = config['base_dn']
        self.actif_users_dn = config['actif_users_dn']
        self.out_users_dn = config['out_users_dn']
        self.all_users_dn = config['all_users_dn']
        self.template_dn = config['template_dn']
        self.usercreation_dn = config['usercreation_dn']
        self.admin_group_dn = config['admin_group_dn']
        self.reader_group_dn = config['reader_group_dn']
        self.oci_admin_group_dn = config.get('oci_admin_group_dn', '')  
        self.role_base_dn = config['role_base_dn']
        self.resource_base_dn = config['resource_base_dn']
        self.app_base_dn = config['app_base_dn']
        self.toprocess_users_dn = config['toprocess_users_dn']
    
    def _get_connection(self):
        """
        Obtenir une connexion LDAP déjà établie pour réutilisation.
        """
        return Connection(
            self.ldap_server,
            user=self.bind_dn,
            password=self.password,
            auto_bind=True
        )

    def _escape_ldap_filter(self, input_string):
        """
        Échapper les caractères spéciaux dans un filtre LDAP.
        """
        if not input_string:
            return ""
        
        # Échapper les caractères spéciaux selon la RFC 2254
        special_chars = {
            '\\': r'\5c',
            '*': r'\2a',
            '(': r'\28',
            ')': r'\29',
            '\0': r'\00'
        }
        
        result = input_string
        for char, replacement in special_chars.items():
            result = result.replace(char, replacement)
        
        return result