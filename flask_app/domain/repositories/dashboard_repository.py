# flask_app/domain/repositories/dashboard_repository.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class DashboardRepository(ABC):
    """
    Interface définissant les opérations de persistance pour les statistiques du tableau de bord.
    """
    
    @abstractmethod
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques générales pour le tableau de bord.

        Returns:
            Dictionnaire contenant toutes les statistiques
        """
        pass
    
    @abstractmethod
    def get_total_users_count(self) -> int:
        """
        Récupère le nombre total d'utilisateurs.

        Returns:
            Nombre d'utilisateurs
        """
        pass
    
    @abstractmethod
    def get_recent_logins_count(self, days: int = 7) -> int:
        """
        Récupère le nombre d'utilisateurs qui se sont connectés récemment.

        Args:
            days: Nombre de jours à considérer

        Returns:
            Nombre d'utilisateurs récemment connectés
        """
        pass
    
    @abstractmethod
    def get_disabled_accounts_count(self) -> int:
        """
        Récupère le nombre de comptes désactivés.

        Returns:
            Nombre de comptes désactivés
        """
        pass
    
    @abstractmethod
    def get_inactive_users_count(self, months: int = 3) -> int:
        """
        Récupère le nombre d'utilisateurs actifs qui ne se sont pas connectés depuis X mois.

        Args:
            months: Nombre de mois d'inactivité

        Returns:
            Nombre d'utilisateurs inactifs
        """
        pass
    
    @abstractmethod
    def get_expired_password_users_count(self) -> int:
        """
        Récupère le nombre d'utilisateurs actifs dont le mot de passe est expiré.

        Returns:
            Nombre d'utilisateurs avec mot de passe expiré
        """
        pass
    
    @abstractmethod
    def get_never_logged_in_users_count(self) -> int:
        """
        Récupère le nombre d'utilisateurs actifs qui ne se sont jamais connectés.

        Returns:
            Nombre d'utilisateurs qui ne se sont jamais connectés
        """
        pass