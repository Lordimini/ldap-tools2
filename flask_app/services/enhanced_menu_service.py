# flask_app/services/enhanced_menu_service.py
import os
import json
import copy
from flask import current_app, g, session

class EnhancedMenuService:
    """
    Service for managing dynamic menus based on both user roles and LDAP source.
    Combines role-based menu configuration with LDAP source-specific menu items.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.role_menus = {}
        self.source_menus = {}
        self.default_menu = []
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the menu service with a Flask application"""
        self.app = app
        
        # Load base menu
        base_menu_path = os.path.join(app.root_path, 'config', 'menu_base.json')
        if os.path.exists(base_menu_path):
            with open(base_menu_path, 'r') as f:
                self.default_menu = json.load(f).get('menu_items', [])
        
        # Load role-specific menus
        self._load_role_menus()
        
        # Load source-specific menus
        self._load_source_menus()
        
        # Make menu service available in templates
        @app.context_processor
        def inject_menu_service():
            return {'menu_service': self}
    
    def _load_role_menus(self):
        """Load role-specific menu configurations"""
        config_dir = os.path.join(self.app.root_path, 'config')
        
        # Look for menu_role_*.json files
        for filename in os.listdir(config_dir):
            if filename.startswith('menu_role_') and filename.endswith('.json'):
                role = filename[len('menu_role_'):-len('.json')]
                filepath = os.path.join(config_dir, filename)
                
                with open(filepath, 'r') as f:
                    menu_data = json.load(f)
                    self.role_menus[role] = menu_data.get('menu_items', [])
    
    def _load_source_menus(self):
        """Load LDAP source-specific menu configurations"""
        config_dir = os.path.join(self.app.root_path, 'config')
        
        # Look for menu_*.json files that aren't role or base menus
        for filename in os.listdir(config_dir):
            if (filename.startswith('menu_') and 
                not filename.startswith('menu_role_') and 
                filename != 'menu_base.json' and 
                filename.endswith('.json')):
                
                source = filename[len('menu_'):-len('.json')]
                filepath = os.path.join(config_dir, filename)
                
                with open(filepath, 'r') as f:
                    menu_data = json.load(f)
                    self.source_menus[source] = menu_data.get('menu_items', [])
    
    def get_menu_for_user(self, user=None, ldap_source=None):
        """
        Get menu items for the current user based on roles and LDAP source
        
        Args:
            user: The current user object (defaults to g.user)
            ldap_source: The LDAP source to use (defaults to session)
            
        Returns:
            list: The merged and filtered menu items
        """
        if user is None:
            user = g.user if hasattr(g, 'user') else None
        
        if ldap_source is None:
            ldap_source = session.get('ldap_source', 'meta')
        
        # If no user or not authenticated, return empty menu
        if not user or not user.is_authenticated:
            return []
        
        # Get base menu according to user role
        role_menu = self._get_role_menu(user)
        
        # Get menu specific to LDAP source
        source_menu = self._get_source_menu(ldap_source)
        
        # Merge menus
        merged_menu = self._merge_menus(role_menu, source_menu)
        
        # Filter by user permissions
        filtered_menu = self._filter_menu_by_permissions(merged_menu, user)
        
        return filtered_menu
    
    def _get_role_menu(self, user):
        """Get menu based on user roles"""
        # If user has admin role, return admin menu
        if user.is_admin and 'admin' in self.role_menus:
            return copy.deepcopy(self.role_menus['admin'])
            
        # If user has reader role, return reader menu
        elif user.is_reader and 'reader' in self.role_menus:
            return copy.deepcopy(self.role_menus['reader'])
        
        # For other roles, combine their menus
        combined_menu = []
        for role in user.roles:
            if role in self.role_menus:
                for item in self.role_menus[role]:
                    if item not in combined_menu:
                        combined_menu.append(item)
        
        # If no role-specific menu found, fallback to default
        if not combined_menu:
            return copy.deepcopy(self.default_menu)
            
        return combined_menu
    
    def _get_source_menu(self, ldap_source):
        """Get menu based on LDAP source"""
        if ldap_source in self.source_menus:
            return copy.deepcopy(self.source_menus[ldap_source])
        return []
    
    def _merge_menus(self, role_menu, source_menu):
        """
        Merge role-based menu with source-specific menu
        
        The strategy is:
        1. Start with the role-based menu
        2. For each section in the source menu, find the corresponding section in role menu
        3. If section exists, merge its items intelligently
        4. If section doesn't exist, add it completely
        """
        merged_menu = copy.deepcopy(role_menu)
        
        # Create a lookup for sections in the role menu
        section_lookup = {}
        for i, item in enumerate(merged_menu):
            if item.get('is_section'):
                section_lookup[item.get('label', '').lower()] = i
        
        # Process each item in the source menu
        for source_item in source_menu:
            # If it's a section, try to merge with existing section
            if source_item.get('is_section'):
                section_label = source_item.get('label', '').lower()
                
                # If section already exists in role menu, merge items
                if section_label in section_lookup:
                    section_index = section_lookup[section_label]
                    section = merged_menu[section_index]
                    
                    # Merge items in this section
                    if 'items' in source_item and 'items' in section:
                        self._merge_section_items(section['items'], source_item['items'])
                
                # If section doesn't exist, add it
                else:
                    merged_menu.append(source_item)
                    section_lookup[section_label] = len(merged_menu) - 1
            
            # If it's a regular menu item, add if not already present
            else:
                if not any(item.get('url') == source_item.get('url') for item in merged_menu):
                    merged_menu.append(source_item)
        
        return merged_menu
    
    def _merge_section_items(self, existing_items, new_items):
        """Merge items within a section, adding new items that don't exist"""
        # Create lookup for existing items by URL
        item_lookup = {item.get('url', ''): i for i, item in enumerate(existing_items)}
        
        # Process each new item
        for new_item in new_items:
            url = new_item.get('url', '')
            
            # If item with this URL already exists, update its fields
            if url in item_lookup:
                # Preserve permissions from both sources
                existing_item = existing_items[item_lookup[url]]
                
                # Keep required_permission if it exists in either
                if 'required_permission' in new_item and 'required_permission' not in existing_item:
                    existing_item['required_permission'] = new_item['required_permission']
                
                # Update icon if a custom one is provided
                if 'icon' in new_item:
                    existing_item['icon'] = new_item['icon']
                
                # Update active pattern if provided
                if 'active_pattern' in new_item:
                    existing_item['active_pattern'] = new_item['active_pattern']
            
            # If item doesn't exist, add it
            else:
                existing_items.append(new_item)
                item_lookup[url] = len(existing_items) - 1
    
    def _filter_menu_by_permissions(self, menu, user):
        """Filter menu items based on user permissions"""
        filtered_menu = []
        
        for item in menu:
            # If it's a section, filter its items
            if item.get('is_section'):
                # Deep copy to avoid modifying original
                section_copy = copy.deepcopy(item)
                
                if 'items' in section_copy:
                    section_copy['items'] = self._filter_items_by_permissions(
                        section_copy['items'], user
                    )
                    
                    # Only include sections with items
                    if section_copy['items']:
                        filtered_menu.append(section_copy)
            
            # If it's a regular item, check permissions
            else:
                if self._check_item_permission(item, user):
                    filtered_menu.append(item)
        
        return filtered_menu
    
    def _filter_items_by_permissions(self, items, user):
        """Filter a list of menu items based on user permissions"""
        return [item for item in items if self._check_item_permission(item, user)]
    
    def _check_item_permission(self, item, user):
        """Check if user has permission to see a menu item"""
        # If item requires specific permission
        if 'required_permission' in item:
            return user.has_permission(item['required_permission'])
        
        # If item is admin-only
        if item.get('admin_only', False):
            return user.is_admin
        
        # Default: no restrictions
        return True
    
    def render_menu(self):
        """Render the menu HTML for the current user"""
        user = g.user if hasattr(g, 'user') else None
        ldap_source = session.get('ldap_source', 'meta')
        
        # Get menu items for current user and source
        menu_items = self.get_menu_for_user(user, ldap_source)
        
        # Render menu HTML
        return self._render_menu_html(menu_items)
    
    def _render_menu_html(self, menu_items):
        """Generate HTML for the menu items"""
        html = '<ul class="nav nav-pills flex-column mb-auto">'
        
        for item in menu_items:
            if item.get('is_section'):
                # Render section header
                html += f'<li class="nav-item mb-1 mt-3">'
                html += f'<h6 class="sidebar-heading px-3 mt-4 mb-1 text-muted">{item.get("label", "")}</h6>'
                html += '</li>'
                
                # Render section items
                if 'items' in item:
                    for subitem in item['items']:
                        html += self._render_menu_item(subitem)
            else:
                html += self._render_menu_item(item)
        
        html += '</ul>'
        return html
    
    def _render_menu_item(self, item):
        """Generate HTML for a single menu item"""
        url = item.get('url', '#')
        label = item.get('label', '')
        icon = item.get('icon', '')
        active_pattern = item.get('active_pattern', '')
        
        # Determine if this item is active
        is_active = self._is_item_active(active_pattern)
        active_class = 'active' if is_active else ''
        
        # Add LDAP source parameter to URL if needed
        if '?' not in url and url != '#':
            url += f'?source={session.get("ldap_source", "meta")}'
        
        # Generate HTML
        html = f'<li class="nav-item mb-1">'
        html += f'<a href="{url}" class="nav-link text-white {active_class}">'
        
        if icon:
            html += f'<i class="{icon} me-2"></i>'
            
        html += f'{label}'
        html += '</a></li>'
        
        return html
    
    def _is_item_active(self, active_pattern):
        """Determine if a menu item is active based on current request path"""
        import re
        from flask import request
        
        if not active_pattern:
            return False
            
        path = request.path
        return bool(re.match(active_pattern, path))