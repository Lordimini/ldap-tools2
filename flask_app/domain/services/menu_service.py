# flask_app/domain/services/menu_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class MenuService(ABC):
    """
    Interface pour les services de gestion des menus.
    """
    
    @abstractmethod
    def get_menu_for_user(self, user_data: Dict[str, Any], ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Récupère les éléments de menu pour un utilisateur selon ses rôles.
        
        Args:
            user_data: Données utilisateur
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Éléments de menu appropriés
        """
        pass
    
    @abstractmethod
    def render_menu(self, user_data: Dict[str, Any], ldap_source: str = None) -> str:
        """
        Génère le HTML du menu pour un utilisateur.
        
        Args:
            user_data: Données utilisateur
            ldap_source: Source LDAP à utiliser
            
        Returns:
            HTML du menu
        """
        pass
    
    @abstractmethod
    def is_menu_item_active(self, item: Dict[str, Any], current_path: str) -> bool:
        """
        Vérifie si un élément de menu doit être marqué comme actif.
        
        Args:
            item: Élément de menu
            current_path: Chemin actuel
            
        Returns:
            True si l'élément est actif, False sinon
        """
        pass
    
    @abstractmethod
    def get_available_menus(self) -> Dict[str, Any]:
        """
        Récupère toutes les configurations de menu disponibles.
        
        Returns:
            Configurations de menu
        """
        pass