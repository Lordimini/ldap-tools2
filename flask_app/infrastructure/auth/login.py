# flask_app/application/auth/login.py
from typing import Dict, Any, Optional
from flask_app.domain.services.auth_service import AuthService
from flask_app.infrastructure.auth.session_manager import SessionManager
from flask_app.domain.dtos.auth_dtos import LoginRequestDTO, LoginResultDTO
from flask_app.domain.models.user import User


class LoginUseCase:
    """
    Cas d'utilisation pour l'authentification d'un utilisateur.
    Cette classe orchestre le processus de login et représente un cas d'utilisation
    selon l'architecture DDD (Domain-Driven Design).
    """
    
    def __init__(self, auth_service: AuthService, session_manager: SessionManager):
        """
        Initialise le cas d'utilisation avec les services nécessaires.
        
        Args:
            auth_service: Service d'authentification
            session_manager: Gestionnaire de session
        """
        self.auth_service = auth_service
        self.session_manager = session_manager
    
    def execute(self, username: str, password: str, ldap_source: str = 'meta', remember: bool = False) -> LoginResultDTO:
        """
        Exécute le cas d'utilisation de login.
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            ldap_source: Source LDAP à utiliser
            remember: Si True, la session sera persistante
            
        Returns:
            DTO contenant le résultat du login
        """
        try:
            # Créer le DTO de requête
            login_request = LoginRequestDTO(
                username=username,
                password=password,
                ldap_source=ldap_source,
                remember=remember
            )
            
            # Authentifier l'utilisateur via le service d'authentification
            success, user_data = self.auth_service.authenticate(
                username=login_request.username,
                password=login_request.password,
                ldap_source=login_request.ldap_source
            )
            
            if not success or not user_data:
                # Échec d'authentification
                return LoginResultDTO(
                    success=False,
                    error_message="Nom d'utilisateur ou mot de passe invalide."
                )
            
            # Créer l'objet User à partir des données LDAP
            user = User.from_ldap_data(
                username=username,
                user_data=user_data,
                ldap_source=ldap_source
            )
            
            # Créer une session pour l'utilisateur
            session_created = self.session_manager.create_session(
                user=user,
                remember=login_request.remember
            )
            
            if not session_created:
                # Échec de création de session
                return LoginResultDTO(
                    success=False,
                    error_message="Erreur lors de la création de la session."
                )
            
            # Définir la source LDAP active
            self.session_manager.set_active_ldap_source(ldap_source)
            
            # Succès du login
            return LoginResultDTO(
                success=True,
                user=user_data,
                redirect_url="/dashboard"
            )
            
        except Exception as e:
            # Gestion des erreurs inattendues
            return LoginResultDTO(
                success=False,
                error_message=f"Une erreur s'est produite: {str(e)}"
            )
    
    def logout(self) -> bool:
        """
        Déconnecte l'utilisateur actuel.
        
        Returns:
            True si la déconnexion a réussi, False sinon
        """
        try:
            return self.session_manager.destroy_session()
        except Exception as e:
            print(f"Erreur lors de la déconnexion: {str(e)}")
            return False