# flask_app/infrastructure/persistence/ldap/ldap_connection.py
from typing import Dict, Any, Optional, List
from ldap3 import Server, Connection, ALL
import threading
import time
import logging

logger = logging.getLogger(__name__)

class LDAPConnection:
    """
    Classe pour établir et gérer une connexion LDAP.
    Implémente une connexion simple à usage unique.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise une nouvelle connexion LDAP avec les paramètres de configuration.
        
        Args:
            config: Configuration LDAP contenant les paramètres de connexion
        """
        self.config = config
        self.server = Server(config['ldap_server'], get_info=ALL)
        self.connection = None
    
    def connect(self, bind_dn: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Établit une connexion au serveur LDAP.
        
        Args:
            bind_dn: DN utilisateur pour la connexion (utilise bind_dn de config si None)
            password: Mot de passe (utilise bind_password de config si None)
            
        Returns:
            True si connexion réussie, False sinon
        """
        try:
            # Utiliser les identifiants fournis ou les valeurs par défaut de la config
            bind_dn = bind_dn or self.config['bind_dn']
            password = password or self.config['bind_password']
            
            self.connection = Connection(
                self.server,
                user=bind_dn,
                password=password,
                auto_bind=True
            )
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion LDAP: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        Déconnecte du serveur LDAP.
        """
        if self.connection:
            self.connection.unbind()
            self.connection = None
    
    def is_connected(self) -> bool:
        """
        Vérifie si la connexion est active.
        
        Returns:
            True si la connexion est active, False sinon
        """
        return self.connection is not None and self.connection.bound


class LDAPConnectionProvider:
    """
    Fournisseur de connexions LDAP avec gestion de pool de connexions.
    Cette classe implémente un pattern de pool de connexions pour 
    réutiliser les connexions et optimiser les performances.
    """
    
    def __init__(self, config: Dict[str, Any], pool_size: int = 5, max_lifetime: int = 300):
        """
        Initialise le fournisseur de connexions avec la configuration LDAP.
        
        Args:
            config: Configuration LDAP contenant les paramètres de connexion
            pool_size: Taille maximale du pool de connexions
            max_lifetime: Durée de vie maximale d'une connexion en secondes
        """
        self.config = config
        self.pool_size = pool_size
        self.max_lifetime = max_lifetime
        self.pool = []
        self.lock = threading.RLock()
        self.connections_created = 0
    
    def get_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration LDAP utilisée par ce fournisseur.
        
        Returns:
            Configuration LDAP
        """
        return self.config
    
    def get_connection(self) -> Connection:
        """
        Obtient une connexion LDAP du pool ou en crée une nouvelle si nécessaire.
        
        Returns:
            Connexion LDAP active
        """
        with self.lock:
            # Nettoyer les connexions expirées ou inactives
            self._cleanup_connections()
            
            # Vérifier s'il y a des connexions disponibles dans le pool
            if self.pool:
                connection = self.pool.pop()
                return connection.connection
            
            # Créer une nouvelle connexion si le pool est vide ou si toutes les connexions sont utilisées
            if self.connections_created < self.pool_size:
                conn = LDAPConnection(self.config)
                if conn.connect():
                    self.connections_created += 1
                    return conn.connection
            
            # Si on dépasse la limite de pool, attendre qu'une connexion se libère
            logger.warning("Pool de connexions LDAP saturé, attente d'une connexion disponible")
            
            # Attente simple, pourrait être amélioré avec une file d'attente et des conditions
            max_wait = 5  # Attendre au maximum 5 secondes
            wait_time = 0.1
            waited = 0
            
            while waited < max_wait:
                time.sleep(wait_time)
                waited += wait_time
                
                # Vérifier à nouveau le pool
                self._cleanup_connections()
                if self.pool:
                    connection = self.pool.pop()
                    return connection.connection
            
            # En dernier recours, créer une connexion surnuméraire
            logger.error("Création d'une connexion LDAP en dehors du pool")
            conn = LDAPConnection(self.config)
            if conn.connect():
                return conn.connection
            
            raise Exception("Impossible d'établir une connexion LDAP")
    
    def release_connection(self, connection: Connection) -> None:
        """
        Libère une connexion et la remet dans le pool si possible.
        
        Args:
            connection: Connexion LDAP à libérer
        """
        with self.lock:
            # Vérifier si la connexion est toujours valide
            if connection and connection.bound:
                # Créer un wrapper pour la connexion avec timestamp
                conn_wrapper = {
                    'connection': connection,
                    'timestamp': time.time()
                }
                
                # Remettre la connexion dans le pool si la taille le permet
                if len(self.pool) < self.pool_size:
                    self.pool.append(conn_wrapper)
                else:
                    # Fermer la connexion si le pool est plein
                    try:
                        connection.unbind()
                    except Exception as e:
                        logger.error(f"Erreur lors de la fermeture de connexion: {e}")
                    finally:
                        self.connections_created -= 1
    
    def _cleanup_connections(self) -> None:
        """
        Nettoie les connexions expirées ou fermées du pool.
        """
        current_time = time.time()
        active_connections = []
        
        for conn_wrapper in self.pool:
            connection = conn_wrapper['connection']
            timestamp = conn_wrapper['timestamp']
            
            # Vérifier si la connexion est expirée ou fermée
            if (current_time - timestamp > self.max_lifetime) or not connection.bound:
                # Fermer la connexion expirée
                try:
                    connection.unbind()
                except Exception:
                    pass
                finally:
                    self.connections_created -= 1
            else:
                # Garder la connexion active
                active_connections.append(conn_wrapper)
        
        # Mettre à jour le pool avec seulement les connexions actives
        self.pool = active_connections
    
    def close_all_connections(self) -> None:
        """
        Ferme toutes les connexions du pool.
        """
        with self.lock:
            for conn_wrapper in self.pool:
                try:
                    conn_wrapper['connection'].unbind()
                except Exception:
                    pass
            
            self.pool = []
            self.connections_created = 0