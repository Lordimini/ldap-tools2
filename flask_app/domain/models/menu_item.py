# flask_app/domain/models/menu_item.py
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class MenuItem:
    """
    Modèle représentant un élément de menu dans l'interface utilisateur.
    """
    label: str
    url: str = ""
    icon: str = ""
    active_pattern: str = ""
    is_section: bool = False
    items: List['MenuItem'] = field(default_factory=list)
    required_permission: Optional[str] = None
    admin_only: bool = False
    visible: bool = True
    id: Optional[str] = None
    
    def is_active(self, current_path: str) -> bool:
        """
        Vérifie si cet élément de menu doit être marqué comme actif.
        
        Args:
            current_path: Chemin actuel de l'URL
            
        Returns:
            True si l'élément est actif, False sinon
        """
        import re
        if not self.active_pattern:
            return self.url == current_path
        return bool(re.search(self.active_pattern, current_path))
    
    def has_active_child(self, current_path: str) -> bool:
        """
        Vérifie si l'un des enfants de ce menu est actif.
        
        Args:
            current_path: Chemin actuel de l'URL
            
        Returns:
            True si un enfant est actif, False sinon
        """
        if not self.is_section:
            return False
        
        return any(item.is_active(current_path) for item in self.items)
    
    def is_accessible_to_user(self, user_permissions: List[str], is_admin: bool) -> bool:
        """
        Vérifie si cet élément de menu est accessible à un utilisateur.
        
        Args:
            user_permissions: Liste des permissions de l'utilisateur
            is_admin: Si l'utilisateur est administrateur
            
        Returns:
            True si l'élément est accessible, False sinon
        """
        if not self.visible:
            return False
            
        if self.admin_only and not is_admin:
            return False
            
        if self.required_permission and self.required_permission not in user_permissions:
            return False
            
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MenuItem':
        """
        Crée une instance MenuItem à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données du menu
            
        Returns:
            Instance MenuItem
        """
        # Récursivement créer les éléments enfants
        items = []
        if data.get('is_section') and 'items' in data:
            items = [cls.from_dict(item_data) for item_data in data['items']]
        
        return cls(
            label=data.get('label', ''),
            url=data.get('url', ''),
            icon=data.get('icon', ''),
            active_pattern=data.get('active_pattern', ''),
            is_section=data.get('is_section', False),
            items=items,
            required_permission=data.get('required_permission'),
            admin_only=data.get('admin_only', False),
            visible=data.get('visible', True),
            id=data.get('id')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'élément de menu en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données de l'élément de menu
        """
        result = {
            'label': self.label,
            'url': self.url,
            'icon': self.icon,
            'active_pattern': self.active_pattern,
            'is_section': self.is_section,
            'visible': self.visible
        }
        
        if self.is_section:
            result['items'] = [item.to_dict() for item in self.items]
        
        if self.required_permission:
            result['required_permission'] = self.required_permission
            
        if self.admin_only:
            result['admin_only'] = self.admin_only
            
        if self.id:
            result['id'] = self.id
            
        return result