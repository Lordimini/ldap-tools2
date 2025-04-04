from flask_login import UserMixin
from functools import wraps
from flask import redirect, url_for, flash, abort, g

class User(UserMixin):
    """
    Enhanced User class with role-based permissions and profile data.
    Extends UserMixin from Flask-Login for easy integration.
    """
    def __init__(self, username, dn, display_name=None, email=None, ldap_source=None, 
                 roles=None, permissions=None, groups=None):
        self.id = username  # required by Flask-Login
        self.username = username
        self.dn = dn
        self.display_name = display_name or username
        self.email = email
        self.ldap_source = ldap_source or 'meta'
        self.roles = roles or []
        self.permissions = permissions or set()
        self.groups = groups or []
        # self.is_authenticated = True
        # self.is_active = True
        # self.is_anonymous = False
        self._profile_data = {}
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return role in self.roles
    
    def has_any_role(self, roles):
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)
    
    def has_permission(self, permission):
        """Check if user has a specific permission"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions):
        """Check if user has any of the specified permissions"""
        return any(perm in self.permissions for perm in permissions)
    
    def is_in_group(self, group):
        """Check if user is a member of a specific group"""
        return group in self.groups
    
    def get_id(self):
        """Required by Flask-Login"""
        return self.username
    
    def update_profile_data(self, data):
        """Update additional profile data"""
        self._profile_data.update(data)
    
    def get_profile_data(self, key, default=None):
        """Get specific profile data"""
        return self._profile_data.get(key, default)
    
    @property
    def name(self):
        """Return display name or username for user interface"""
        return self.display_name or self.username
    
    @property 
    def is_admin(self):
        """Check if user has admin role"""
        return 'admin' in self.roles

    @property
    def is_reader(self):
        """Check if user has reader role"""
        return 'reader' in self.roles
    
    @classmethod
    def from_ldap_data(cls, username, user_data, ldap_source='meta'):
        groups = []
        if 'groupMembership' in user_data and user_data['groupMembership']:
            groups = [group['cn'] for group in user_data['groupMembership']]
        
        roles = []
        
        if 'admin_group_dn' in user_data and user_data.get('is_admin_member', False):
            roles.append('admin')
        
        if 'reader_group_dn' in user_data and user_data.get('is_reader_member', False):
            roles.append('reader')
        
        if 'oci_admin_group_dn' in user_data and user_data.get('is_oci_admin_member', False):
            roles.append('OCI-admin')
        
        from flask import current_app
        permissions = set()
        
        if current_app and hasattr(current_app, 'role_config'):
            permissions = current_app.role_config.get_permissions(roles)
        else:
            if 'admin' in roles:
                permissions.update([
                    'view_users', 'create_users', 'edit_users', 'delete_users', 'admin_users'
                ])
        
        return cls(
            username=username,
            dn=user_data.get('dn', ''),
            display_name=user_data.get('fullName', username),
            email=user_data.get('mail', None),
            ldap_source=ldap_source,
            roles=roles,
            permissions=permissions,
            groups=groups
        )
        
# Role-based access decorators
def role_required(role):
    """Decorator to require a specific role for access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated and has the required role
            if not g.user or not g.user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not g.user.has_role(role):
                flash(f'You need the "{role}" role to access this page.', 'danger')
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission):
    """Decorator to require a specific permission for access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated and has the required permission
            if not g.user or not g.user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not g.user.has_permission(permission):
                flash(f'You don\'t have permission to access this resource.', 'danger')
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not g.user.is_admin:
            flash('Administrator access is required.', 'danger')
            abort(403)  # Forbidden
        
        return f(*args, **kwargs)
    return decorated_function