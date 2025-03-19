# flask_app/domain/repositories/template_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class TemplateRepository(ABC):
    """
    Interface définissant les opérations de persistance pour les templates utilisateur.
    """
    
    @abstractmethod
    def get_template_details(self, template_cn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un template spécifique.

        Args:
            template_cn: CN du template

        Returns:
            Détails du template ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def get_user_types(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les types d'utilisateur disponibles.

        Returns:
            Liste des types d'utilisateur avec leurs descriptions
        """
        pass