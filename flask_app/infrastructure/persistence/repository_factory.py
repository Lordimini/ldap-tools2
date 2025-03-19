# flask_app/infrastructure/persistence/repository_factory.py
from typing import Dict, Any, Optional

from flask_app.domain.repositories.user_repository import UserRepository
from flask_app.domain.repositories.group_repository import GroupRepository
from flask_app.domain.repositories.role_repository import RoleRepository
from flask_app.domain.repositories.service_repository import ServiceRepository
from flask_app.domain.repositories.template_repository import TemplateRepository
from flask_app.domain.repositories.autocomplete_repository import AutocompleteRepository
from flask_app.domain.repositories.dashboard_repository import DashboardRepository

from flask_app.infrastructure.persistence.ldap.ldap_connection import LDAPConnectionProvider
from flask_app.infrastructure.persistence.ldap.ldap_user_repo import LDAPUserRepository
from flask_app.infrastructure.persistence.ldap.ldap_group_repo import LDAPGroupRepository
from flask_app.infrastructure.persistence.ldap.ldap_role_repo import LDAPRoleRepository
from flask_app.infrastructure.persistence.ldap.ldap_service_repo import LDAPServiceRepository
from flask_app.infrastructure.persistence.ldap.ldap_template_repo import LDAPTemplateRepository
from flask_app.infrastructure.persistence.ldap.ldap_autocomplete_repo import LDAPAutocompleteRepository
from flask_app.infrastructure.persistence.ldap.ldap_dashboard_repo import LDAPDashboardRepository


class RepositoryFactory:
    """
    Fabrique pour créer des instances de repositories.
    Cette classe implémente le pattern Factory pour créer des repositories
    en fonction de la source de données et injecter les dépendances appropriées.
    """
    
    def __init__(self):
        """
        Initialise la fabrique de repositories.
        """
        self._connection_providers = {}
        self._repositories = {}
    
    def configure_ldap_source(self, source_name: str, config: Dict[str, Any]) -> None:
        """
        Configure une source LDAP avec la configuration spécifiée.
        
        Args:
            source_name: Nom de la source LDAP
            config: Configuration LDAP
        """
        # Créer un provider de connexion pour cette source
        connection_provider = LDAPConnectionProvider(config)
        self._connection_providers[source_name] = connection_provider
    
    def get_user_repository(self, source_name: str = 'meta') -> UserRepository:
        """
        Obtient un repository d'utilisateur pour la source spécifiée.
        
        Args:
            source_name: Nom de la source de données
            
        Returns:
            Instance de UserRepository
        """
        repo_key = f"{source_name}:user"
        
        # Vérifier si le repository existe déjà
        if repo_key in self._repositories:
            return self._repositories[repo_key]
        
        # Vérifier si la source LDAP est configurée
        if source_name not in self._connection_providers:
            raise ValueError(f"Source LDAP '{source_name}' non configurée")
        
        # Créer une nouvelle instance du repository avec le provider approprié
        connection_provider = self._connection_providers[source_name]
        user_repo = LDAPUserRepository(connection_provider)
        
        # Mettre en cache le repository pour une utilisation future
        self._repositories[repo_key] = user_repo
        
        return user_repo
    
    def get_group_repository(self, source_name: str = 'meta') -> GroupRepository:
        """
        Obtient un repository de groupe pour la source spécifiée.
        
        Args:
            source_name: Nom de la source de données
            
        Returns:
            Instance de GroupRepository
        """
        repo_key = f"{source_name}:group"
        
        # Vérifier si le repository existe déjà
        if repo_key in self._repositories:
            return self._repositories[repo_key]
        
        # Vérifier si la source LDAP est configurée
        if source_name not in self._connection_providers:
            raise ValueError(f"Source LDAP '{source_name}' non configurée")
        
        # Créer une nouvelle instance du repository avec le provider approprié
        connection_provider = self._connection_providers[source_name]
        group_repo = LDAPGroupRepository(connection_provider)
        
        # Mettre en cache le repository pour une utilisation future
        self._repositories[repo_key] = group_repo
        
        return group_repo
    
    def get_role_repository(self, source_name: str = 'meta') -> RoleRepository:
        """
        Obtient un repository de rôle pour la source spécifiée.
        
        Args:
            source_name: Nom de la source de données
            
        Returns:
            Instance de RoleRepository
        """
        repo_key = f"{source_name}:role"
        
        # Vérifier si le repository existe déjà
        if repo_key in self._repositories:
            return self._repositories[repo_key]
        
        # Vérifier si la source LDAP est configurée
        if source_name not in self._connection_providers:
            raise ValueError(f"Source LDAP '{source_name}' non configurée")
        
        # Créer une nouvelle instance du repository avec le provider approprié
        connection_provider = self._connection_providers[source_name]
        role_repo = LDAPRoleRepository(connection_provider)
        
        # Mettre en cache le repository pour une utilisation future
        self._repositories[repo_key] = role_repo
        
        return role_repo
    
    def get_service_repository(self, source_name: str = 'meta') -> ServiceRepository:
        """
        Obtient un repository de service pour la source spécifiée.
        
        Args:
            source_name: Nom de la source de données
            
        Returns:
            Instance de ServiceRepository
        """
        repo_key = f"{source_name}:service"
        
        # Vérifier si le repository existe déjà
        if repo_key in self._repositories:
            return self._repositories[repo_key]
        
        # Vérifier si la source LDAP est configurée
        if source_name not in self._connection_providers:
            raise ValueError(f"Source LDAP '{source_name}' non configurée")
        
        # Créer une nouvelle instance du repository avec le provider approprié
        connection_provider = self._connection_providers[source_name]
        service_repo = LDAPServiceRepository(connection_provider)
        
        # Mettre en cache le repository pour une utilisation future
        self._repositories[repo_key] = service_repo
        
        return service_repo
    
    def get_template_repository(self, source_name: str = 'meta') -> TemplateRepository:
        """
        Obtient un repository de template pour la source spécifiée.
        
        Args:
            source_name: Nom de la source de données
            
        Returns:
            Instance de TemplateRepository
        """
        repo_key = f"{source_name}:template"
        
        # Vérifier si le repository existe déjà
        if repo_key in self._repositories:
            return self._repositories[repo_key]
        
        # Vérifier si la source LDAP est configurée
        if source_name not in self._connection_providers:
            raise ValueError(f"Source LDAP '{source_name}' non configurée")
        
        # Créer une nouvelle instance du repository avec le provider approprié
        connection_provider = self._connection_providers[source_name]
        template_repo = LDAPTemplateRepository(connection_provider)
        
        # Mettre en cache le repository pour une utilisation future
        self._repositories[repo_key] = template_repo
        
        return template_repo
    
    def get_autocomplete_repository(self, source_name: str = 'meta') -> AutocompleteRepository:
        """
        Obtient un repository d'autocomplétion pour la source spécifiée.
        
        Args:
            source_name: Nom de la source de données
            
        Returns:
            Instance de AutocompleteRepository
        """
        repo_key = f"{source_name}:autocomplete"
        
        # Vérifier si le repository existe déjà
        if repo_key in self._repositories:
            return self._repositories[repo_key]
        
        # Vérifier si la source LDAP est configurée
        if source_name not in self._connection_providers:
            raise ValueError(f"Source LDAP '{source_name}' non configurée")
        
        # Créer une nouvelle instance du repository avec le provider approprié
        connection_provider = self._connection_providers[source_name]
        autocomplete_repo = LDAPAutocompleteRepository(connection_provider)
        
        # Mettre en cache le repository pour une utilisation future
        self._repositories[repo_key] = autocomplete_repo
        
        return autocomplete_repo
    
    def get_dashboard_repository(self, source_name: str = 'meta') -> DashboardRepository:
        """
        Obtient un repository de tableau de bord pour la source spécifiée.
        
        Args:
            source_name: Nom de la source de données
            
        Returns:
            Instance de DashboardRepository
        """
        repo_key = f"{source_name}:dashboard"
        
        # Vérifier si le repository existe déjà
        if repo_key in self._repositories:
            return self._repositories[repo_key]
        
        # Vérifier si la source LDAP est configurée
        if source_name not in self._connection_providers:
            raise ValueError(f"Source LDAP '{source_name}' non configurée")
        
        # Créer une nouvelle instance du repository avec le provider approprié
        connection_provider = self._connection_providers[source_name]
        dashboard_repo = LDAPDashboardRepository(connection_provider)
        
        # Mettre en cache le repository pour une utilisation future
        self._repositories[repo_key] = dashboard_repo
        
        return dashboard_repo
    
    def clear_cache(self, source_name: Optional[str] = None) -> None:
        """
        Efface le cache des repositories.
        
        Args:
            source_name: Nom de la source à effacer, ou None pour effacer toutes les sources
        """
        if source_name:
            # Effacer seulement les repositories de la source spécifiée
            keys_to_remove = [k for k in self._repositories.keys() if k.startswith(f"{source_name}:")]
            for key in keys_to_remove:
                del self._repositories[key]
        else:
            # Effacer tous les repositories
            self._repositories.clear()