# flask_app/domain/models/template.py
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Template:
    """
    Modèle représentant un template utilisateur LDAP.
    """
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
    
    def get_group_count(self) -> int:
        """
        Retourne le nombre de groupes associés au template.
        
        Returns:
            Nombre de groupes
        """
        return len(self.groups)
    
    @classmethod
    def from_ldap_data(cls, template_data: Dict[str, Any]) -> 'Template':
        """
        Crée une instance Template à partir des données LDAP.
        
        Args:
            template_data: Données LDAP du template
            
        Returns:
            Instance Template
        """
        # Extraire les groupes
        groups = []
        if 'groupMembership' in template_data and template_data['groupMembership']:
            for group_dn in template_data['groupMembership']:
                # Si le groupe a déjà le format de dictionnaire attendu
                if isinstance(group_dn, dict) and 'dn' in group_dn:
                    groups.append(group_dn)
                # Si le groupe est juste un DN
                else:
                    group_name = group_dn.split(',')[0].split('=')[1] if '=' in group_dn else group_dn
                    groups.append({
                        'dn': group_dn,
                        'cn': group_name
                    })
        
        return cls(
            cn=template_data.get('cn', ''),
            dn=template_data.get('dn'),
            description=template_data.get('description'),
            title=template_data.get('title'),
            ou=template_data.get('ou'),
            employee_type=template_data.get('FavvEmployeeType'),
            employee_sub_type=template_data.get('FavvEmployeeSubType'),
            service_manager_dn=template_data.get('FavvExtDienstMgrDn'),
            service_manager_name=template_data.get('ServiceManagerName'),
            groups=groups
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le template en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données du template
        """
        return {
            'cn': self.cn,
            'dn': self.dn,
            'description': self.description,
            'title': self.title,
            'ou': self.ou,
            'employee_type': self.employee_type,
            'employee_sub_type': self.employee_sub_type,
            'service_manager_dn': self.service_manager_dn,
            'service_manager_name': self.service_manager_name,
            'groups': self.groups,
            'group_count': self.get_group_count()
        }