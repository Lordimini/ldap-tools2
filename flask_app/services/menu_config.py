from flask import g, session, current_app
import os
import json
import copy

class MenuConfig:
    """Service for configuring and managing dynamic menus based on user roles"""
    
    def __init__(self, app=None):
        self.app = app
        self.menu_configs = {}
        self.role_menus = {}
        self.default_menu = []
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the menu configuration with the Flask app"""
        self.app = app
        self._load_menu_configs()
        self._prepare_role_menus()
        
        # Register with app context
        app.menu_config = self
        
        # Add to context processor for use in templates
        @app.context_processor
        def inject_menu_config():
            return {'menu_config': self}
    
    def _load_menu_configs(self):
        """Load menu configuration files from config directory"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        
        # Load base menu configuration
        base_menu_path = os.path.join(config_dir, 'menu_base.json')
        if os.path.exists(base_menu_path):
            with open(base_menu_path, 'r') as f:
                self.default_menu = json.load(f).get('menu_items', [])
        
        # Load role-specific menu configurations
        for filename in os.listdir(config_dir):
            if filename.startswith('menu_role_') and filename.endswith('.json'):
                role_name = filename[10:-5]  # Extract role name between 'menu_role_' and '.json'
                file_path = os.path.join(config_dir, filename)
                
                with open(file_path, 'r') as f:
                    self.menu_configs[role_name] = json.load(f).get('menu_items', [])
    
    def _prepare_role_menus(self):
        """Prepare combined menus for each role"""
        # Admin gets all menu items
        if 'admin' in self.menu_configs:
            self.role_menus['admin'] = self.menu_configs['admin']
        else:
            # If no specific admin config, use default + admin items
            admin_menu = copy.deepcopy(self.default_menu)
            self.role_menus['admin'] = admin_menu
        
        # Reader gets reader-specific items + common items
        if 'reader' in self.menu_configs:
            self.role_menus['reader'] = self.menu_configs['reader']
        else:
            # Filter out admin-only items from default menu
            reader_menu = [
                item for item in self.default_menu 
                if not item.get('admin_only', False)
            ]
            self.role_menus['reader'] = reader_menu
        
        # For other roles, create as needed
        for role, menu_items in self.menu_configs.items():
            if role not in ['admin', 'reader']:
                self.role_menus[role] = menu_items
    
    def get_menu_for_user(self, user=None):
        """
        Get menu items for the current user based on their roles
        
        Args:
            user: User object (uses g.user if not provided)
        
        Returns:
            list: Menu items appropriate for the user's roles
        """
        if user is None:
            user = g.user if hasattr(g, 'user') else None
        
        # If no user or not authenticated, return empty menu
        if not user or not user.is_authenticated:
            return []
        
        # Check user roles and return appropriate menu
        if user.is_admin and 'admin' in self.role_menus:
            return self.role_menus['admin']
        elif user.is_reader and 'reader' in self.role_menus:
            return self.role_menus['reader']
        
        # If user has other roles, combine their role menus
        combined_menu = []
        for role in user.roles:
            if role in self.role_menus:
                # Add items not already in combined menu
                for item in self.role_menus[role]:
                    if item not in combined_menu:
                        combined_menu.append(item)
        
        # If no specific role menu found, fall back to default menu
        if not combined_menu:
            # Filter items that don't require specific permissions
            combined_menu = [
                item for item in self.default_menu 
                if not item.get('required_permission') or 
                (user.has_permission(item.get('required_permission')))
            ]
        
        return combined_menu
    
    def render_menu(self, user=None):
        """
        Render HTML menu for the current user
        
        Args:
            user: User object (uses g.user if not provided)
            
        Returns:
            str: HTML string of menu
        """
        if user is None:
            user = g.user if hasattr(g, 'user') else None
        
        menu_items = self.get_menu_for_user(user)
        
        # Start building the menu HTML
        html = '<ul class="nav flex-column">'
        
        for item in menu_items:
            # Skip items that are explicitly set to not visible
            if item.get('visible') is False:
                continue
            
            # Check if user has required permission for this item
            if 'required_permission' in item and user:
                if not user.has_permission(item['required_permission']):
                    continue
            
            if item.get('is_section'):
                # Render section header
                html += f'<div class="sidebar-heading">{item["label"]}</div>'
                
                # Render section items (only if they're visible)
                for sub_item in item.get('items', []):
                    # Skip sub-items that are explicitly set to not visible
                    if sub_item.get('visible') is False:
                        continue
                    
                    # Check permission for sub-item
                    if 'required_permission' in sub_item and user:
                        if not user.has_permission(sub_item['required_permission']):
                            continue
                    
                    # Check if this is the active item based on current path
                    is_active = self._is_active(sub_item)
                    active_class = 'active' if is_active else ''
                    
                    html += f'''
                    <li class="nav-item">
                        <a class="nav-link {active_class}" href="{sub_item['url']}">
                            <i class="{sub_item['icon']}"></i>
                            <span>{sub_item['label']}</span>
                        </a>
                    </li>
                    '''
            else:
                # Render regular menu item
                is_active = self._is_active(item)
                active_class = 'active' if is_active else ''
                
                html += f'''
                <li class="nav-item">
                    <a class="nav-link {active_class}" href="{item['url']}">
                        <i class="{item['icon']}"></i>
                        <span>{item['label']}</span>
                    </a>
                </li>
                '''
        
        html += '</ul>'
        return html
    
    def _is_active(self, item):
        """
        Check if a menu item should be marked as active based on current path
        
        Args:
            item: Menu item to check
            
        Returns:
            bool: True if item is active, False otherwise
        """
        from flask import request
        current_path = request.path
        
        if 'active_pattern' in item:
            import re
            return re.search(item['active_pattern'], current_path) is not None
        else:
            return current_path == item['url']