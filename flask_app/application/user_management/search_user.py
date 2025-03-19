# flask_app/application/user_management/search_user.py
from typing import Dict, Any, List, Optional
from flask_app.domain.services.user_service import UserService
from flask_app.domain.models.result import Result
from flask_app.domain.models.paged_result import PagedResult
from flask_app.domain.dtos.user_dtos import UserDTO, UserSearchResultDTO
from flask_app.domain.dtos.common_dtos import PagedResultDTO, ResultDTO


class SearchUserUseCase:
    """
    Cas d'utilisation pour la recherche d'utilisateurs.
    Cette classe orchestre le processus de recherche d'utilisateurs et représente
    un cas d'utilisation selon l'architecture DDD (Domain-Driven Design).
    """
    
    def __init__(self, user_service: UserService):
        """
        Initialise le cas d'utilisation avec les services nécessaires.
        
        Args:
            user_service: Service de gestion des utilisateurs
        """
        self.user_service = user_service
    
    def search_by_criteria(self, search_term: str, search_type: str, 
                          ldap_source: str = None, page: int = 1, 
                          page_size: int = 20) -> ResultDTO[PagedResultDTO[UserSearchResultDTO]]:
        """
        Recherche des utilisateurs selon des critères spécifiés.
        
        Args:
            search_term: Terme de recherche
            search_type: Type de recherche (cn, fullName, mail, etc.)
            ldap_source: Source LDAP à utiliser
            page: Numéro de page pour la pagination
            page_size: Nombre d'éléments par page
            
        Returns:
            DTO de résultat contenant une liste paginée d'utilisateurs
        """
        try:
            # Valider les paramètres d'entrée
            if not search_term or not search_type:
                return ResultDTO(
                    success=False,
                    error="Les paramètres de recherche sont requis."
                )
            
            # Effectuer la recherche via le service utilisateur
            result = self.user_service.search_user(
                search_term=search_term,
                search_type=search_type,
                ldap_source=ldap_source,
                return_list=True
            )
            
            # Paginer les résultats
            total_results = len(result)
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_results)
            
            paged_items = result[start_idx:end_idx]
            
            # Convertir les résultats en DTOs
            search_results = []
            for item in paged_items:
                search_results.append(UserSearchResultDTO(
                    dn=item.get('dn', ''),
                    cn=item.get('cn', ''),
                    full_name=item.get('fullName', ''),
                    email=item.get('mail', None),
                    title=item.get('title', None),
                    department=item.get('service', None)
                ))
            
            # Créer le DTO de pagination
            page_info = {
                'page': page,
                'page_size': page_size,
                'total': total_results,
                'total_pages': (total_results + page_size - 1) // page_size,
                'has_previous': page > 1,
                'has_next': end_idx < total_results,
                'previous_page': max(1, page - 1),
                'next_page': min((total_results + page_size - 1) // page_size, page + 1)
            }
            
            # Retourner le résultat paginé
            return ResultDTO(
                success=True,
                data=PagedResultDTO(
                    items=search_results,
                    page_info=page_info
                )
            )
            
        except Exception as e:
            # Gestion des erreurs inattendues
            return ResultDTO(
                success=False,
                error=f"Une erreur s'est produite lors de la recherche: {str(e)}"
            )
    
    def get_user_details(self, user_dn: str, ldap_source: str = None) -> ResultDTO[UserDTO]:
        """
        Récupère les détails d'un utilisateur spécifique.
        
        Args:
            user_dn: DN de l'utilisateur
            ldap_source: Source LDAP à utiliser
            
        Returns:
            DTO de résultat contenant les détails de l'utilisateur
        """
        try:
            # Valider les paramètres d'entrée
            if not user_dn:
                return ResultDTO(
                    success=False,
                    error="Le DN de l'utilisateur est requis."
                )
            
            # Récupérer les détails via le service utilisateur
            user_details = self.user_service.get_user_details(
                user_dn=user_dn,
                ldap_source=ldap_source
            )
            
            if not user_details:
                return ResultDTO(
                    success=False,
                    error="Utilisateur non trouvé."
                )
            
            # Convertir en UserDTO
            user_dto = UserDTO(
                username=user_details.get('CN', ''),
                dn=user_details.get('dn', ''),
                display_name=user_details.get('fullName', ''),
                email=user_details.get('mail', None),
                ldap_source=ldap_source or 'meta',
                roles=[role for role in user_details.get('roles', [])],
                permissions=user_details.get('permissions', []),
                groups=user_details.get('groupMembership', []),
                cn=user_details.get('CN', ''),
                sn=user_details.get('sn', ''),
                given_name=user_details.get('givenName', ''),
                title=user_details.get('title', ''),
                department=user_details.get('service', ''),
                manager_dn=user_details.get('FavvHierarMgrDN', ''),
                manager_name=user_details.get('manager_name', ''),
                employee_type=user_details.get('favvEmployeeType', ''),
                favv_nat_nr=user_details.get('FavvNatNr', ''),
                generation_qualifier=user_details.get('generationQualifier', ''),
                is_disabled=user_details.get('loginDisabled', 'NO') == 'YES',
                is_locked=False,  # Information non disponible dans les données actuelles
                full_name=user_details.get('fullName', ''),
                last_login=None,  # Conversion datetime à implémenter si nécessaire
                password_expiration_time=None  # Conversion datetime à implémenter si nécessaire
            )
            
            return ResultDTO(
                success=True,
                data=user_dto
            )
            
        except Exception as e:
            # Gestion des erreurs inattendues
            return ResultDTO(
                success=False,
                error=f"Une erreur s'est produite lors de la récupération des détails: {str(e)}"
            )