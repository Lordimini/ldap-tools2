# flask_app/domain/services/role_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

class RoleService(ABC):
    """
    Interface pour les services de gestion des rôles.
    """
    
    @abstractmethod
    def get_role_users(self, role_cn: str, ldap_source: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les utilisateurs associés à un rôle.
        
        Args:
            role_cn: CN du rôle
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Informations du rôle et liste des utilisateurs
        """
        pass
    
    @abstractmethod
    def get_role_groups(self, role_cn: str, ldap_source: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les groupes associés à un rôle.
        
        Args:
            role_cn: CN du rôle
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Informations du rôle et liste des groupes
        """
        pass
    
    @abstractmethod
    def view_role(self, dn: str, ldap_source: str = None) -> Optional[Dict[str, Any]]:
        """
        Affiche les détails d'un rôle.
        
        Args:
            dn: DN du rôle
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Informations détaillées du rôle
        """
        pass
    
    @abstractmethod
    def get_ldap_children(self, current_dn: str, ldap_source: str = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Récupère les enfants d'un conteneur LDAP (rôles et conteneurs).
        
        Args:
            current_dn: DN du conteneur actuel
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Tuple (liste des enfants, dn_parent)
        """
        pass
    
    @abstractmethod
    def search_roles(self, search_term: str, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Recherche des rôles par nom.
        
        Args:
            search_term: Terme de recherche
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste des rôles correspondant au critère
        """
        pass
    
    @abstractmethod
    def export_role_users(self, role_cn: str, format: str = 'csv', ldap_source: str = None):
        """
        Exporte les utilisateurs d'un rôle dans un format spécifique.
        
        Args:
            role_cn: CN du rôle
            format: Format d'export ('csv', 'pdf', etc.)
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Données d'export dans le format demandé
        """
        pass