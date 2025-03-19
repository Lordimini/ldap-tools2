# flask_app/infrastructure/auth/session_manager.py
from typing import Dict, Any, Optional
from flask import session, g
from flask_login import login_user, logout_user, current_user
from flask_app.domain.models.user import User


class SessionManager:
    """
    Service de gestion des sessions utilisateur.
    """
    
    def __init__(self):
        """
        Initialise le gestionnaire de session.
        """
        pass
    
    def create_session(self, user: User, remember: bool = False) -> bool:
        """
        Crée une session pour un utilisateur.
        
        Args:
            user: Utilisateur à connecter
            remember: Si True, la session persistera au-delà de la fermeture du navigateur
            
        Returns:
            True si la session a été créée avec succès, False sinon
        """
        try:
            # Utiliser Flask-Login pour gérer la session
            login_user(user, remember=remember)
            
            # Stocker des informations supplémentaires dans la session Flask
            session['logged_in'] = True
            session['username'] = user.username
            session['roles'] = user.roles
            session['ldap_source'] = user.ldap_source
            
            return True
        except Exception as e:
            print(f"Erreur lors de la création de la session: {str(e)}")
            return False
    
    def destroy_session(self) -> bool:
        """
        Détruit la session actuelle.
        
        Returns:
            True si la session a été détruite avec succès, False sinon
        """
        try:
            # Utiliser Flask-Login pour déconnecter l'utilisateur
            logout_user()
            
            # Nettoyer la session Flask
            session.clear()
            
            return True
        except Exception as e:
            print(f"Erreur lors de la destruction de la session: {str(e)}")
            return False
    
    def get_current_user(self) -> Optional[User]:
        """
        Obtient l'utilisateur actuellement connecté.
        
        Returns:
            L'utilisateur actuel ou None si aucun utilisateur n'est connecté
        """
        if hasattr(g, 'user') and g.user:
            return g.user
        return current_user if current_user.is_authenticated else None
    
    def set_session_data(self, key: str, value: Any) -> None:
        """
        Définit une donnée dans la session.
        
        Args:
            key: Clé de la donnée
            value: Valeur à stocker
        """
        session[key] = value
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """
        Récupère une donnée de la session.
        
        Args:
            key: Clé de la donnée à récupérer
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            La valeur associée à la clé ou la valeur par défaut
        """
        return session.get(key, default)
    
    def set_active_ldap_source(self, source: str) -> bool:
        """
        Définit la source LDAP active pour l'utilisateur courant.
        
        Args:
            source: Identifiant de la source LDAP (meta, idme, etc.)
            
        Returns:
            True si la source a été définie, False sinon
        """
        try:
            session['ldap_source'] = source
            
            # Mettre à jour la source LDAP de l'utilisateur actuel si disponible
            current_user = self.get_current_user()
            if current_user:
                current_user.ldap_source = source
            
            return True
        except Exception as e:
            print(f"Erreur lors de la définition de la source LDAP active: {str(e)}")
            return False
    
    def get_active_ldap_source(self) -> str:
        """
        Récupère la source LDAP active pour l'utilisateur courant.
        
        Returns:
            Identifiant de la source LDAP active ou 'meta' par défaut
        """
        # Vérifier d'abord dans la session
        source = self.get_session_data('ldap_source')
        if source:
            return source
        
        # Puis vérifier dans les données de l'utilisateur actuel
        current_user = self.get_current_user()
        if current_user and hasattr(current_user, 'ldap_source'):
            return current_user.ldap_source
        
        # Valeur par défaut
        return 'meta'