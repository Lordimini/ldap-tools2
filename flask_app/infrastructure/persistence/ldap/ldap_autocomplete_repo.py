# flask_app/infrastructure/persistence/ldap/ldap_autocomplete_repo.py
from typing import List, Dict, Any
from flask_app.domain.repositories.autocomplete_repository import AutocompleteRepository
from flask_app.infrastructure.persistence.ldap.ldap_connection import LDAPConnection


class LDAPAutocompleteRepository(AutocompleteRepository):
    """
    Implémentation LDAP pour le repository d'autocomplétion.
    Cette classe implémente les méthodes définies dans l'interface AutocompleteRepository
    en utilisant le protocole LDAP pour fournir des fonctionnalités d'autocomplétion.
    """
    
    def __init__(self, connection_provider):
        """
        Initialise le repository avec un fournisseur de connexion LDAP.
        
        Args:
            connection_provider: Fournisseur de connexion LDAP qui gère le pool de connexions
        """
        self.connection_provider = connection_provider
        self.config = connection_provider.get_config()
    
    def autocomplete(self, search_type: str, search_term: str) -> List[Dict[str, Any]]:
        """
        Fonction d'autocomplétion unifiée supportant différents types de recherche.
        
        Args:
            search_type: Type de recherche ('group', 'fullName', 'role', 'services', 'managers')
            search_term: Terme de recherche
            
        Returns:
            Liste de dictionnaires avec 'label' et 'value'
        """
        # Validation initiale
        if not search_term or not search_type:
            return []
        
        # Ne pas effectuer de recherche si le terme est trop court (uniquement pour fullName)
        if search_type == 'fullName' and len(search_term) < 3:
            return []
        
        # Utiliser les fonctions dédiées pour les cas spéciaux
        if search_type == 'roles' or search_type == 'role':
            return self.autocomplete_role(search_term)
        elif search_type == 'services':
            return self.autocomplete_services(search_term)
        
        conn = self.connection_provider.get_connection()
        try:
            results = []
            
            # Échapper les caractères spéciaux pour LDAP
            search_term_escaped = self._escape_ldap_filter(search_term)
            
            # Configuration spécifique selon le type de recherche
            if search_type == 'group':
                for base_dn in [self.config['base_dn'], self.config['app_base_dn']]:
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(&(cn=*{search_term_escaped}*)(objectClass=groupOfNames))',
                        search_scope='SUBTREE',
                        attributes=['cn']
                    )
                    
                    for entry in conn.entries:
                        if ('cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY' not in entry.entry_dn):
                            results.append({
                                'label': f"{entry.cn.value} ({entry.entry_dn})",
                                'value': entry.cn.value
                            })
            
            elif search_type == 'fullName':
                ldap_filter = f'(&(objectClass=Person)(fullName=*{search_term_escaped}*))'
                attributes = ['cn', 'fullName']
                
                conn.search(
                    search_base=self.config['all_users_dn'],
                    search_filter=ldap_filter,
                    search_scope='SUBTREE',
                    attributes=attributes,
                    size_limit=20,
                    time_limit=5
                )
                
                for entry in conn.entries:
                    if hasattr(entry, 'fullName') and entry.fullName.value:
                        results.append({
                            'label': entry.fullName.value,
                            'value': entry.fullName.value
                        })
                
                # Limiter à 20 résultats
                results = results[:20]
            
            elif search_type == 'managers':
                search_base = self.config['actif_users_dn']
                search_filter = f'(&(FavvDienstHoofd=YES)(fullName=*{search_term_escaped}*))'
                
                conn.search(
                    search_base=search_base,
                    search_filter=search_filter,
                    search_scope='SUBTREE',
                    attributes=['cn', 'fullName', 'title', 'mail']
                )
                
                for entry in conn.entries:
                    results.append({
                        'label': f"{entry.fullName.value} - {entry.mail.value if hasattr(entry, 'mail') and entry.mail else 'No email'} - {entry.title.value if hasattr(entry, 'title') and entry.title else 'No title'}",
                        'value': entry.fullName.value
                    })
            
            else:
                # Type de recherche non reconnu
                return []
            
            return results
                
        except Exception as e:
            print(f"Erreur lors de l'autocomplétion ({search_type}): {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def autocomplete_role(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Fonction d'autocomplétion spécifique pour les rôles.
        
        Args:
            search_term: Terme de recherche
            
        Returns:
            Liste de dictionnaires avec 'label' et 'value'
        """
        conn = self.connection_provider.get_connection()
        try:
            roles = []
            
            # Vérifier que role_base_dn est bien une liste
            base_dns = self.config['role_base_dn']
            if not isinstance(base_dns, list):
                base_dns = [base_dns]
            
            # Échapper les caractères spéciaux pour LDAP
            search_term_escaped = self._escape_ldap_filter(search_term)
            
            # Exécuter la recherche pour chaque base_dn valide
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré: {base_dn}")
                    continue
                
                try:
                    print(f"Recherche de rôles dans {base_dn} avec filtre: (cn=*{search_term_escaped}*)")
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(cn=*{search_term_escaped}*)',
                        search_scope='SUBTREE',
                        attributes=['cn']
                    )
                    
                    # Traiter les entrées trouvées dans ce base_dn
                    for entry in conn.entries:
                        if hasattr(entry, 'cn') and entry.cn:
                            label = f"{entry.cn.value}" if hasattr(entry.cn, 'value') else "Unknown"
                            if hasattr(entry, 'entry_dn'):
                                label += f" ({entry.entry_dn})"
                            
                            roles.append({
                                'label': label,
                                'value': entry.cn.value if hasattr(entry.cn, 'value') else entry.entry_dn
                            })
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    # Continuer avec le prochain base_dn en cas d'erreur
                    continue
            
            return roles
            
        except Exception as e:
            print(f"Erreur lors de l'autocomplétion des rôles: {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def autocomplete_services(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Fonction d'autocomplétion pour les services (OU).
        
        Args:
            search_term: Terme de recherche
            
        Returns:
            Liste de dictionnaires avec 'label' et 'value'
        """
        conn = self.connection_provider.get_connection()
        try:
            # Échapper le terme de recherche
            search_term_escaped = self._escape_ldap_filter(search_term)
            
            # Dictionnaire pour éliminer les doublons (clé = valeur du service en minuscules)
            unique_services = {}
            
            # Bases DN à rechercher
            base_dns = [self.config['app_base_dn'], self.config['base_dn']]
            
            # Parcourir toutes les bases DN
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré dans autocomplete_services: {base_dn}")
                    continue
                
                try:
                    # Limiter la recherche pour de meilleures performances
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(ou=*{search_term_escaped}*)',
                        search_scope='SUBTREE',
                        attributes=['ou'],
                        size_limit=50,  # Limiter le nombre de résultats
                        time_limit=5     # Limiter le temps de recherche en secondes
                    )
                    
                    # Ajouter chaque service unique au dictionnaire
                    for entry in conn.entries:
                        if hasattr(entry, 'ou') and entry.ou and entry.ou.value:
                            # Utiliser la valeur en minuscules comme clé pour éviter les doublons
                            service_value = entry.ou.value
                            service_key = service_value.lower()
                            
                            # Ajouter seulement si ce service n'existe pas déjà
                            if service_key not in unique_services:
                                unique_services[service_key] = {
                                    'label': service_value,
                                    'value': service_value
                                }
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    # Continuer avec le prochain base_dn en cas d'erreur
                    continue
            
            # Convertir le dictionnaire en liste pour le retour
            services = list(unique_services.values())
            
            # Trier les services par ordre alphabétique
            services.sort(key=lambda x: x['label'])
            
            # Limiter le nombre de résultats retournés
            services = services[:20]
            
            return services
                
        except Exception as e:
            print(f"Erreur lors de l'autocomplétion des services: {str(e)}")
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