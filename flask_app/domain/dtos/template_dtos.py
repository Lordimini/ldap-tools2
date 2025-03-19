# flask_app/domain/dtos/template_dtos.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class TemplateDTO:
    """DTO pour les données de template utilisateur complètes."""
    cn: str
    dn: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    ou: Optional[str] = None
    employee_type: Optional[str] = None
    employee_sub_type: Optional[str] = None
    service_manager_dn: Optional[str] = None
    service_manager_name: Optional[str] = None
    groups: List[Dict[str, Any]] = field(default_factory=list)
    group_count: int = 0

@dataclass
class TemplateGroupDTO:
    """DTO pour un groupe associé à un template."""
    dn: str
    cn: str

@dataclass
class UserTypeDTO:
    """DTO pour un type d'utilisateur basé sur un template."""
    value: str
    label: str
    title: Optional[str] = None

@dataclass
class UserPreviewDTO:
    """DTO pour la prévisualisation des détails utilisateur avant création."""
    cn: str
    password: str
    template_details: Optional[Dict[str, Any]] = None
    has_short_name: bool = False