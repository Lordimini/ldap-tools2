# flask_app/infrastructure/auth/ldap_authenticator.py
from typing import Optional, Dict, Any, Tuple
from flask_app.domain.repositories.user_repository import UserRepository
from flask_app.domain.models.user import User


class LDAPAuthenticator:
    """
    Service d'authentification qui utilise LDAP pour vérifier les identifiants utilisateur.
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialise l'authentificateur avec le repository utilisateur.
        
        Args:
            user_repository: Repository pour accéder aux données utilisateur
        """
        self.user_repository = user_repository
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Authentifie un utilisateur contre LDAP.
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            
        Returns:
            Tuple (succès, données utilisateur ou None si échec)
        """
        try:
            # Construire le DN de l'utilisateur en se basant sur le username
            user_data = self.user_repository.find_by_username(username)
            
            if not user_data:
                return False, None
            
            user_dn = user_data.get('dn')
            
            # Tenter de se connecter directement avec le DN de l'utilisateur et son mot de passe
            conn = self._get_connection(user_dn, password)
            
            if not conn:
                return False, None
            
            # Vérifier si l'utilisateur est membre des groupes admin ou reader
            admin_group_member = self._check_admin_membership(conn, user_dn)
            reader_group_member = self._check_reader_membership(conn, user_dn)
            
            # Ajouter l'information d'appartenance aux groupes
            user_data['is_admin_member'] = admin_group_member
            user_data['is_reader_member'] = reader_group_member
            
            # Fermer la connexion
            conn.unbind()
            
            return True, user_data
            
        except Exception as e:
            print(f"Erreur d'authentification: {str(e)}")
            return False, None
    
    def _get_connection(self, user_dn: str, password: str):
        """
        Établit une connexion LDAP avec les identifiants de l'utilisateur.
        
        Args:
            user_dn: DN de l'utilisateur
            password: Mot de passe de l'utilisateur
            
        Returns:
            Connexion LDAP ou None si échec
        """
        try:
            # Utiliser le repository utilisateur pour obtenir une connexion
            # Le repository doit gérer les détails de connexion LDAP
            conn = self.user_repository.authenticate(user_dn, password)
            return conn
        except Exception as e:
            print(f"Erreur de connexion LDAP: {str(e)}")
            return None
    
    def _check_admin_membership(self, conn, user_dn: str) -> bool:
        """
        Vérifie si l'utilisateur est membre du groupe admin.
        
        Args:
            conn: Connexion LDAP
            user_dn: DN de l'utilisateur
            
        Returns:
            True si l'utilisateur est membre du groupe admin, False sinon
        """
        try:
            # Obtenir le DN du groupe admin (cela devrait venir de la configuration)
            admin_group_dn = self.user_repository.config['admin_group_dn']
            
            # Vérifier si l'utilisateur est membre du groupe
            conn.search(
                search_base=admin_group_dn,
                search_filter=f'(member={user_dn})',
                search_scope='BASE'
            )
            
            return len(conn.entries) > 0
        except Exception as e:
            print(f"Erreur lors de la vérification de l'appartenance au groupe admin: {str(e)}")
            return False
    
    def _check_reader_membership(self, conn, user_dn: str) -> bool:
        """
        Vérifie si l'utilisateur est membre du groupe reader.
        
        Args:
            conn: Connexion LDAP
            user_dn: DN de l'utilisateur
            
        Returns:
            True si l'utilisateur est membre du groupe reader, False sinon
        """
        try:
            # Obtenir le DN du groupe reader (cela devrait venir de la configuration)
            reader_group_dn = self.user_repository.config['reader_group_dn']
            
            # Vérifier si l'utilisateur est membre du groupe
            conn.search(
                search_base=reader_group_dn,
                search_filter=f'(member={user_dn})',
                search_scope='BASE'
            )
            
            return len(conn.entries) > 0
        except Exception as e:
            print(f"Erreur lors de la vérification de l'appartenance au groupe reader: {str(e)}")
            return False