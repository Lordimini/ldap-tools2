# flask_app/domain/repositories/role_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

class RoleRepository(ABC):
    """
    Interface définissant les opérations de persistance pour les rôles.
    """
    
    @abstractmethod
    def find_by_cn(self, role_cn: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un rôle par son CN.

        Args:
            role_cn: CN du rôle à rechercher

        Returns:
            Données du rôle ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def get_role_users(self, role_cn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les utilisateurs associés à un rôle.

        Args:
            role_cn: CN du rôle

        Returns:
            Dictionnaire contenant les informations du rôle et la liste des utilisateurs
        """
        pass
    
    @abstractmethod
    def get_role_groups(self, role_cn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les groupes associés à un rôle.

        Args:
            role_cn: CN du rôle

        Returns:
            Dictionnaire contenant les informations du rôle et la liste des groupes
        """
        pass
    
    @abstractmethod
    def view_role(self, dn: str) -> Optional[Dict[str, Any]]:
        """
        Affiche les détails d'un rôle, y compris ses utilisateurs.

        Args:
            dn: DN du rôle

        Returns:
            Dictionnaire détaillé des informations du rôle
        """
        pass
    
    @abstractmethod
    def get_ldap_children(self, current_dn: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Récupère les enfants d'un conteneur LDAP (rôles et conteneurs).

        Args:
            current_dn: DN du conteneur actuel

        Returns:
            Tuple (liste des enfants, dn_parent)
        """
        pass
    
    @abstractmethod
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Recherche des rôles par nom.

        Args:
            search_term: Terme de recherche

        Returns:
            Liste des rôles correspondant au critère
        """
        pass