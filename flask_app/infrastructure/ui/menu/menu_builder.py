# flask_app/infrastructure/ui/menu/menu_builder.py
import os
import json
import re
from typing import List, Dict, Any, Optional
from flask import request, current_app
from flask_app.domain.models.menu_item import MenuItem
from flask_app.domain.models.user import User


class MenuBuilder:
    """
    Service pour la construction et la gestion des menus de l'interface utilisateur.
    """
    
    def __init__(self):
        """
        Initialise le constructeur de menu.
        """
        self.menu_configs = {}
        self.role_menus = {}
        self.default_menu = []
        self._load_menu_configs()
        self._prepare_role_menus()
    
    def _load_menu_configs(self):
        """
        Charge les configurations de menu depuis les fichiers JSON.
        """
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config')
        
        # Charger le menu de base
        base_menu_path = os.path.join(config_dir, 'menu_base.json')
        if os.path.exists(base_menu_path):
            with open(base_menu_path, 'r') as f:
                self.default_menu = json.load(f).get('menu_items', [])
        
        # Charger les configurations de menu spécifiques aux rôles
        for filename in os.listdir(config_dir):
            if filename.startswith('menu_') and filename.endswith('.json'):
                menu_name = filename[5:-5]  # Extraire le nom entre 'menu_' et '.json'
                file_path = os.path.join(config_dir, filename)
                
                with open(file_path, 'r') as f:
                    menu_data = json.load(f).get('menu_items', [])
                    
                    # Convertir les éléments de menu en objets MenuItem
                    menu_items = []
                    for item_data in menu_data:
                        menu_items.append(self._create_menu_item(item_data))
                    
                    self.menu_configs[menu_name] = menu_items
    
    def _create_menu_item(self, item_data: Dict[str, Any]) -> MenuItem:
        """
        Crée un objet MenuItem à partir des données JSON.
        
        Args:
            item_data: Données de l'élément de menu
            
        Returns:
            Objet MenuItem
        """
        # Récursivement créer les éléments enfants
        items = []
        if item_data.get('is_section') and 'items' in item_data:
            items = [self._create_menu_item(child_data) for child_data in item_data['items']]
        
        return MenuItem(
            label=item_data.get('label', ''),
            url=item_data.get('url', ''),
            icon=item_data.get('icon', ''),
            active_pattern=item_data.get('active_pattern', ''),
            is_section=item_data.get('is_section', False),
            items=items,
            required_permission=item_data.get('required_permission'),
            admin_only=item_data.get('admin_only', False),
            visible=item_data.get('visible', True),
            id=item_data.get('id')
        )
    
    def _prepare_role_menus(self):
        """
        Prépare les menus combinés pour chaque rôle.
        """
        # Admin obtient tous les éléments de menu
        if 'role_admin' in self.menu_configs:
            self.role_menus['admin'] = self.menu_configs['role_admin']
        else:
            # Si aucune configuration admin spécifique, utiliser default + admin items
            admin_menu = [self._create_menu_item(item) for item in self.default_menu]
            self.role_menus['admin'] = admin_menu
        
        # Reader obtient les éléments reader-specific + éléments communs
        if 'role_reader' in self.menu_configs:
            self.role_menus['reader'] = self.menu_configs['role_reader']
        else:
            # Filtrer les éléments admin-only du menu par défaut
            reader_menu = []
            for item in self.default_menu:
                if not item.get('admin_only', False):
                    reader_menu.append(self._create_menu_item(item))
            self.role_menus['reader'] = reader_menu
        
        # Pour les autres sources LDAP, créer selon les besoins
        for name, menu_items in self.menu_configs.items():
            if name.startswith('menu_') and name not in ['menu_base', 'menu_role_admin', 'menu_role_reader']:
                source_name = name[5:]  # Supprimer 'menu_'
                self.role_menus[source_name] = menu_items
    
    def get_menu_for_user(self, user: User, ldap_source: str = None) -> List[MenuItem]:
        """
        Obtient les éléments de menu appropriés pour un utilisateur donné.
        
        Args:
            user: Utilisateur pour lequel générer le menu
            ldap_source: Source LDAP à utiliser (optionnel)
            
        Returns:
            Liste des éléments de menu appropriés
        """
        # Si aucun utilisateur ou non authentifié, retourner un menu vide
        if not user or not user.is_authenticated:
            return []
        
        # Utiliser la source LDAP de l'utilisateur si non spécifiée
        if ldap_source is None:
            ldap_source = user.ldap_source
        
        # Vérifier si un menu spécifique à la source existe
        source_menu_key = ldap_source.lower()
        if source_menu_key in self.menu_configs:
            # Filtrer les éléments de menu selon les droits de l'utilisateur
            return self._filter_menu_items_for_user(self.menu_configs[source_menu_key], user)
        
        # Vérifier les rôles de l'utilisateur et retourner le menu approprié
        if user.is_admin and 'admin' in self.role_menus:
            return self._filter_menu_items_for_user(self.role_menus['admin'], user)
        elif user.is_reader and 'reader' in self.role_menus:
            return self._filter_menu_items_for_user(self.role_menus['reader'], user)
        
        # Créer un menu combiné basé sur les rôles de l'utilisateur
        combined_menu = []
        for role in user.roles:
            if role in self.role_menus:
                for item in self.role_menus[role]:
                    if item not in combined_menu and self._is_item_accessible(item, user):
                        combined_menu.append(item)
        
        # Si aucun menu spécifique au rôle trouvé, utiliser le menu par défaut
        if not combined_menu:
            default_items = [self._create_menu_item(item) for item in self.default_menu]
            combined_menu = self._filter_menu_items_for_user(default_items, user)
        
        return combined_menu
    
    def _filter_menu_items_for_user(self, menu_items: List[MenuItem], user: User) -> List[MenuItem]:
        """
        Filtre les éléments de menu en fonction des droits de l'utilisateur.
        
        Args:
            menu_items: Liste des éléments de menu à filtrer
            user: Utilisateur pour lequel filtrer
            
        Returns:
            Liste des éléments de menu filtrés
        """
        filtered_items = []
        
        for item in menu_items:
            if self._is_item_accessible(item, user):
                # Si c'est une section, filtrer ses éléments enfants aussi
                if item.is_section and item.items:
                    filtered_children = self._filter_menu_items_for_user(item.items, user)
                    
                    # Ne pas inclure la section si tous ses enfants sont filtrés
                    if filtered_children:
                        # Créer une copie de l'élément avec les enfants filtrés
                        filtered_item = MenuItem(
                            label=item.label,
                            url=item.url,
                            icon=item.icon,
                            active_pattern=item.active_pattern,
                            is_section=item.is_section,
                            items=filtered_children,
                            required_permission=item.required_permission,
                            admin_only=item.admin_only,
                            visible=item.visible,
                            id=item.id
                        )
                        filtered_items.append(filtered_item)
                else:
                    filtered_items.append(item)
        
        return filtered_items
    
    def _is_item_accessible(self, item: MenuItem, user: User) -> bool:
        """
        Vérifie si un élément de menu est accessible à un utilisateur.
        
        Args:
            item: Élément de menu à vérifier
            user: Utilisateur pour lequel vérifier
            
        Returns:
            True si l'élément est accessible, False sinon
        """
        # Vérifier la visibilité explicite
        if not item.visible:
            return False
        
        # Vérifier si admin-only
        if item.admin_only and not user.is_admin:
            return False
        
        # Vérifier les permissions requises
        if item.required_permission and not user.has_permission(item.required_permission):
            return False
        
        return True
    
    def is_menu_item_active(self, item: MenuItem, current_path: Optional[str] = None) -> bool:
        """
        Vérifie si un élément de menu doit être marqué comme actif.
        
        Args:
            item: Élément de menu à vérifier
            current_path: Chemin actuel, utilise request.path si non spécifié
            
        Returns:
            True si l'élément est actif, False sinon
        """
        if current_path is None:
            current_path = request.path if request else '/'
        
        return item.is_active(current_path)
    
    def render_menu(self, user: User, ldap_source: Optional[str] = None) -> str:
        """
        Génère le HTML du menu pour un utilisateur donné.
        
        Args:
            user: Utilisateur pour lequel générer le menu
            ldap_source: Source LDAP à utiliser (optionnel)
            
        Returns:
            HTML du menu sous forme de chaîne
        """
        # Obtenir les éléments de menu pour l'utilisateur
        menu_items = self.get_menu_for_user(user, ldap_source)
        
        if not menu_items:
            return '<ul class="nav flex-column"></ul>'
        
        # Path courant pour déterminer les éléments actifs
        current_path = request.path if request else '/'
        
        # Compteur pour générer des IDs uniques pour les sections
        section_counter = 0
        
        # Commencer à construire le HTML du menu
        html = '<ul class="nav flex-column">'
        
        for item in menu_items:
            # Vérifier si l'élément est une section avec des sous-éléments
            if item.is_section and item.items:
                # Incrémenter le compteur pour un ID unique
                section_counter += 1
                section_id = f'section-{section_counter}'
                
                # Vérifier si un des enfants est actif pour la classe de la section
                has_active_child = any(child.is_active(current_path) for child in item.items)
                section_expanded = 'show' if has_active_child else ''
                arrow_class = 'bi-chevron-up' if has_active_child else 'bi-chevron-down'
                
                # Rendre l'en-tête de la section
                html += f'''
                <li class="nav-item section-header">
                    <a class="nav-link d-flex justify-content-between align-items-center" 
                       data-bs-toggle="collapse" 
                       href="#{section_id}" 
                       role="button" 
                       aria-expanded="{str(has_active_child).lower()}" 
                       aria-controls="{section_id}">
                        <span>{item.label}</span>
                        <i class="bi {arrow_class} section-icon"></i>
                    </a>
                    <div class="collapse {section_expanded}" id="{section_id}">
                        <ul class="nav flex-column section-items">
                '''
                
                # Rendre les enfants de la section
                for child in item.items:
                    is_active = child.is_active(current_path)
                    active_class = 'active' if is_active else ''
                    
                    html += f'''
                    <li class="nav-item">
                        <a class="nav-link {active_class}" href="{child.url}">
                            <i class="{child.icon}"></i>
                            <span>{child.label}</span>
                        </a>
                    </li>
                    '''
                
                # Fermer la section
                html += '''
                        </ul>
                    </div>
                </li>
                '''
            else:
                # Rendre un élément régulier
                is_active = item.is_active(current_path)
                active_class = 'active' if is_active else ''
                
                html += f'''
                <li class="nav-item">
                    <a class="nav-link {active_class}" href="{item.url}">
                        <i class="{item.icon}"></i>
                        <span>{item.label}</span>
                    </a>
                </li>
                '''
        
        # Fermer la liste du menu
        html += '</ul>'
        
        return html
    
    def get_available_menus(self) -> Dict[str, str]:
        """
        Récupère la liste des menus disponibles.
        
        Returns:
            Dictionnaire des menus disponibles (id -> nom)
        """
        available_menus = {}
        
        # Menus de rôles
        available_menus['admin'] = 'Administration'
        available_menus['reader'] = 'Reader'
        
        # Menus de sources LDAP
        for name in self.menu_configs.keys():
            if name.startswith('menu_') and not name.startswith('menu_role_'):
                source_name = name[5:]  # Retirer 'menu_'
                display_name = source_name.upper()
                available_menus[source_name] = display_name
        
        return available_menus