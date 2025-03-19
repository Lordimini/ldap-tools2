# flask_app/domain/dtos/common_dtos.py
from typing import List, Dict, Any, Optional, TypeVar, Generic, Union
from dataclasses import dataclass, field

T = TypeVar('T')

@dataclass
class ResultDTO(Generic[T]):
    """DTO pour les résultats d'opérations."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None

@dataclass
class PageInfoDTO:
    """DTO pour les informations de pagination."""
    page: int
    page_size: int
    total: int
    total_pages: int
    has_previous: bool
    has_next: bool
    previous_page: int
    next_page: int

@dataclass
class PagedResultDTO(Generic[T]):
    """DTO pour les résultats paginés."""
    items: List[T]
    page_info: PageInfoDTO

@dataclass
class AutocompleteItemDTO:
    """DTO pour un élément d'autocomplétion générique."""
    label: str
    value: str

@dataclass
class SelectOptionDTO:
    """DTO pour une option dans un menu déroulant."""
    value: str
    label: str
    disabled: bool = False
    selected: bool = False

@dataclass
class DashboardStatsDTO:
    """DTO pour les statistiques du tableau de bord."""
    total_users: int
    disabled_accounts: int
    inactive_users: int
    expired_password_users: int
    never_logged_in_users: int
    recent_logins: int

@dataclass
class ActivityItemDTO:
    """DTO pour un élément d'activité dans l'historique."""
    user: str
    action: str
    action_label: str
    target: str
    timestamp: str
    elapsed: str
    details: Optional[Dict[str, Any]] = None