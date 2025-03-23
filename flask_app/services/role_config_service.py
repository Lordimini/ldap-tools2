# flask_app/services/role_config_service.py
import json
import os

class RoleConfigService:
    def __init__(self, app=None):
        self.app = app
        self.config = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        self._load_role_config()
        
        # Register with app context
        app.role_config = self
    
    def _load_role_config(self):
        
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'config', 
            'role_user_types.json'
        )
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
    
    def get_allowed_user_types(self, roles):
        """Get allowed user types for the given roles"""
        allowed_types = set()
        
        # Default to empty list if roles is None
        if not roles:
            return []
            
        for role in roles:
            role_config = self.config.get('role_permissions', {}).get(role, {})
            types = role_config.get('user_types', [])
            
            # If '*' is in types, user can access all types
            if '*' in types:
                return ['*']
                
            # Otherwise add specific types
            allowed_types.update(types)
            
        return list(allowed_types)
    
    def get_permissions(self, roles):
        """Get permissions for the given roles"""
        permissions = set()
        
        # Default to empty set if roles is None
        if not roles:
            return permissions
            
        for role in roles:
            role_config = self.config.get('role_permissions', {}).get(role, {})
            role_permissions = role_config.get('permissions', [])
            permissions.update(role_permissions)
            
        return permissions
    
    def can_manage_user_type(self, roles, user_type):
        """Check if user with given roles can manage a specific user type"""
        allowed_types = self.get_allowed_user_types(roles)
        
        # If '*' is in allowed_types, user can manage all types
        if '*' in allowed_types:
            return True
            
        return user_type in allowed_types