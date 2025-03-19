# flask_app/domain/models/group.py
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Group:
    """
    Modèle représentant un groupe LDAP.
    """
    name: str
    dn: str
    description: Optional[str] = None
    members: List[Dict[str, Any]] = field(default_factory=list)
    
    def has_member(self, user_dn: str) -> bool:
        """
        Vérifie si un utilisateur est membre du groupe.
        
        Args:
            user_dn: DN de l'utilisateur
            
        Returns:
            True si l'utilisateur est membre, False sinon
        """
        return any(member.get('dn') == user_dn for member in self.members)
    
    def has_member_by_cn(self, user_cn: str) -> bool:
        """
        Vérifie si un utilisateur est membre du groupe par son CN.
        
        Args:
            user_cn: CN de l'utilisateur
            
        Returns:
            True si l'utilisateur est membre, False sinon
        """
        return any(member.get('CN') == user_cn for member in self.members)
    
    def get_member_count(self) -> int:
        """
        Retourne le nombre de membres dans le groupe.
        
        Returns:
            Nombre de membres
        """
        return len(self.members)
    
    def get_member_by_cn(self, user_cn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un membre par son CN.
        
        Args:
            user_cn: CN de l'utilisateur
            
        Returns:
            Informations du membre ou None si non trouvé
        """
        for member in self.members:
            if member.get('CN') == user_cn:
                return member
        return None
    
    @classmethod
    def from_ldap_data(cls, group_data: Dict[str, Any]) -> 'Group':
        """
        Crée une instance Group à partir des données LDAP.
        
        Args:
            group_data: Données LDAP du groupe
            
        Returns:
            Instance Group
        """
        return cls(
            name=group_data.get('group_name', ''),
            dn=group_data.get('group_dn', ''),
            description=group_data.get('description', None),
            members=group_data.get('users', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le groupe en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données du groupe
        """
        return {
            'name': self.name,
            'dn': self.dn,
            'description': self.description,
            'members': self.members,
            'member_count': self.get_member_count()
        }