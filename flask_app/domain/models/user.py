# flask_app/domain/models/user.py
from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    """
    Modèle d'utilisateur représentant un utilisateur LDAP.
    """
    username: str
    dn: str
    display_name: str = None
    email: str = None
    ldap_source: str = "meta"
    roles: List[str] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)
    groups: List[Dict[str, Any]] = field(default_factory=list)
    
    # Attributs LDAP communs
    cn: str = None
    sn: str = None
    given_name: str = None
    title: str = None
    department: str = None  # ou
    manager_dn: str = None  # FavvHierarMgrDN
    manager_name: str = None
    employee_type: str = None  # FavvEmployeeType
    favv_nat_nr: str = None
    generation_qualifier: str = None
    
    # États
    is_disabled: bool = False
    is_locked: bool = False
    login_time: Optional[datetime] = None
    password_expiration_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialise les attributs après la création de l'instance"""
        if self.display_name is None:
            self.display_name = self.username
    
    def has_role(self, role: str) -> bool:
        """Vérifie si l'utilisateur a un rôle spécifique"""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Vérifie si l'utilisateur a au moins un des rôles spécifiés"""
        return any(role in self.roles for role in roles)
    
    def has_permission(self, permission: str) -> bool:
        """Vérifie si l'utilisateur a une permission spécifique"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Vérifie si l'utilisateur a au moins une des permissions spécifiées"""
        return any(perm in self.permissions for perm in permissions)
    
    def is_in_group(self, group_name: str) -> bool:
        """Vérifie si l'utilisateur est membre d'un groupe spécifique"""
        return any(group['cn'] == group_name for group in self.groups)
    
    def get_group_names(self) -> List[str]:
        """Retourne les noms des groupes dont l'utilisateur est membre"""
        return [group['cn'] for group in self.groups]
    
    @property
    def name(self) -> str:
        """Retourne le nom d'affichage ou le nom d'utilisateur"""
        return self.display_name or self.username
    
    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur a le rôle d'administrateur"""
        return 'admin' in self.roles
    
    @property
    def is_reader(self) -> bool:
        """Vérifie si l'utilisateur a le rôle de lecteur"""
        return 'reader' in self.roles
    
    @property
    def full_name(self) -> str:
        """Retourne le nom complet (prénom + nom)"""
        if self.sn and self.given_name:
            return f"{self.sn} {self.given_name}"
        return self.display_name or self.username
    
    @classmethod
    def from_ldap_data(cls, username: str, ldap_data: Dict[str, Any], ldap_source: str = 'meta') -> 'User':
        """
        Crée une instance User à partir des données LDAP.
        
        Args:
            username: Nom d'utilisateur
            ldap_data: Données LDAP
            ldap_source: Source LDAP
            
        Returns:
            Instance User
        """
        # Extraire les groupes
        groups = []
        if 'groupMembership' in ldap_data and ldap_data['groupMembership']:
            groups = ldap_data['groupMembership']
        
        # Extraire les rôles
        roles = []
        if 'is_admin_member' in ldap_data and ldap_data.get('is_admin_member'):
            roles.append('admin')
        if 'is_reader_member' in ldap_data and ldap_data.get('is_reader_member'):
            roles.append('reader')
        
        # Définir les permissions
        permissions = set()
        if 'admin' in roles:
            permissions.update([
                'view_users', 'create_users', 'edit_users', 'delete_users',
                'view_groups', 'edit_groups', 'create_groups', 'delete_groups',
                'view_roles', 'edit_roles', 'create_roles', 'delete_roles',
                'view_services', 'edit_services', 'upload_files', 'manage_system'
            ])
        elif 'reader' in roles:
            permissions.update([
                'view_users', 'view_groups', 'view_roles', 'view_services'
            ])
        
        # Déterminer si l'utilisateur est désactivé ou verrouillé
        login_disabled = ldap_data.get('loginDisabled', 'NO') == 'YES'
        
        # Convertir les timestamps
        login_time = None
        if 'loginTime' in ldap_data and ldap_data['loginTime']:
            try:
                login_time = datetime.strptime(ldap_data['loginTime'], "%Y%m%d%H%M%SZ")
            except ValueError:
                pass
        
        password_expiration_time = None
        if 'passwordExpirationTime' in ldap_data and ldap_data['passwordExpirationTime']:
            try:
                password_expiration_time = datetime.strptime(ldap_data['passwordExpirationTime'], "%Y%m%d%H%M%SZ")
            except ValueError:
                pass
        
        # Créer l'instance User
        return cls(
            username=username,
            dn=ldap_data.get('dn', ''),
            display_name=ldap_data.get('fullName', username),
            email=ldap_data.get('mail', None),
            ldap_source=ldap_source,
            roles=roles,
            permissions=permissions,
            groups=groups,
            cn=ldap_data.get('CN', username),
            sn=ldap_data.get('sn', None),
            given_name=ldap_data.get('givenName', None),
            title=ldap_data.get('title', None),
            department=ldap_data.get('service', None),
            manager_dn=ldap_data.get('FavvHierarMgrDN', None),
            manager_name=ldap_data.get('manager_name', None) or ldap_data.get('ChefHierarchique', None),
            employee_type=ldap_data.get('favvEmployeeType', None),
            favv_nat_nr=ldap_data.get('FavvNatNr', None),
            generation_qualifier=ldap_data.get('generationQualifier', None),
            is_disabled=login_disabled,
            is_locked=False,  # Information non disponible dans les données LDAP actuelles
            login_time=login_time,
            password_expiration_time=password_expiration_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'utilisateur en dictionnaire, utile pour la sérialisation.
        
        Returns:
            Dictionnaire contenant les données de l'utilisateur
        """
        return {
            'username': self.username,
            'dn': self.dn,
            'display_name': self.display_name,
            'email': self.email,
            'ldap_source': self.ldap_source,
            'roles': list(self.roles),
            'permissions': list(self.permissions),
            'groups': self.groups,
            'cn': self.cn,
            'sn': self.sn,
            'given_name': self.given_name,
            'title': self.title,
            'department': self.department,
            'manager_dn': self.manager_dn,
            'manager_name': self.manager_name,
            'employee_type': self.employee_type,
            'favv_nat_nr': self.favv_nat_nr,
            'generation_qualifier': self.generation_qualifier,
            'is_disabled': self.is_disabled,
            'is_locked': self.is_locked,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'password_expiration_time': self.password_expiration_time.isoformat() if self.password_expiration_time else None,
            'is_admin': self.is_admin,
            'is_reader': self.is_reader,
            'name': self.name,
            'full_name': self.full_name
        }