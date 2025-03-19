# flask_app/domain/repositories/service_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class ServiceRepository(ABC):
    """
    Interface définissant les opérations de persistance pour les services (OU).
    """
    
    @abstractmethod
    def get_service_users(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les utilisateurs d'un service donné.

        Args:
            service_name: Nom du service (ou)

        Returns:
            Dictionnaire contenant les informations du service et la liste des utilisateurs
        """
        pass
    
    @abstractmethod
    def get_managers(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des utilisateurs marqués comme managers (FavvDienstHoofd=YES).

        Returns:
            Liste des utilisateurs managers
        """
        pass
    
    @abstractmethod
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Recherche des services par nom.

        Args:
            search_term: Terme de recherche

        Returns:
            Liste des services correspondant au critère
        """
        pass