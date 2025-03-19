# flask_app/domain/models/activity.py
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Activity:
    """
    Modèle représentant une activité utilisateur pour l'audit.
    """
    user: str
    action: str
    target: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    ldap_source: Optional[str] = None
    
    # flask_app/domain/models/activity.py (suite)
    @classmethod
    def create(cls, user: str, action: str, target: str, 
              details: Optional[Dict[str, Any]] = None,
              ip_address: Optional[str] = None,
              ldap_source: Optional[str] = None) -> 'Activity':
        """
        Crée une nouvelle activité.
        
        Args:
            user: Utilisateur qui a effectué l'action
            action: Type d'action (create, update, delete, etc.)
            target: Cible de l'action
            details: Détails supplémentaires
            ip_address: Adresse IP de l'utilisateur
            ldap_source: Source LDAP utilisée
            
        Returns:
            Instance Activity
        """
        return cls(
            user=user,
            action=action,
            target=target,
            timestamp=datetime.now(),
            details=details,
            ip_address=ip_address,
            ldap_source=ldap_source
        )
    
    def get_action_label(self) -> str:
        """
        Retourne un libellé lisible pour l'action.
        
        Returns:
            Libellé de l'action
        """
        action_labels = {
            'create': 'Created',
            'update': 'Updated',
            'delete': 'Deleted',
            'add': 'Added',
            'remove': 'Removed',
            'login': 'Logged in',
            'logout': 'Logged out',
            'password_reset': 'Reset password',
            'upload': 'Uploaded',
            'download': 'Downloaded',
            'move': 'Moved',
            'search': 'Searched'
        }
        return action_labels.get(self.action, self.action.capitalize())
    
    def get_elapsed_time(self) -> str:
        """
        Retourne le temps écoulé depuis cette activité de manière lisible.
        
        Returns:
            Temps écoulé (ex: "5 minutes ago")
        """
        now = datetime.now()
        delta = now - self.timestamp
        
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return self.timestamp.strftime("%Y-%m-%d %H:%M")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'activité en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données de l'activité
        """
        return {
            'user': self.user,
            'action': self.action,
            'action_label': self.get_action_label(),
            'target': self.target,
            'timestamp': self.timestamp.isoformat(),
            'elapsed': self.get_elapsed_time(),
            'details': self.details,
            'ip_address': self.ip_address,
            'ldap_source': self.ldap_source
        }