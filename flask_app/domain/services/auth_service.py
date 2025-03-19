# flask_app/domain/services/auth_service.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

class AuthService(ABC):
    """
    Interface pour les services d'authentification et d'autorisation.
    """
    
    @abstractmethod
    def authenticate(self, username: str, password: str, ldap_source: str = 'meta') -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Authentifie un utilisateur contre LDAP.
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            ldap_source: Source LDAP à utiliser ('meta', 'idme', etc.)
            
        Returns:
            Tuple (succès, données utilisateur ou None si échec)
        """
        pass
    
    @abstractmethod
    def get_user_permissions(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détermine les permissions d'un utilisateur en fonction de ses groupes LDAP.
        
        Args:
            user_data: Données utilisateur issues de LDAP
            
        Returns:
            Dictionnaire avec rôles et permissions
        """
        pass
    
    @abstractmethod
    def is_authorized(self, user_data: Dict[str, Any], permission: str = None, role: str = None) -> bool:
        """
        Vérifie si un utilisateur a une permission ou un rôle spécifique.
        
        Args:
            user_data: Données utilisateur
            permission: Permission à vérifier (optionnel)
            role: Rôle à vérifier (optionnel)
            
        Returns:
            True si autorisé, False sinon
        """
        pass
    
    @abstractmethod
    def get_active_ldap_source(self) -> str:
        """
        Récupère la source LDAP active pour l'utilisateur courant.
        
        Returns:
            Identifiant de la source LDAP
        """
        pass
    
    @abstractmethod
    def set_active_ldap_source(self, source: str) -> bool:
        """
        Définit la source LDAP active pour l'utilisateur courant.
        
        Args:
            source: Identifiant de la source LDAP
            
        Returns:
            True si la source existe et a été définie, False sinon
        """
        pass
    
    @abstractmethod
    def get_available_ldap_sources(self) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les sources LDAP disponibles.
        
        Returns:
            Dictionnaire des sources disponibles avec leurs configurations
        """
        pass