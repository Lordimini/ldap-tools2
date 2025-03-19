# flask_app/app_initializer.py
from typing import Dict, Any
from flask import Flask

from flask_app.infrastructure.persistence.repository_factory import RepositoryFactory
from flask_app.config.meta_config import meta_login_config
from flask_app.config.idme_config import idme_login_config

from flask_app.application.auth.login import LoginUseCase
from flask_app.application.user_management.search_user import SearchUserUseCase
from flask_app.application.user_management.create_user import CreateUserUseCase
from flask_app.application.user_management.update_user import UpdateUserUseCase
from flask_app.application.group_management.add_user_to_group import AddUserToGroupUseCase
from flask_app.application.group_management.create_group import CreateGroupUseCase

from flask_app.domain.services.auth_service import AuthService
from flask_app.domain.services.user_service import UserService
from flask_app.domain.services.group_service import GroupService
from flask_app.domain.services.role_service import RoleService
from flask_app.domain.services.service_service import ServiceService
from flask_app.domain.services.template_service import TemplateService
from flask_app.domain.services.menu_service import MenuService
from flask_app.domain.services.dashboard_service import DashboardService
from flask_app.domain.services.autocomplete_service import AutocompleteService

from flask_app.infrastructure.auth.ldap_authenticator import LDAPAuthenticator
from flask_app.infrastructure.auth.session_manager import SessionManager
from flask_app.infrastructure.ui.menu.menu_builder import MenuBuilder


class AppInitializer:
    """
    Classe responsable de l'initialisation et de la configuration 
    de l'application selon les principes SOLID.
    """
    
    def __init__(self, app: Flask):
        """
        Initialise la classe avec l'application Flask.
        
        Args:
            app: L'application Flask à configurer
        """
        self.app = app
        self.repository_factory = RepositoryFactory()
        
        # Configurer les sources LDAP
        self._configure_ldap_sources()
        
        # Initialiser les services et les cas d'utilisation
        self._initialize_services()
        self._initialize_use_cases()
        
        # Attacher les services à l'application Flask
        self._attach_services_to_app()
    
    def _configure_ldap_sources(self) -> None:
        """
        Configure les différentes sources LDAP disponibles.
        """
        # Source Meta
        self.repository_factory.configure_ldap_source('meta', meta_login_config)
        
        # Source IDME
        self.repository_factory.configure_ldap_source('idme', idme_login_config)
        
        # Ajouter d'autres sources LDAP au besoin
    
    def _initialize_services(self) -> None:
        """
        Initialise les services de l'application avec les dépendances appropriées.
        """
        # Création des services pour la source META (par défaut)
        self._create_services_for_source('meta')
        
        # Création des services pour d'autres sources
        self._create_services_for_source('idme')
        
        # Services qui ne dépendent pas d'une source LDAP spécifique
        self.session_manager = SessionManager()
        self.menu_builder = MenuBuilder()
    
    def _create_services_for_source(self, source_name: str) -> None:
        """
        Crée les services pour une source spécifique.
        
        Args:
            source_name: Nom de la source LDAP
        """
        # Obtenir les repositories pour cette source
        user_repo = self.repository_factory.get_user_repository(source_name)
        group_repo = self.repository_factory.get_group_repository(source_name)
        role_repo = self.repository_factory.get_role_repository(source_name)
        service_repo = self.repository_factory.get_service_repository(source_name)
        template_repo = self.repository_factory.get_template_repository(source_name)
        autocomplete_repo = self.repository_factory.get_autocomplete_repository(source_name)
        dashboard_repo = self.repository_factory.get_dashboard_repository(source_name)
        
        # Créer les services avec les repositories appropriés
        authenticator = LDAPAuthenticator(user_repo)
        
        # Stocker les services par source dans un dictionnaire pour un accès facile
        if not hasattr(self, 'services'):
            self.services = {}
        
        if source_name not in self.services:
            self.services[source_name] = {}
        
        # Initialiser les services avec leurs dépendances
        self.services[source_name]['auth_service'] = AuthService(authenticator, self.session_manager)
        self.services[source_name]['user_service'] = UserService(user_repo, template_repo)
        self.services[source_name]['group_service'] = GroupService(group_repo, user_repo)
        self.services[source_name]['role_service'] = RoleService(role_repo)
        self.services[source_name]['service_service'] = ServiceService(service_repo)
        self.services[source_name]['template_service'] = TemplateService(template_repo)
        self.services[source_name]['autocomplete_service'] = AutocompleteService(autocomplete_repo)
        self.services[source_name]['dashboard_service'] = DashboardService(dashboard_repo)
        self.services[source_name]['menu_service'] = MenuService(self.menu_builder)
    
    def _initialize_use_cases(self) -> None:
        """
        Initialise les cas d'utilisation de l'application.
        """
        # Cas d'utilisation pour l'authentification
        self.login_use_case = LoginUseCase(
            self.services['meta']['auth_service'],
            self.session_manager
        )
        
        # Cas d'utilisation pour la gestion des utilisateurs
        self.search_user_use_case = SearchUserUseCase(self.services['meta']['user_service'])
        self.create_user_use_case = CreateUserUseCase(
            self.services['meta']['user_service'],
            self.services['meta']['template_service']
        )
        self.update_user_use_case = UpdateUserUseCase(self.services['meta']['user_service'])
        
        # Cas d'utilisation pour la gestion des groupes
        self.add_user_to_group_use_case = AddUserToGroupUseCase(
            self.services['meta']['group_service'],
            self.services['meta']['user_service']
        )
        self.create_group_use_case = CreateGroupUseCase(self.services['meta']['group_service'])
        
        # Ajouter d'autres cas d'utilisation au besoin
    
    def _attach_services_to_app(self) -> None:
        """
        Attache les services à l'application Flask pour un accès facile.
        """
        # Attachement des dépendances principales
        self.app.repository_factory = self.repository_factory
        self.app.session_manager = self.session_manager
        self.app.menu_builder = self.menu_builder
        
        # Attachement des services par source
        self.app.services = self.services
        
        # Attachement des cas d'utilisation
        self.app.login_use_case = self.login_use_case
        self.app.search_user_use_case = self.search_user_use_case
        self.app.create_user_use_case = self.create_user_use_case
        self.app.update_user_use_case = self.update_user_use_case
        self.app.add_user_to_group_use_case = self.add_user_to_group_use_case
        self.app.create_group_use_case = self.create_group_use_case
        
        # Helper pour obtenir le service actif selon la source LDAP actuelle
        def get_active_service(service_name: str):
            active_ldap_source = self.session_manager.get_active_ldap_source()
            return self.services[active_ldap_source][service_name]
        
        self.app.get_active_service = get_active_service


def initialize_app(app: Flask) -> None:
    """
    Fonction utilitaire pour initialiser l'application.
    
    Args:
        app: L'application Flask à initialiser
    """
    initializer = AppInitializer(app)
    return app