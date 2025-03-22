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
        
        # Register with app context
        app.menu_config = self
        
        # Add to context processor for use in templates
        @app.context_processor
        def inject_menu_config():
            return {'menu_config': self}
    
    def _load_menu_configs(self):
        """Load menu configuration from a single JSON file"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        
        # Load the single menu configuration file
        menu_path = os.path.join(config_dir, 'menu_role_permissions.json')
        if os.path.exists(menu_path):
            with open(menu_path, 'r') as f:
                self.menu_configs = json.load(f)
            # Initialize default menu - prenez le menu de meta par défaut si disponible
            if 'sources' in self.menu_configs and 'meta' in self.menu_configs['sources']:
                self.default_menu = self.menu_configs['sources']['meta'].get('menu_items', [])
            else:
                self.default_menu = []
        else:
            self.menu_configs = {}
            self.default_menu = []
        
        # Since we're using a single file with permissions,
        # we don't need separate role-specific menus anymore
        self.menu_configs = {}
        self.role_menus = {}
    
    def get_menu_for_user(self, user=None):
        if user is None:
            user = g.user if hasattr(g, 'user') else None
        
        # If no user or not authenticated, return empty menu
        if not user or not user.is_authenticated:
            return []
            
        # Get current LDAP source
        ldap_source = getattr(user, 'ldap_source', None) or session.get('ldap_source', 'meta')
        
        # Get menu items for the current source, or fall back to default
        if 'sources' in self.menu_configs and ldap_source in self.menu_configs['sources']:
            menu_items = copy.deepcopy(self.menu_configs['sources'][ldap_source].get('menu_items', self.default_menu))
        else:
            menu_items = copy.deepcopy(self.default_menu)
    
        # Filter menu items based on user permissions
        filtered_menu = []
        
        for item in menu_items:
            # If it's a section, process its subitems
            if item.get('is_section', False):
                filtered_subitems = []
                for subitem in item.get('items', []):
                    # Check if the user has the required permission(s)
                    has_permission = True
                    
                    # Check for multiple permissions (OR logic)
                    required_permissions = subitem.get('required_permissions', [])
                    if required_permissions:
                        # User needs at least one of these permissions
                        has_permission = any(user.has_permission(p) for p in required_permissions)
                    # Check for single permission
                    elif 'required_permission' in subitem:
                        has_permission = user.has_permission(subitem['required_permission'])
                    
                    if has_permission:
                        filtered_subitems.append(subitem)
                
                # Only add the section if it has visible subitems
                if filtered_subitems:
                    section_copy = copy.deepcopy(item)
                    section_copy['items'] = filtered_subitems
                    filtered_menu.append(section_copy)
            else:
                # For regular items, check the permission(s)
                has_permission = True
                
                # Check for multiple permissions (OR logic)
                required_permissions = item.get('required_permissions', [])
                if required_permissions:
                    # User needs at least one of these permissions
                    has_permission = any(user.has_permission(p) for p in required_permissions)
                # Check for single permission
                elif 'required_permission' in item:
                    has_permission = user.has_permission(item['required_permission'])
                
                if has_permission:
                    filtered_menu.append(item)
        
        return filtered_menu
    
    
    
    def render_menu(self, user=None):
        """
        Render HTML menu for the current user with collapsible sections
        
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
        
        # Counter to create unique IDs for each collapsible section
        section_counter = 0
        
        for item in menu_items:
            # Skip items that are explicitly set to not visible
            if item.get('visible') is False:
                continue
            
            # Item permission check is already done in get_menu_for_user
            if item.get('is_section'):
                # Increment counter for unique ID
                section_counter += 1
                section_id = f'section-{section_counter}'
                
                # Render collapsible section header
                html += f'''
                <li class="nav-item section-header">
                    <a class="nav-link d-flex justify-content-between align-items-center" 
                    data-bs-toggle="collapse" 
                    href="#{section_id}" 
                    role="button" 
                    aria-expanded="false" 
                    aria-controls="{section_id}">
                        <span>{item["label"]}</span>
                        <i class="bi bi-chevron-down section-icon"></i>
                    </a>
                    <div class="collapse" id="{section_id}">
                        <ul class="nav flex-column section-items">
                '''
                
                # Render section items
                for sub_item in item.get('items', []):
                    # Skip sub-items that are explicitly set to not visible
                    if sub_item.get('visible') is False:
                        continue
                    
                    # Permission check already done in get_menu_for_user
                    
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
                
                # Close the section
                html += '''
                        </ul>
                    </div>
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