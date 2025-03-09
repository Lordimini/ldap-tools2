from ldap3 import Server, Connection, ALL, MODIFY_ADD, SUBTREE
from flask_app.config.ldap_config import ldap_login_config
from flask import redirect, url_for, flash, json, render_template
import unicodedata

class LDAPModel:
    def __init__(self):
        self.ldap_server = ldap_login_config['ldap_server']
        self.bind_dn = ldap_login_config['bind_dn']
        self.password = ldap_login_config['bind_password']
        self.base_dn = ldap_login_config['base_dn']
        self.actif_users_dn = ldap_login_config['actif_users_dn']
        self.out_users_dn = ldap_login_config['out_users_dn']
        self.all_users_dn = ldap_login_config['all_users_dn']
        self.template_dn = ldap_login_config['template_dn']
        self.usercreation_dn = ldap_login_config['usercreation_dn']
        self.admin_group_dn = ldap_login_config['admin_group_dn']
        self.reader_group_dn = ldap_login_config['reader_group_dn']
        self.role_base_dn = ldap_login_config['role_base_dn']
        self.resource_base_dn = ldap_login_config['resource_base_dn']
        self.app_base_dn = ldap_login_config['app_base_dn']
        self.toprocess_users_dn = ldap_login_config['toprocess_users_dn']
        
    def authenticate(self, username, password):
        user_dn = f'cn={username},{self.actif_users_dn}'
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
    
    def authenticate_admin(self, username, password):
        try:
            server = Server(self.ldap_server, get_info=ALL)
            conn = Connection(server, username, password=password, auto_bind=True)
            return conn
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None

    
####################################################################
####################################################################
####################################################################

    def search_user(self, search_term, search_type):
        pass     
####################################################################
####################################################################
####################################################################


    def get_group_users(self, group_name):
            pass
####################################################################
####################################################################
####################################################################        

    def get_role_users(self, role_cn):
        pass        
####################################################################
####################################################################
####################################################################
    
    def get_role_groups(self, role_cn):
        pass
        

####################################################################
####################################################################
####################################################################
    
    
    def view_role(self, dn):
        pass
   
  
    def get_service_users(self, service_name):
        pass
            
            
        
        
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

    def _get_connection(self):
        """
        Obtenir une connexion LDAP déjà établie pour réutilisation.
        """
        # On pourrait implémenter un pool de connexions ici
        return Connection(
            self.ldap_server,
            user=self.bind_dn,
            password=self.password,
            auto_bind=True
        )   
    
    
    

####################################################################
####################################################################
####################################################################

    def get_ldap_children(self, current_dn):
        pass
    def generate_unique_cn(self, given_name, sn):
        pass  
    def create_user(self, cn, ldap_attributes, template_details=None):
        pass 
    
    def check_name_combination_exists(self, given_name, sn):
        pass
        
    
    def get_template_details(self, template_cn):
        pass

    def generate_password_from_cn(self, cn):
        pass
    
    def check_favvnatnr_exists(self, favvnatnr):
        pass 
        
    def get_managers(self):
        pass
        
    
    def get_total_users_count(self):
        pass

    def get_recent_logins_count(self, days=7):
        pass
    def get_disabled_accounts_count(self):
        pass

    def get_inactive_users_count(self, months=3):
        pass
    
    def get_expired_password_users_count(self):
        pass
    
    def get_never_logged_in_users_count(self):
        pass
    
    def add_user_to_group(self, user_dn, group_dn):
        pass
    
    def get_pending_users(self):
        pass        
    def get_user_details(self, user_dn):
        pass
    
    def complete_user_creation(self, user_dn, target_container, attributes, groups, set_password=False):
        pass
            
    def delete_user(self, user_dn):
        pass
    
    # Ces méthodes doivent être ajoutées à la classe LDAPModel dans flask_app/models/ldap.py

    def search_active_users(self, search_term, search_type):
        pass
    def search_user_by_dn(self, user_dn):
        pass 
    
    def update_user(self, user_dn, attributes, groups_to_add=None, groups_to_remove=None, reset_password=False, expire_password=False, target_container=None, change_reason=None):
        pass 
    def remove_user_from_group(self, user_dn, group_dn):
        

    def get_dashboard_stats(self):
        pass
    
#########################################################
##### Auto Complete Section #############################
#########################################################
        
        
    def get_group_users_by_dn(self, group_dn, group_name=None):
        pass