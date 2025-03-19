# flask_app/domain/repositories/autocomplete_repository.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AutocompleteRepository(ABC):
    """
    Interface définissant les opérations de persistance pour les fonctionnalités d'autocomplétion.
    """
    
    @abstractmethod
    def autocomplete(self, search_type: str, search_term: str) -> List[Dict[str, Any]]:
        """
        Fonction d'autocomplétion unifiée supportant différents types de recherche.

        Args:
            search_type: Type de recherche ('group', 'fullName', 'role', 'services', 'managers')
            search_term: Terme de recherche

        Returns:
            Liste de dictionnaires avec 'label' et 'value'
        """
        pass
    
    @abstractmethod
    def autocomplete_role(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Fonction d'autocomplétion spécifique pour les rôles.

        Args:
            search_term: Terme de recherche

        Returns:
            Liste de dictionnaires avec 'label' et 'value'
        """
        pass
    
    @abstractmethod
    def autocomplete_services(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Fonction d'autocomplétion pour les services (OU).

        Args:
            search_term: Terme de recherche

        Returns:
            Liste de dictionnaires avec 'label' et 'value'
        """
        pass