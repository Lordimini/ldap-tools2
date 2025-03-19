# flask_app/domain/services/service_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class ServiceService(ABC):
    """
    Interface pour les services de gestion des services (OU).
    """
    
    @abstractmethod
    def get_service_users(self, service_name: str, ldap_source: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les utilisateurs d'un service donné.
        
        Args:
            service_name: Nom du service (ou)
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Informations du service et liste des utilisateurs
        """
        pass
    
    @abstractmethod
    def get_managers(self, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Récupère la liste des utilisateurs marqués comme managers.
        
        Args:
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste des utilisateurs managers
        """
        pass
    
    @abstractmethod
    def search_services(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Recherche des services par nom.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste des services correspondant au critère
        """
        pass
    
    @abstractmethod
    def export_service_users(self, service_name: str, format: str = 'csv', ldap_source: str = None):
        """
        Exporte les utilisateurs d'un service dans un format spécifique.
        
        Args:
            service_name: Nom du service
            format: Format d'export ('csv', 'pdf', etc.)
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Données d'export dans le format demandé
        """
        pass