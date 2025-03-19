# flask_app/domain/dtos/user_dtos.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class UserDTO:
    """DTO pour les données utilisateur complètes."""
    username: str
    dn: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    ldap_source: str = "meta"
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    groups: List[Dict[str, Any]] = field(default_factory=list)
    cn: Optional[str] = None
    sn: Optional[str] = None
    given_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    manager_dn: Optional[str] = None
    manager_name: Optional[str] = None
    employee_type: Optional[str] = None
    favv_nat_nr: Optional[str] = None
    generation_qualifier: Optional[str] = None
    is_disabled: bool = False
    is_locked: bool = False
    is_admin: bool = False
    is_reader: bool = False
    full_name: Optional[str] = None
    last_login: Optional[datetime] = None
    password_expiration_time: Optional[datetime] = None

@dataclass
class UserSearchResultDTO:
    """DTO pour les résultats de recherche d'utilisateur (format simplifié)."""
    dn: str
    cn: str
    full_name: str
    email: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None

@dataclass
class UserListItemDTO:
    """DTO pour un élément dans une liste d'utilisateurs."""
    dn: str
    cn: str
    full_name: str
    email: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    is_disabled: bool = False

@dataclass
class UserProfileDTO:
    """DTO pour le profil utilisateur affiché dans l'interface utilisateur."""
    username: str
    display_name: str
    email: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    is_admin: bool = False
    is_reader: bool = False
    ldap_source: str = "meta"
    dn: str = ""

@dataclass
class UserCreationDTO:
    """DTO pour la création d'un nouvel utilisateur."""
    given_name: str
    sn: str
    email: Optional[str] = None
    user_type: str = ""
    favv_nat_nr: Optional[str] = None
    manager: Optional[str] = None
    manager_dn: Optional[str] = None
    template_cn: Optional[str] = None
    email_override: bool = False
    favv_nat_nr_override: bool = False
    manager_override: bool = False

@dataclass
class UserCreationResultDTO:
    """DTO pour le résultat de la création d'un utilisateur."""
    success: bool
    cn: str
    password: Optional[str] = None
    error_message: Optional[str] = None
    groups_added: int = 0
    groups_failed: int = 0

@dataclass
class UserUpdateDTO:
    """DTO pour la mise à jour d'un utilisateur existant."""
    dn: str
    email: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    manager_dn: Optional[str] = None
    reset_password: bool = False
    expire_password: bool = False
    target_container: Optional[str] = None
    groups_to_add: List[Dict[str, str]] = field(default_factory=list)
    groups_to_remove: List[Dict[str, str]] = field(default_factory=list)
    is_disabled: bool = False
    generation_qualifier: Optional[str] = None