# flask_app/domain/dtos/role_dtos.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class RoleDTO:
    """DTO pour les données de rôle complètes."""
    name: str
    dn: str
    description: Optional[str] = None
    users: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    category: Optional[str] = None
    user_count: int = 0
    resource_count: int = 0

@dataclass
class RoleListItemDTO:
    """DTO pour un élément dans une liste de rôles."""
    name: str
    dn: str
    description: Optional[str] = None
    category: Optional[str] = None
    user_count: int = 0

@dataclass
class RoleUserDTO:
    """DTO pour un utilisateur assigné à un rôle."""
    dn: str
    cn: str
    full_name: str
    title: Optional[str] = None
    department: Optional[str] = None
    req_desc: Optional[str] = None

@dataclass
class RoleResourceDTO:
    """DTO pour une ressource (groupe) associée à un rôle."""
    name: str
    dn: Optional[str] = None
    description: Optional[str] = None

@dataclass
class RoleSearchResultDTO:
    """DTO pour les résultats de recherche de rôle."""
    name: str
    dn: str
    description: Optional[str] = None
    category: Optional[str] = None

@dataclass
class LDAPBrowserItemDTO:
    """DTO pour un élément dans le navigateur LDAP."""
    type: str  # 'container' ou 'role'
    name: str
    dn: str
    role_cn: Optional[str] = None