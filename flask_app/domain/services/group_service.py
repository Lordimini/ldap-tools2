# flask_app/domain/services/group_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

class GroupService(ABC):
    """
    Interface pour les services de gestion des groupes.
    """
    
    @abstractmethod
    def get_group_users(self, group_name: str = None, group_dn: str = None, ldap_source: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les membres d'un groupe.
        
        Args:
            group_name: Nom du groupe (optionnel si group_dn est fourni)
            group_dn: DN du groupe (optionnel si group_name est fourni)
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Informations du groupe et liste des membres
        """
        pass
    
    @abstractmethod
    def add_user_to_group(self, user_dn: str, group_dn: str, ldap_source: str = None) -> bool:
        """
        Ajoute un utilisateur à un groupe.
        
        Args:
            user_dn: DN de l'utilisateur
            group_dn: DN du groupe
            ldap_source: Source LDAP à utiliser
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def remove_user_from_group(self, user_dn: str, group_dn: str, ldap_source: str = None) -> bool:
        """
        Retire un utilisateur d'un groupe.
        
        Args:
            user_dn: DN de l'utilisateur
            group_dn: DN du groupe
            ldap_source: Source LDAP à utiliser
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def add_users_to_group(self, users: List[Dict[str, Any]], group_dn: str, ldap_source: str = None) -> Tuple[int, List[str]]:
        """
        Ajoute plusieurs utilisateurs à un groupe.
        
        Args:
            users: Liste des DNs d'utilisateurs à ajouter
            group_dn: DN du groupe
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Tuple (nombre de succès, liste des échecs)
        """
        pass
    
    @abstractmethod
    def validate_bulk_cns(self, cn_list: List[str], group_dn: str, ldap_source: str = None) -> Dict[str, Any]:
        """
        Valide une liste de CNs et retourne les utilisateurs trouvés.
        
        Args:
            cn_list: Liste des CNs à valider
            group_dn: DN du groupe (pour vérifier si l'utilisateur est déjà membre)
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Dict avec utilisateurs valides et CNs invalides
        """
        pass
    
    @abstractmethod
    def search_groups(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Recherche des groupes par nom.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste des groupes correspondant au critère
        """
        pass
    
    @abstractmethod
    def export_group_users(self, group_name: str = None, group_dn: str = None, 
                         format: str = 'csv', ldap_source: str = None):
        """
        Exporte les membres d'un groupe dans un format spécifique.
        
        Args:
            group_name: Nom du groupe (optionnel si group_dn est fourni)
            group_dn: DN du groupe (optionnel si group_name est fourni)
            format: Format d'export ('csv', 'pdf', etc.)
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Données d'export dans le format demandé
        """
        pass