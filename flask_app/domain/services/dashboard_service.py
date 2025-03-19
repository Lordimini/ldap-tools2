# flask_app/domain/services/dashboard_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class DashboardService(ABC):
    """
    Interface pour les services de tableau de bord et statistiques.
    """
    
    @abstractmethod
    def get_dashboard_stats(self, ldap_source: str = None) -> Dict[str, Any]:
        """
        Récupère les statistiques pour le tableau de bord.
        
        Args:
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Statistiques du tableau de bord
        """
        pass
    
    @abstractmethod
    def get_user_stats(self, ldap_source: str = None) -> Dict[str, Any]:
        """
        Récupère des statistiques détaillées sur les utilisateurs.
        
        Args:
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Statistiques détaillées des utilisateurs
        """
        pass
    
    @abstractmethod
    def get_recent_activities(self, limit: int = 5, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Récupère les activités récentes pour affichage dans le tableau de bord.
        
        Args:
            limit: Nombre maximum d'activités à récupérer
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste des activités récentes
        """
        pass