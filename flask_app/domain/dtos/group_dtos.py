# flask_app/domain/dtos/group_dtos.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class GroupDTO:
    """DTO pour les données de groupe complètes."""
    name: str
    dn: str
    description: Optional[str] = None
    members: List[Dict[str, Any]] = field(default_factory=list)
    member_count: int = 0

@dataclass
class GroupListItemDTO:
    """DTO pour un élément dans une liste de groupes."""
    name: str
    dn: str
    description: Optional[str] = None
    member_count: int = 0

@dataclass
class GroupMemberDTO:
    """DTO pour un membre d'un groupe."""
    dn: str
    cn: str
    full_name: str
    title: Optional[str] = None
    department: Optional[str] = None

@dataclass
class GroupSearchResultDTO:
    """DTO pour les résultats de recherche de groupe."""
    name: str
    dn: str
    description: Optional[str] = None
    
@dataclass
class AutocompleteGroupItemDTO:
    """DTO pour un élément d'autocomplétion de groupe."""
    label: str
    value: str
    dn: Optional[str] = None

@dataclass
class GroupAddRemoveResultDTO:
    """DTO pour le résultat d'ajout/suppression de membres à un groupe."""
    success: bool
    message: str
    success_count: int = 0
    failed_users: List[str] = field(default_factory=list)

@dataclass
class BulkCNValidationDTO:
    """DTO pour la validation d'une liste de CNs pour ajout au groupe."""
    valid_users: List[Dict[str, Any]]
    invalid_users: List[str]