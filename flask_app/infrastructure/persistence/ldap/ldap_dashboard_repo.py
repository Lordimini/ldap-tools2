# flask_app/infrastructure/persistence/ldap/ldap_dashboard_repo.py
from typing import Dict, Any, List
from datetime import datetime, timedelta
from flask_app.domain.repositories.dashboard_repository import DashboardRepository
from flask_app.infrastructure.persistence.ldap.ldap_connection import LDAPConnection


class LDAPDashboardRepository(DashboardRepository):
    """
    Implémentation LDAP pour le repository de tableau de bord.
    Cette classe implémente les méthodes définies dans l'interface DashboardRepository
    en utilisant le protocole LDAP pour collecter des statistiques sur les utilisateurs.
    """
    
    def __init__(self, connection_provider):
        """
        Initialise le repository avec un fournisseur de connexion LDAP.
        
        Args:
            connection_provider: Fournisseur de connexion LDAP qui gère le pool de connexions
        """
        self.connection_provider = connection_provider
        self.config = connection_provider.get_config()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques générales pour le tableau de bord.
        
        Returns:
            Dictionnaire contenant toutes les statistiques
        """
        return {
            'total_users': self.get_total_users_count(),
            'disabled_accounts': self.get_disabled_accounts_count(),
            'inactive_users': self.get_inactive_users_count(),
            'expired_password_users': self.get_expired_password_users_count(),
            'never_logged_in_users': self.get_never_logged_in_users_count(),
            'recent_logins': self.get_recent_logins_count()
        }
    
    def get_total_users_count(self) -> int:
        """
        Récupère le nombre total d'utilisateurs.
        
        Returns:
            Nombre d'utilisateurs
        """
        conn = self.connection_provider.get_connection()
        try:
            # Recherche tous les utilisateurs dans la base spécifiée
            search_base = self.config['actif_users_dn']
            search_filter = '(objectClass=Person)'
            
            # Effectuer la recherche avec l'option paged_size pour gérer un grand nombre d'utilisateurs
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn'],
                paged_size=1000
            )
            
            # Compter le nombre total d'entrées
            total_entries = len(conn.entries)
            
            # Si la recherche est paginée, récupérer toutes les pages
            cookie = conn.result.get('controls', {}).get('1.2.840.113556.1.4.319', {}).get('value', {}).get('cookie')
            while cookie:
                conn.search(
                    search_base=search_base,
                    search_filter=search_filter,
                    search_scope='SUBTREE',
                    attributes=['cn'],
                    paged_size=1000,
                    paged_cookie=cookie
                )
                total_entries += len(conn.entries)
                cookie = conn.result.get('controls', {}).get('1.2.840.113556.1.4.319', {}).get('value', {}).get('cookie')
            
            return total_entries
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs: {str(e)}")
            return 0
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_recent_logins_count(self, days: int = 7) -> int:
        """
        Récupère le nombre d'utilisateurs qui se sont connectés récemment.
        
        Args:
            days: Nombre de jours à considérer
            
        Returns:
            Nombre d'utilisateurs récemment connectés
        """
        conn = self.connection_provider.get_connection()
        try:
            # Calculer la date limite (timestamp au format GeneralizedTime)
            limit_date = datetime.now() - timedelta(days=days)
            limit_timestamp = limit_date.strftime("%Y%m%d%H%M%SZ")
            
            # Rechercher les utilisateurs avec une date de connexion récente
            search_base = self.config['actif_users_dn']
            search_filter = f'(&(objectClass=Person)(loginTime>={limit_timestamp}))'
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn', 'loginTime']
            )
            
            recent_logins = len(conn.entries)
            
            return recent_logins
            
        except Exception as e:
            print(f"Erreur lors du comptage des connexions récentes: {str(e)}")
            return 0
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_disabled_accounts_count(self) -> int:
        """
        Récupère le nombre de comptes désactivés.
        
        Returns:
            Nombre de comptes désactivés
        """
        conn = self.connection_provider.get_connection()
        try:
            # Rechercher les utilisateurs avec loginDisabled=TRUE
            search_base = self.config['actif_users_dn']
            search_filter = '(&(objectClass=Person)(loginDisabled=TRUE))'
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn']
            )
            
            disabled_count = len(conn.entries)
            
            return disabled_count
            
        except Exception as e:
            print(f"Erreur lors du comptage des comptes désactivés: {str(e)}")
            return 0
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_inactive_users_count(self, months: int = 3) -> int:
        """
        Récupère le nombre d'utilisateurs actifs qui ne se sont pas connectés depuis X mois.
        
        Args:
            months: Nombre de mois d'inactivité
            
        Returns:
            Nombre d'utilisateurs inactifs
        """
        conn = self.connection_provider.get_connection()
        try:
            # Calculer la date limite (timestamp au format GeneralizedTime)
            limit_date = datetime.now() - timedelta(days=30*months)
            limit_timestamp = limit_date.strftime("%Y%m%d%H%M%SZ")
            
            # Rechercher les utilisateurs actifs mais avec une ancienne date de connexion
            search_base = self.config['actif_users_dn']
            search_filter = f'(&(objectClass=Person)(loginDisabled=FALSE)(loginTime<={limit_timestamp}))'
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn', 'loginTime']
            )
            
            inactive_users = len(conn.entries)
            
            return inactive_users
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs inactifs: {str(e)}")
            return 0
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_expired_password_users_count(self) -> int:
        """
        Récupère le nombre d'utilisateurs actifs dont le mot de passe est expiré.
        
        Returns:
            Nombre d'utilisateurs avec mot de passe expiré
        """
        conn = self.connection_provider.get_connection()
        try:
            # Obtenir la date actuelle au format LDAP GeneralizedTime
            current_date = datetime.now().strftime("%Y%m%d%H%M%SZ")
            
            # Rechercher les utilisateurs actifs avec un mot de passe expiré
            search_base = self.config['actif_users_dn']
            search_filter = f'(&(objectClass=Person)(loginDisabled=FALSE)(passwordExpirationTime<={current_date}))'
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn', 'passwordExpirationTime']
            )
            
            expired_password_users = len(conn.entries)
            
            return expired_password_users
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs avec mot de passe expiré: {str(e)}")
            return 0
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_never_logged_in_users_count(self) -> int:
        """
        Récupère le nombre d'utilisateurs actifs qui ne se sont jamais connectés.
        
        Returns:
            Nombre d'utilisateurs qui ne se sont jamais connectés
        """
        conn = self.connection_provider.get_connection()
        try:
            # Rechercher les utilisateurs actifs sans attribut loginTime
            search_base = self.config['actif_users_dn']
            search_filter = '(&(objectClass=Person)(loginDisabled=FALSE)(!(loginTime=*)))'
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn']
            )
            
            never_logged_in = len(conn.entries)
            
            return never_logged_in
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs n'ayant jamais effectué de connexion: {str(e)}")
            return 0
        finally:
            self.connection_provider.release_connection(conn)