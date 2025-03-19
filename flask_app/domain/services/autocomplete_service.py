# flask_app/domain/services/autocomplete_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AutocompleteService(ABC):
    """
    Interface pour les services d'autocomplétion.
    """
    
    @abstractmethod
    def autocomplete(self, search_type: str, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Service d'autocomplétion unifié pour différents types de recherche.
        
        Args:
            search_type: Type de recherche ('group', 'fullName', 'role', 'services', 'managers')
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste de suggestions
        """
        pass
    
    @abstractmethod
    def autocomplete_fullname(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Autocomplétion pour les noms complets.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste de suggestions
        """
        pass
    
    @abstractmethod
    def autocomplete_groups(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Autocomplétion pour les groupes.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste de suggestions
        """
        pass
    
    @abstractmethod
    def autocomplete_roles(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Autocomplétion pour les rôles.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste de suggestions
        """
        pass
    
    @abstractmethod
    def autocomplete_services(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Autocomplétion pour les services.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste de suggestions
        """
        pass
    
    @abstractmethod
    def autocomplete_managers(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Autocomplétion pour les managers.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste de suggestions
        """
        pass