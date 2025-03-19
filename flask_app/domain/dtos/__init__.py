# flask_app/domain/dtos/__init__.py
# User DTOs
from .user_dtos import (
    UserDTO, UserSearchResultDTO, UserListItemDTO, 
    UserProfileDTO, UserCreationDTO, UserCreationResultDTO,
    UserUpdateDTO
)

# Group DTOs
from .group_dtos import (
    GroupDTO, GroupListItemDTO, GroupMemberDTO,
    GroupSearchResultDTO, AutocompleteGroupItemDTO,
    GroupAddRemoveResultDTO, BulkCNValidationDTO
)

# Role DTOs
from .role_dtos import (
    RoleDTO, RoleListItemDTO, RoleUserDTO,
    RoleResourceDTO, RoleSearchResultDTO,
    LDAPBrowserItemDTO
)

# Service DTOs
from .service_dtos import (
    ServiceDTO, ServiceListItemDTO, ServiceUserDTO,
    ServiceSearchResultDTO, AutocompleteServiceItemDTO
)

# Template DTOs
from .template_dtos import (
    TemplateDTO, TemplateGroupDTO, UserTypeDTO,
    UserPreviewDTO
)

# Menu DTOs
from .menu_dtos import (
    MenuItemDTO, MenuConfigDTO
)

# Auth DTOs
from .auth_dtos import (
    LoginRequestDTO, LoginResultDTO, LDAPSourceDTO
)

# Common DTOs
from .common_dtos import (
    ResultDTO, PageInfoDTO, PagedResultDTO,
    AutocompleteItemDTO, SelectOptionDTO,
    DashboardStatsDTO, ActivityItemDTO
)