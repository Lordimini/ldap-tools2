# flask_app/domain/dtos/mappers.py
from typing import List, Dict, Any, TypeVar, Generic, Optional, Type
from ..models.user import User
from ..models.group import Group
from ..models.role import Role
from ..models.service import Service
from ..models.template import Template
from ..models.menu_item import MenuItem
from ..models.activity import Activity
from ..models.paged_result import PagedResult

from .user_dtos import UserDTO, UserListItemDTO, UserSearchResultDTO, UserProfileDTO
from .group_dtos import GroupDTO, GroupListItemDTO, GroupMemberDTO
from .role_dtos import RoleDTO, RoleListItemDTO, RoleUserDTO
from .service_dtos import ServiceDTO, ServiceListItemDTO, ServiceUserDTO
from .menu_dtos import MenuItemDTO
from .common_dtos import PagedResultDTO, PageInfoDTO, ActivityItemDTO

T = TypeVar('T')
D = TypeVar('D')

class DTOMapper:
    """Classe utilitaire pour convertir entre objets de domaine et DTOs."""
    
    @staticmethod
    def map_user_to_dto(user: User) -> UserDTO:
        """Convertit un User en UserDTO."""
        return UserDTO(
            username=user.username,
            dn=user.dn,
            display_name=user.display_name,
            email=user.email,
            ldap_source=user.ldap_source,
            roles=user.roles,
            permissions=list(user.permissions),
            groups=user.groups,
            cn=user.cn,
            sn=user.sn,
            given_name=user.given_name,
            title=user.title,
            department=user.department,
            manager_dn=user.manager_dn,
            manager_name=user.manager_name,
            employee_type=user.employee_type,
            favv_nat_nr=user.favv_nat_nr,
            generation_qualifier=user.generation_qualifier,
            is_disabled=user.is_disabled,
            is_locked=user.is_locked,
            is_admin=user.is_admin,
            is_reader=user.is_reader,
            full_name=user.full_name,
            last_login=user.login_time,
            password_expiration_time=user.password_expiration_time
        )
    
    @staticmethod
    def map_user_to_profile_dto(user: User) -> UserProfileDTO:
        """Convertit un User en UserProfileDTO."""
        return UserProfileDTO(
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            roles=user.roles,
            groups=[g['cn'] for g in user.groups],
            is_admin=user.is_admin,
            is_reader=user.is_reader,
            ldap_source=user.ldap_source,
            dn=user.dn
        )
    
    @staticmethod
    def map_group_to_dto(group: Group) -> GroupDTO:
        """Convertit un Group en GroupDTO."""
        return GroupDTO(
            name=group.name,
            dn=group.dn,
            description=group.description,
            members=group.members,
            member_count=group.get_member_count()
        )
    
    @staticmethod
    def map_role_to_dto(role: Role) -> RoleDTO:
        """Convertit un Role en RoleDTO."""
        return RoleDTO(
            name=role.name,
            dn=role.dn,
            description=role.description,
            users=role.users,
            resources=role.resources,
            category=role.category,
            user_count=role.get_user_count(),
            resource_count=role.get_resources_count()
        )
    
    @staticmethod
    def map_service_to_dto(service: Service) -> ServiceDTO:
        """Convertit un Service en ServiceDTO."""
        return ServiceDTO(
            name=service.name,
            description=service.description,
            users=service.users,
            user_count=service.get_user_count()
        )
    
    @staticmethod
    def map_menu_item_to_dto(menu_item: MenuItem, current_path: str = "") -> MenuItemDTO:
        """Convertit un MenuItem en MenuItemDTO."""
        items = []
        if menu_item.is_section and menu_item.items:
            items = [DTOMapper.map_menu_item_to_dto(item, current_path) for item in menu_item.items]
        
        return MenuItemDTO(
            label=menu_item.label,
            url=menu_item.url,
            icon=menu_item.icon,
            active_pattern=menu_item.active_pattern,
            is_section=menu_item.is_section,
            items=items,
            required_permission=menu_item.required_permission,
            admin_only=menu_item.admin_only,
            visible=menu_item.visible,
            id=menu_item.id,
            is_active=menu_item.is_active(current_path) if current_path else False
        )
    
    @staticmethod
    def map_activity_to_dto(activity: Activity) -> ActivityItemDTO:
        """Convertit une Activity en ActivityItemDTO."""
        return ActivityItemDTO(
            user=activity.user,
            action=activity.action,
            action_label=activity.get_action_label(),
            target=activity.target,
            timestamp=activity.timestamp.isoformat(),
            elapsed=activity.get_elapsed_time(),
            details=activity.details
        )
    
    @staticmethod
    def map_paged_result_to_dto(paged_result: PagedResult[T], 
                                map_function=None) -> PagedResultDTO[D]:
        """
        Convertit un PagedResult en PagedResultDTO.
        
        Args:
            paged_result: PagedResult à convertir
            map_function: Fonction de mapping pour les éléments
            
        Returns:
            PagedResultDTO avec les éléments convertis
        """
        page_info = PageInfoDTO(
            page=paged_result.page,
            page_size=paged_result.page_size,
            total=paged_result.total,
            total_pages=paged_result.total_pages,
            has_previous=paged_result.has_previous,
            has_next=paged_result.has_next,
            previous_page=paged_result.previous_page,
            next_page=paged_result.next_page
        )
        
        items = paged_result.items
        if map_function:
            items = [map_function(item) for item in items]
        
        return PagedResultDTO(
            items=items,
            page_info=page_info
        )
    
    @classmethod
    def map_list(cls, items: List[T], map_function) -> List[D]:
        """
        Mappe une liste d'éléments avec une fonction de mapping.
        
        Args:
            items: Liste à mapper
            map_function: Fonction de mapping
            
        Returns:
            Liste des éléments mappés
        """
        return [map_function(item) for item in items]