# flask_app/services/menu_service.py
import json
import os
import re
from flask import session, request, current_app

class MenuService:
    """
    Service for managing dynamic menus based on LDAP source
    """
    
    def __init__(self, app=None):
        self.app = app
        self.menu_cache = {}
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        # Initialize cache with available menu configurations
        self._load_menu_configs()
    
    def _load_menu_configs(self):
        """Load all menu configuration files into the cache"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        
        # Look for all menu_*.json files
        for filename in os.listdir(config_dir):
            if filename.startswith('menu_') and filename.endswith('.json'):
                source_name = filename[5:-5]  # Extract name between 'menu_' and '.json'
                file_path = os.path.join(config_dir, filename)
                
                with open(file_path, 'r') as f:
                    self.menu_cache[source_name] = json.load(f)
    
    def get_menu_for_current_source(self):
        """Get menu items for the current LDAP source"""
        # Get current source from session or from ldap_config_manager
        try:
            if hasattr(current_app, 'ldap_config_manager') and hasattr(current_app.ldap_config_manager, 'get_active_config_name'):
                current_source = current_app.ldap_config_manager.get_active_config_name()
            else:
                current_source = session.get('ldap_source', 'ldap')
        except Exception as e:
            print(f"Error getting current source: {e}")
            current_source = 'ldap'  # Fallback to default
            
        return self.get_menu_for_source(current_source)
    
    def get_menu_for_source(self, source):
        """Get menu items for a specific source"""
        # Normalize the source name to match the menu config files
        source_key = source.lower().replace(' ', '_')
        
        if source_key not in self.menu_cache:
            # Default to standard LDAP if source not found
            source_key = 'ldap'
        
        return self.menu_cache.get(source_key, {}).get('menu_items', [])
    
    def render_menu(self):
        """Render the menu HTML for the current source"""
        menu_items = self.get_menu_for_current_source()
        current_path = request.path
        
        html = '<ul class="nav flex-column">'
        
        for item in menu_items:
            # Skip items that are explicitly set to not visible
            if item.get('visible') is False:
                continue
                
            if item.get('is_section'):
                # Render section header
                html += f'<div class="sidebar-heading">{item["label"]}</div>'
                
                # Render section items (only if they're visible)
                for sub_item in item.get('items', []):
                    # Skip sub-items that are explicitly set to not visible
                    if sub_item.get('visible') is False:
                        continue
                        
                    is_active = self._is_active(sub_item, current_path)
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
                is_active = self._is_active(item, current_path)
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
    
    def _is_active(self, item, current_path):
        """Check if a menu item should be marked as active"""
        if 'active_pattern' in item:
            return re.search(item['active_pattern'], current_path) is not None
        else:
            return current_path == item['url']
    
    def get_available_sources(self):
        """Get a list of available LDAP sources"""
        if hasattr(current_app, 'ldap_config_manager'):
            return current_app.ldap_config_manager.get_available_configs()
        else:
            # Return keys from menu_cache as fallback
            return list(self.menu_cache.keys())
    
    def get_active_source(self):
        """Get the currently active LDAP source"""
        if hasattr(current_app, 'ldap_config_manager'):
            return current_app.ldap_config_manager.get_active_config_name()
        else:
            return session.get('ldap_source', 'ldap')