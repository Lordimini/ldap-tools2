# flask_app/domain/repositories/group_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class GroupRepository(ABC):
    """
    Interface définissant les opérations de persistance pour les groupes.
    """
    
    @abstractmethod
    def find_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un groupe par son nom.

        Args:
            group_name: Nom du groupe à rechercher

        Returns:
            Données du groupe ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def find_by_dn(self, group_dn: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un groupe par son DN.

        Args:
            group_dn: DN du groupe

        Returns:
            Données du groupe ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def get_members(self, group_name: str = None, group_dn: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les membres d'un groupe.

        Args:
            group_name: Nom du groupe (optionnel si group_dn est fourni)
            group_dn: DN du groupe (optionnel si group_name est fourni)

        Returns:
            Dictionnaire contenant les informations du groupe et la liste des membres
        """
        pass
    
    @abstractmethod
    def add_user_to_group(self, user_dn: str, group_dn: str) -> bool:
        """
        Ajoute un utilisateur à un groupe.

        Args:
            user_dn: DN de l'utilisateur
            group_dn: DN du groupe

        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def remove_user_from_group(self, user_dn: str, group_dn: str) -> bool:
        """
        Retire un utilisateur d'un groupe.

        Args:
            user_dn: DN de l'utilisateur
            group_dn: DN du groupe

        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Recherche des groupes par nom.

        Args:
            search_term: Terme de recherche

        Returns:
            Liste des groupes correspondant au critère
        """
        pass