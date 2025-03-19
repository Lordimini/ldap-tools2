# flask_app/domain/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class UserRepository(ABC):
    """
    Interface définissant les opérations de persistance pour les utilisateurs.
    Cette interface isole la logique métier des détails d'implémentation LDAP.
    """
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un utilisateur par son nom d'utilisateur (CN).

        Args:
            username: Le nom d'utilisateur à rechercher

        Returns:
            Les données de l'utilisateur ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def find_by_dn(self, dn: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un utilisateur par son DN.

        Args:
            dn: Le DN de l'utilisateur

        Returns:
            Les données de l'utilisateur ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def search(self, search_term: str, search_type: str, return_list: bool = False) -> List[Dict[str, Any]]:
        """
        Recherche des utilisateurs selon différents critères.

        Args:
            search_term: Le terme de recherche
            search_type: Le type de recherche (cn, fullName, mail, etc.)
            return_list: Si True, retourne une liste simplifiée d'utilisateurs

        Returns:
            Liste des utilisateurs correspondant aux critères
        """
        pass
    
    @abstractmethod
    def create(self, user_data: Dict[str, Any], template_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crée un nouvel utilisateur.

        Args:
            user_data: Les données de l'utilisateur à créer
            template_details: Détails du template à appliquer (optionnel)

        Returns:
            Les données de l'utilisateur créé avec informations supplémentaires
        """
        pass
    
    @abstractmethod
    def update(self, user_dn: str, attributes: Dict[str, Any], 
              groups_to_add: Optional[List[Dict[str, str]]] = None, 
              groups_to_remove: Optional[List[Dict[str, str]]] = None,
              target_container: Optional[str] = None) -> tuple:
        """
        Met à jour un utilisateur existant.

        Args:
            user_dn: DN de l'utilisateur à mettre à jour
            attributes: Attributs à modifier
            groups_to_add: Groupes à ajouter
            groups_to_remove: Groupes à retirer
            target_container: Container cible pour déplacement (optionnel)

        Returns:
            Tuple (succès, message)
        """
        pass
    
    @abstractmethod
    def delete(self, user_dn: str) -> tuple:
        """
        Supprime un utilisateur.

        Args:
            user_dn: DN de l'utilisateur à supprimer

        Returns:
            Tuple (succès, message)
        """
        pass
    
    @abstractmethod
    def get_pending_users(self) -> List[Dict[str, Any]]:
        """
        Récupère les utilisateurs en attente dans le container to-process.

        Returns:
            Liste des utilisateurs en attente
        """
        pass
    
    @abstractmethod
    def complete_user_creation(self, user_dn: str, target_container: str, 
                             attributes: Dict[str, Any], groups: List[Dict[str, Any]],
                             set_password: bool = False) -> tuple:
        """
        Finalise la création d'un utilisateur en le déplaçant et en définissant des attributs.

        Args:
            user_dn: DN de l'utilisateur
            target_container: Container de destination
            attributes: Attributs à définir
            groups: Groupes à ajouter
            set_password: Si True, définit un mot de passe par défaut

        Returns:
            Tuple (succès, message)
        """
        pass
    
    @abstractmethod
    def check_name_exists(self, given_name: str, sn: str) -> tuple:
        """
        Vérifie si un utilisateur avec ce prénom et nom existe déjà.

        Args:
            given_name: Prénom
            sn: Nom de famille

        Returns:
            Tuple (existe, dn_si_existe)
        """
        pass
    
    @abstractmethod
    def check_favvnatnr_exists(self, favvnatnr: str) -> tuple:
        """
        Vérifie si un utilisateur avec ce numéro national existe déjà.

        Args:
            favvnatnr: Numéro de registre national

        Returns:
            Tuple (existe, dn_si_existe, nom_complet)
        """
        pass