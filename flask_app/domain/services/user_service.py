# flask_app/domain/services/user_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

class UserService(ABC):
    """
    Interface pour les services de gestion des utilisateurs.
    """
    
    @abstractmethod
    def search_user(self, search_term: str, search_type: str, 
                   ldap_source: str = None, return_list: bool = False) -> Dict[str, Any]:
        """
        Recherche des utilisateurs selon différents critères.
        
        Args:
            search_term: Terme de recherche
            search_type: Type de recherche ('cn', 'fullName', etc.)
            ldap_source: Source LDAP à utiliser
            return_list: Si True, retourne une liste simplifiée
            
        Returns:
            Résultats de recherche (utilisateur unique ou liste)
        """
        pass
    
    @abstractmethod
    def get_user_details(self, user_dn: str, ldap_source: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un utilisateur.
        
        Args:
            user_dn: DN de l'utilisateur
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Détails de l'utilisateur ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any], ldap_source: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Crée un nouvel utilisateur.
        
        Args:
            user_data: Données de l'utilisateur
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Tuple (succès, message, données utilisateur créé)
        """
        pass
    
    @abstractmethod
    def update_user(self, user_dn: str, attributes: Dict[str, Any], 
                   groups_to_add: List[Dict[str, str]] = None, 
                   groups_to_remove: List[Dict[str, str]] = None,
                   reset_password: bool = False,
                   expire_password: bool = False,
                   target_container: str = None,
                   ldap_source: str = None) -> Tuple[bool, str]:
        """
        Met à jour un utilisateur existant.
        
        Args:
            user_dn: DN de l'utilisateur
            attributes: Attributs à modifier
            groups_to_add: Groupes à ajouter
            groups_to_remove: Groupes à retirer
            reset_password: Si True, réinitialise le mot de passe
            expire_password: Si True, expire le mot de passe
            target_container: Container cible pour déplacement
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Tuple (succès, message)
        """
        pass
    
    @abstractmethod
    def delete_user(self, user_dn: str, ldap_source: str = None) -> Tuple[bool, str]:
        """
        Supprime un utilisateur.
        
        Args:
            user_dn: DN de l'utilisateur
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Tuple (succès, message)
        """
        pass
    
    @abstractmethod
    def get_pending_users(self, ldap_source: str = None) -> List[Dict[str, Any]]:
        """
        Récupère les utilisateurs en attente dans le container to-process.
        
        Args:
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Liste des utilisateurs en attente
        """
        pass
    
    @abstractmethod
    def complete_user_creation(self, user_dn: str, target_container: str, 
                             attributes: Dict[str, Any], groups: List[Dict[str, Any]],
                             set_password: bool = False,
                             ldap_source: str = None) -> Tuple[bool, str]:
        """
        Finalise la création d'un utilisateur.
        
        Args:
            user_dn: DN de l'utilisateur
            target_container: Container de destination
            attributes: Attributs à définir
            groups: Groupes à ajouter
            set_password: Si True, définit un mot de passe par défaut
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Tuple (succès, message)
        """
        pass
    
    @abstractmethod
    def check_name_exists(self, given_name: str, sn: str, ldap_source: str = None) -> Dict[str, Any]:
        """
        Vérifie si un utilisateur avec ce prénom et nom existe déjà.
        
        Args:
            given_name: Prénom
            sn: Nom de famille
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Résultat de la vérification {'status': 'exists'/'ok', 'message': '...'}
        """
        pass
    
    @abstractmethod
    def check_favvnatnr_exists(self, favvnatnr: str, ldap_source: str = None) -> Dict[str, Any]:
        """
        Vérifie si un utilisateur avec ce numéro national existe déjà.
        
        Args:
            favvnatnr: Numéro de registre national
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Résultat de la vérification {'status': 'exists'/'ok', 'message': '...'}
        """
        pass
    
    @abstractmethod
    def generate_cn(self, given_name: str, sn: str) -> str:
        """
        Génère un CN unique pour un nouvel utilisateur.
        
        Args:
            given_name: Prénom
            sn: Nom de famille
            
        Returns:
            CN généré
        """
        pass
    
    @abstractmethod
    def preview_user_details(self, given_name: str, sn: str, user_type: str, ldap_source: str = None) -> Dict[str, Any]:
        """
        Prévisualise les détails d'un utilisateur avant création.
        
        Args:
            given_name: Prénom
            sn: Nom de famille
            user_type: Type d'utilisateur
            ldap_source: Source LDAP à utiliser
            
        Returns:
            Détails prévisualisés (CN, mot de passe, etc.)
        """
        pass