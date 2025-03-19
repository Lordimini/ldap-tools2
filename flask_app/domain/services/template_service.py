# flask_app/domain/services/template_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class TemplateService(ABC):
    """
    Interface pour les services de gestion des templates utilisateur.
    """
    
    @abstractmethod
    def get_template_details(self, template_cn: str, ldap_source: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un template spécifique.
        
        Args:
            template_cn: CN du template
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Détails du template
        """
        pass
    
    @abstractmethod
    def get_user_types(self, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les types d'utilisateur disponibles.
        
        Args:
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste des types d'utilisateur
        """
        pass