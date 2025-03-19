# flask_app/domain/dtos/service_dtos.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ServiceDTO:
    """DTO pour les données de service (OU) complètes."""
    name: str
    description: Optional[str] = None
    users: List[Dict[str, Any]] = field(default_factory=list)
    user_count: int = 0

@dataclass
class ServiceListItemDTO:
    """DTO pour un élément dans une liste de services."""
    name: str
    description: Optional[str] = None
    user_count: int = 0

@dataclass
class ServiceUserDTO:
    """DTO pour un utilisateur appartenant à un service."""
    cn: str
    full_name: str
    title: Optional[str] = None
    email: Optional[str] = None

@dataclass
class ServiceSearchResultDTO:
    """DTO pour les résultats de recherche de service."""
    name: str
    description: Optional[str] = None

@dataclass
class AutocompleteServiceItemDTO:
    """DTO pour un élément d'autocomplétion de service."""
    label: str
    value: str