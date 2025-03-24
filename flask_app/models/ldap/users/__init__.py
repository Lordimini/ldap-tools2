# flask_app/models/ldap/users/__init__.py
from .user_crud import LDAPUserCRUD
from .user_utils import LDAPUserUtils


class LDAPUserMixin(LDAPUserCRUD, LDAPUserUtils):
    """
    Classe mixine qui combine les fonctionnalités de LDAPUserCRUD et LDAPUserUtils.
    Cette classe maintient la rétrocompatibilité avec le code existant.
    """
    
    def __init__(self, config):
        """
        Initialise la classe avec la configuration LDAP fournie.
        
        Args:
            config (dict): Configuration LDAP
        """
        super().__init__(config)
    
    # Méthodes de compatibilité avec l'ancien code
    
    # def search_user_final(self, search_param, search_type=None, simplified=False, search_active_only=False, return_list=False):
    #     """
    #     Méthode de compatibilité qui redirige vers get_user avec les options appropriées.
        
    #     Args:
    #         search_param: Paramètre de recherche (CN, mail, DN, etc.)
    #         search_type: Type de recherche ('cn', 'fullName', 'mail', etc.)
    #         simplified: Retourner un format simplifié
    #         search_active_only: Ne rechercher que les utilisateurs actifs
    #         return_list: Retourner une liste d'utilisateurs au lieu d'un seul
            
    #     Returns:
    #         dict/list: Données utilisateur ou liste d'utilisateurs selon options
    #     """
    #     options = {
    #         'search_type': search_type,
    #         'simplified': simplified,
    #         'return_list': return_list,
    #         'container': 'active' if search_active_only else 'all'
    #     }
        
    #     return self.get_user(search_param, options)
    
    # def complete_user_creation(self, user_dn, target_container, attributes, groups, set_password=False):
    #     """
    #     Méthode de compatibilité qui redirige vers update_user avec les options appropriées.
        
    #     Args:
    #         user_dn (str): DN de l'utilisateur à compléter
    #         target_container (str): Container cible pour déplacer l'utilisateur
    #         attributes (dict): Attributs à définir
    #         groups (list): Groupes à ajouter
    #         set_password (bool): Définir un nouveau mot de passe
            
    #     Returns:
    #         tuple: (bool, str) - Succès de l'opération et message de statut
    #     """
    #     options = {
    #         'target_container': target_container,
    #         'groups_to_add': groups,
    #         'reset_password': set_password,
    #         'is_completion': True
    #     }
        
    #     return self.update_user(user_dn, attributes, options)
    
    # def get_pending_users(self):
    #     """
    #     Méthode de compatibilité qui récupère les utilisateurs en attente.
        
    #     Returns:
    #         list: Liste des utilisateurs en attente
    #     """
    #     options = {
    #         'container': 'toprocess',
    #         'return_list': True
    #     }
        
    #     return self.get_user("(objectClass=Person)", options)
    
    # Exporter les classes individuelles pour un accès direct
    UserCRUD = LDAPUserCRUD
    UserUtils = LDAPUserUtils