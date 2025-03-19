# flask_app/domain/services/application_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ApplicationService(ABC):
    """
    Interface pour les services d'application généraux.
    """
    
    @abstractmethod
    def get_app_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration de l'application.
        
        Returns:
            Configuration de l'application
        """
        pass
    
    @abstractmethod
    def get_app_version(self) -> str:
        """
        Récupère la version de l'application.
        
        Returns:
            Version de l'application
        """
        pass
    
    @abstractmethod
    def log_activity(self, user: str, action: str, target: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enregistre une activité pour l'audit.
        
        Args:
            user: Utilisateur qui a effectué l'action
            action: Type d'action (create, update, delete, etc.)
            target: Cible de l'action
            details: Détails supplémentaires
            
        Returns:
            True si l'enregistrement a réussi, False sinon
        """
        pass