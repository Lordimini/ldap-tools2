# flask_app/domain/models/service.py
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Service:
    """
    Modèle représentant un service (unité organisationnelle) LDAP.
    """
    name: str
    description: Optional[str] = None
    users: List[Dict[str, Any]] = field(default_factory=list)
    
    def has_user(self, user_dn: str) -> bool:
        """
        Vérifie si un utilisateur appartient à ce service.
        
        Args:
            user_dn: DN de l'utilisateur
            
        Returns:
            True si l'utilisateur appartient au service, False sinon
        """
        return any(user.get('dn') == user_dn for user in self.users)
    
    def has_user_by_cn(self, user_cn: str) -> bool:
        """
        Vérifie si un utilisateur appartient à ce service par son CN.
        
        Args:
            user_cn: CN de l'utilisateur
            
        Returns:
            True si l'utilisateur appartient au service, False sinon
        """
        return any(user.get('CN') == user_cn for user in self.users)
    
    def get_user_count(self) -> int:
        """
        Retourne le nombre d'utilisateurs dans ce service.
        
        Returns:
            Nombre d'utilisateurs
        """
        return len(self.users)
    
    def get_managers(self) -> List[Dict[str, Any]]:
        """
        Retourne les utilisateurs qui sont managers dans ce service.
        
        Returns:
            Liste des managers
        """
        return [user for user in self.users if user.get('is_manager', False)]
    
    @classmethod
    def from_ldap_data(cls, service_data: Dict[str, Any]) -> 'Service':
        """
        Crée une instance Service à partir des données LDAP.
        
        Args:
            service_data: Données LDAP du service
            
        Returns:
            Instance Service
        """
        return cls(
            name=service_data.get('service_name', ''),
            description=service_data.get('description', None),
            users=service_data.get('users', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le service en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données du service
        """
        return {
            'name': self.name,
            'description': self.description,
            'users': self.users,
            'user_count': self.get_user_count()
        }