# flask_app/domain/models/role.py
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Role:
    """
    Modèle représentant un rôle LDAP.
    """
    name: str
    dn: str
    description: Optional[str] = None
    users: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    category: Optional[str] = None
    
    def has_user(self, user_dn: str) -> bool:
        """
        Vérifie si un utilisateur est assigné à ce rôle.
        
        Args:
            user_dn: DN de l'utilisateur
            
        Returns:
            True si l'utilisateur est assigné, False sinon
        """
        return any(user.get('dn') == user_dn for user in self.users)
    
    def has_user_by_cn(self, user_cn: str) -> bool:
        """
        Vérifie si un utilisateur est assigné à ce rôle par son CN.
        
        Args:
            user_cn: CN de l'utilisateur
            
        Returns:
            True si l'utilisateur est assigné, False sinon
        """
        return any(user.get('CN') == user_cn for user in self.users)
    
    def get_user_count(self) -> int:
        """
        Retourne le nombre d'utilisateurs assignés à ce rôle.
        
        Returns:
            Nombre d'utilisateurs
        """
        return len(self.users)
    
    def get_resources_count(self) -> int:
        """
        Retourne le nombre de ressources (groupes) associées à ce rôle.
        
        Returns:
            Nombre de ressources
        """
        return len(self.resources)
    
    @classmethod
    def from_ldap_data(cls, role_data: Dict[str, Any]) -> 'Role':
        """
        Crée une instance Role à partir des données LDAP.
        
        Args:
            role_data: Données LDAP du rôle
            
        Returns:
            Instance Role
        """
        return cls(
            name=role_data.get('role_cn', ''),
            dn=role_data.get('role_dn', ''),
            description=role_data.get('description', None),
            users=role_data.get('users', []),
            resources=role_data.get('groups', []),
            category=role_data.get('category', None)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le rôle en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données du rôle
        """
        return {
            'name': self.name,
            'dn': self.dn,
            'description': self.description,
            'users': self.users,
            'resources': self.resources,
            'category': self.category,
            'user_count': self.get_user_count(),
            'resource_count': self.get_resources_count()
        }