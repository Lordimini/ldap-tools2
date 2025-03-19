# flask_app/domain/dtos/menu_dtos.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class MenuItemDTO:
    """DTO pour un élément de menu."""
    label: str
    url: str = ""
    icon: str = ""
    active_pattern: str = ""
    is_section: bool = False
    items: List['MenuItemDTO'] = field(default_factory=list)
    required_permission: Optional[str] = None
    admin_only: bool = False
    visible: bool = True
    id: Optional[str] = None
    is_active: bool = False

@dataclass
class MenuConfigDTO:
    """DTO pour une configuration de menu complète."""
    name: str
    menu_items: List[MenuItemDTO] = field(default_factory=list)