# flask_app/domain/dtos/auth_dtos.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class LoginRequestDTO:
    """DTO pour une demande de connexion."""
    username: str
    password: str
    ldap_source: str = "meta"
    remember: bool = False

@dataclass
class LoginResultDTO:
    """DTO pour le résultat d'une authentification."""
    success: bool
    user: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None

@dataclass
class LDAPSourceDTO:
    """DTO pour les informations d'une source LDAP."""
    name: str
    display_name: str
    is_default: bool = False
    is_active: bool = False