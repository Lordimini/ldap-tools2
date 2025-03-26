# flask_app/models/ldap/dashboard.py
from .base import LDAPBase
from ldap3 import Connection
from datetime import datetime, timedelta
from flask_app.models.ldap.users.user_crud import LDAPUserCRUD

class LDAPDashboardMixin(LDAPBase):
    def _get_user_crud(self):
        config = {
            'ldap_server': self.ldap_server,
            'bind_dn': self.bind_dn,
            'bind_password': self.password,
            'base_dn': self.base_dn,
            'actif_users_dn': self.actif_users_dn,
            'out_users_dn': self.out_users_dn,
            'all_users_dn': self.all_users_dn,
            'template_dn': self.template_dn
            # Omission des propriétés non nécessaires comme 'toprocess_users_dn'
        }
        return LDAPUserCRUD(config)
    
    
    def get_dashboard_stats(self):
        return {
            'total_users': self.get_total_users_count(),
            'recent_logins': self.get_recent_logins_count(),
            'disabled_accounts': self.get_disabled_accounts_count()
        }
        
    def get_total_users_count(self):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            search_base = self.actif_users_dn
            search_filter = '(objectClass=Person)'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn'],
                        paged_size=1000)
                        
            total_entries = len(conn.entries)
            
            # Si la recherche est paginée, récupérer toutes les pages
            cookie = conn.result.get('controls', {}).get('1.2.840.113556.1.4.319', {}).get('value', {}).get('cookie')
            while cookie:
                conn.search(search_base=search_base,
                            search_filter=search_filter,
                            search_scope='SUBTREE',
                            attributes=['cn'],
                            paged_size=1000,
                            paged_cookie=cookie)
                total_entries += len(conn.entries)
                cookie = conn.result.get('controls', {}).get('1.2.840.113556.1.4.319', {}).get('value', {}).get('cookie')
            
            conn.unbind()
            return total_entries
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs: {str(e)}")
            return 0
        
    def get_recent_logins_count(self, days=7):
        try:
            user_crud = self._get_user_crud()
            
            # Calculer la date limite (timestamp en format GeneralizedTime)
            limit_date = datetime.now() - timedelta(days=days)
            limit_timestamp = limit_date.strftime("%Y%m%d%H%M%SZ")
            
            # Définir le filtre LDAP pour les connexions récentes
            search_filter = f'(&(objectClass=Person)(loginTime>={limit_timestamp}))'
           
            options = {
                'container': 'active',
                'return_list': True,
                'attributes': ['cn', 'loginTime']
            }
            
            # Obtenir les utilisateurs avec une connexion récente
            recent_users = user_crud.get_user(search_filter, options)
            
            # Retourner le nombre d'utilisateurs trouvés
            return len(recent_users)
            
        except Exception as e:
            print(f"Erreur lors du comptage des connexions récentes: {str(e)}")
            return 0

        
    def get_disabled_accounts_count(self):
        try:
            user_crud = self._get_user_crud()
            
            # conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs avec loginDisabled=TRUE
            # search_base = self.actif_users_dn
            search_filter = '(&(objectClass=Person)(loginDisabled=TRUE))'
            
            # conn.search(search_base=search_base,
            #             search_filter=search_filter,
            #             search_scope='SUBTREE',
            #             attributes=['cn'])
            options = {
                'container': 'active',
                'return_list': True,
                'attributes': 'cn'
            }
            disabled_count = user_crud.get_user(search_filter, options)
            
            return len(disabled_count)
            
        except Exception as e:
            print(f"Erreur lors du comptage des comptes désactivés: {str(e)}")
            return 0
        
    def get_inactive_users_count(self, months=3):
        try:
            # Calculer la date limite (timestamp en format GeneralizedTime)
            limit_date = datetime.now() - timedelta(days=30*months)
            limit_timestamp = limit_date.strftime("%Y%m%d%H%M%SZ")
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs actifs mais avec une ancienne date de connexion
            search_base = self.actif_users_dn
            search_filter = f'(&(objectClass=Person)(loginDisabled=FALSE)(loginTime<={limit_timestamp}))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn', 'loginTime'])
            
            inactive_users = len(conn.entries)
            
            conn.unbind()
            return inactive_users
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs inactifs: {str(e)}")
            return 0
    
    def get_expired_password_users_count(self):
        try:
            # Obtenir la date actuelle au format LDAP GeneralizedTime
            current_date = datetime.now().strftime("%Y%m%d%H%M%SZ")
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs actifs avec un mot de passe expiré
            search_base = self.actif_users_dn
            search_filter = f'(&(objectClass=Person)(loginDisabled=FALSE)(passwordExpirationTime<={current_date}))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn', 'passwordExpirationTime'])
            
            expired_password_users = len(conn.entries)
            
            conn.unbind()
            return expired_password_users
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs avec mot de passe expiré: {str(e)}")
            return 0
        
    def get_never_logged_in_users_count(self):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs actifs sans attribut loginTime
            search_base = self.actif_users_dn
            search_filter = '(&(objectClass=Person)(loginDisabled=FALSE)(!(loginTime=*)))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn'])
            
            never_logged_in = len(conn.entries)
            
            conn.unbind()
            return never_logged_in
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs n'ayant jamais effectué de connexion: {str(e)}")
            return 0
  