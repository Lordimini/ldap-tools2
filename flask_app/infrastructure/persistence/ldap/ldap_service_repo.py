# flask_app/infrastructure/persistence/ldap/ldap_service_repo.py
from typing import List, Optional, Dict, Any
from flask_app.domain.repositories.service_repository import ServiceRepository
from flask_app.domain.models.service import Service
from flask_app.domain.models.result import Result
from flask_app.infrastructure.persistence.ldap.ldap_connection import LDAPConnection
from ldap3 import SUBTREE


class LDAPServiceRepository(ServiceRepository):
    """
    Implémentation LDAP pour le repository de service (unité organisationnelle).
    Cette classe implémente les méthodes définies dans l'interface ServiceRepository
    en utilisant le protocole LDAP pour interagir avec le serveur d'annuaire.
    """
    
    def __init__(self, connection_provider):
        """
        Initialise le repository avec un fournisseur de connexion LDAP.
        
        Args:
            connection_provider: Fournisseur de connexion LDAP qui gère le pool de connexions
        """
        self.connection_provider = connection_provider
        self.config = connection_provider.get_config()
    
    def get_service_users(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les utilisateurs d'un service donné.
        
        Args:
            service_name: Nom du service (ou)
            
        Returns:
            Dictionnaire contenant les informations du service et la liste des utilisateurs
        """
        conn = self.connection_provider.get_connection()
        try:
            users = []
            
            # S'assurer que actif_users_dn est une liste
            base_dns = self.config['actif_users_dn']
            if not isinstance(base_dns, list):
                base_dns = [base_dns]
            
            # Échapper le service_name pour éviter les injections LDAP
            service_name_escaped = self._escape_ldap_filter(service_name)
            
            # Parcourir tous les base_dn valides
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré dans get_service_users: {base_dn}")
                    continue
                
                try:
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(ou={service_name_escaped})',
                        search_scope=SUBTREE,
                        attributes=['cn', 'fullName', 'title', 'mail']
                    )
                    
                    # Traiter les résultats
                    for entry in conn.entries:
                        users.append({
                            'CN': entry.cn.value if hasattr(entry, 'cn') else 'Unknown',
                            'fullName': entry.fullName.value if hasattr(entry, 'fullName') else 'Unknown',
                            'title': entry.title.value if hasattr(entry, 'title') else 'N/A',
                            'mail': entry.mail.value if hasattr(entry, 'mail') else 'N/A'
                        })
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    continue
            
            if users:
                result = {
                    'service_name': service_name,
                    'users': users
                }
                return result
            
            return None
            
        except Exception as e:
            print(f"Erreur dans get_service_users: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_managers(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des utilisateurs marqués comme managers (FavvDienstHoofd=YES).
        
        Returns:
            Liste des utilisateurs managers
        """
        conn = self.connection_provider.get_connection()
        try:
            managers = []
            
            # Rechercher les utilisateurs avec FavvDienstHoofd=YES
            search_base = self.config['actif_users_dn']
            search_filter = '(FavvDienstHoofd=YES)'
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['cn', 'fullName', 'title', 'mail']
            )
            
            for entry in conn.entries:
                managers.append({
                    'dn': entry.entry_dn,
                    'fullName': entry.fullName.value if hasattr(entry, 'fullName') else '',
                    'title': entry.title.value if hasattr(entry, 'title') else '',
                    'mail': entry.mail.value if hasattr(entry, 'mail') else ''
                })
            
            return managers
            
        except Exception as e:
            print(f"Erreur lors de la récupération des managers: {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Recherche des services par nom.
        
        Args:
            search_term: Terme de recherche
            
        Returns:
            Liste des services correspondant au critère
        """
        conn = self.connection_provider.get_connection()
        try:
            services = []
            unique_services = set()  # Pour éviter les doublons
            
            # Échapper le terme de recherche
            search_term_escaped = self._escape_ldap_filter(search_term)
            
            # Bases DN à rechercher
            base_dns = [self.config['app_base_dn'], self.config['base_dn']]
            
            # Parcourir toutes les bases DN
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré dans search_services: {base_dn}")
                    continue
                
                try:
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(ou=*{search_term_escaped}*)',
                        search_scope=SUBTREE,
                        attributes=['ou', 'description'],
                        size_limit=50,  # Limiter le nombre de résultats
                        time_limit=5     # Limiter le temps de recherche en secondes
                    )
                    
                    # Ajouter chaque service unique à la liste
                    for entry in conn.entries:
                        if hasattr(entry, 'ou') and entry.ou and entry.ou.value:
                            service_name = entry.ou.value
                            # Éviter les doublons
                            if service_name.lower() not in unique_services:
                                unique_services.add(service_name.lower())
                                
                                service_data = {
                                    'name': service_name,
                                    'description': entry.description.value if hasattr(entry, 'description') and entry.description else None
                                }
                                
                                services.append(service_data)
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    continue
            
            # Trier les services par ordre alphabétique
            services.sort(key=lambda x: x['name'])
            
            # Limiter le nombre de résultats retournés
            services = services[:20]
            
            return services
            
        except Exception as e:
            print(f"Erreur lors de la recherche de services: {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def _escape_ldap_filter(self, input_string: str) -> str:
        """
        Échappe les caractères spéciaux dans un filtre LDAP.
        
        Args:
            input_string: Chaîne d'entrée à échapper
            
        Returns:
            Chaîne échappée pour filtre LDAP
        """
        if not input_string:
            return ""
        
        # Échapper les caractères spéciaux selon la RFC 2254
        special_chars = {
            '\\': r'\5c',
            '*': r'\2a',
            '(': r'\28',
            ')': r'\29',
            '\0': r'\00'
        }
        
        result = input_string
        for char, replacement in special_chars.items():
            result = result.replace(char, replacement)
        
        return result