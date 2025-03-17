# flask_app/models/ldap/dashboard.py
from .base import LDAPBase
from ldap3 import Connection

class LDAPDashboardMixin(LDAPBase):
    def get_dashboard_stats(self):
        """
        Récupère toutes les statistiques nécessaires pour le tableau de bord
        
        Returns:
            dict: Dictionnaire contenant toutes les statistiques
        """
        return {
            'total_users': self.get_total_users_count(),
            # 'total_groups': self.get_total_groups_count(),
            # 'total_roles': self.get_total_roles_count(),
            # 'services_count': self.get_services_count(),
            'recent_logins': self.get_recent_logins_count(),
            'disabled_accounts': self.get_disabled_accounts_count()
        }
        
    def get_total_users_count(self):
        """
        Récupère le nombre total d'utilisateurs dans la base de recherche
        
        Returns:
            int: Nombre total d'utilisateurs
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Recherche tous les utilisateurs dans la base spécifiée
            search_base = self.actif_users_dn
            search_filter = '(objectClass=Person)'
            
            # Effectuer la recherche avec l'option paged_size pour gérer un grand nombre d'utilisateurs
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn'],
                        paged_size=1000)
                        
            # Compter le nombre total d'entrées
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
        """
        Récupère le nombre d'utilisateurs qui se sont connectés récemment
        
        Args:
            days (int): Nombre de jours à considérer pour 'récent'
            
        Returns:
            int: Nombre d'utilisateurs récemment connectés
        """
        try:
            import time
            from datetime import datetime, timedelta
            
            # Calculer la date limite (timestamp en format GeneralizedTime)
            limit_date = datetime.now() - timedelta(days=days)
            limit_timestamp = limit_date.strftime("%Y%m%d%H%M%SZ")
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs avec une date de connexion récente
            search_base = self.actif_users_dn
            search_filter = f'(&(objectClass=Person)(loginTime>={limit_timestamp}))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn', 'loginTime'])
            
            recent_logins = len(conn.entries)
            
            conn.unbind()
            return recent_logins
            
        except Exception as e:
            print(f"Erreur lors du comptage des connexions récentes: {str(e)}")
            return 0

        
    def get_disabled_accounts_count(self):
        """
        Récupère le nombre de comptes désactivés
        
        Returns:
            int: Nombre de comptes désactivés
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs avec loginDisabled=TRUE
            search_base = self.actif_users_dn
            search_filter = '(&(objectClass=Person)(loginDisabled=TRUE))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn'])
            
            disabled_count = len(conn.entries)
            
            conn.unbind()
            return disabled_count
            
        except Exception as e:
            print(f"Erreur lors du comptage des comptes désactivés: {str(e)}")
            return 0
        
    def get_inactive_users_count(self, months=3):
        """
        Récupère le nombre d'utilisateurs actifs (loginDisabled=FALSE) qui ne se sont pas 
        connectés depuis plus de X mois
        
        Args:
            months (int): Nombre de mois d'inactivité
            
        Returns:
            int: Nombre d'utilisateurs inactifs
        """
        try:
            #import time
            from datetime import datetime, timedelta
            
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
        """
        Récupère le nombre d'utilisateurs actifs (loginDisabled=FALSE) dont le mot de passe est expiré
        
        Returns:
            int: Nombre d'utilisateurs avec mot de passe expiré
        """
        try:
            import time
            from datetime import datetime
            
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
        """
        Récupère le nombre d'utilisateurs actifs (loginDisabled=FALSE) qui n'ont jamais effectué de connexion
        (absence de l'attribut loginTime ou valeur vide)
        
        Returns:
            int: Nombre d'utilisateurs qui ne se sont jamais connectés
        """
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
    
    # ... autres méthodes liées au tableau de bord