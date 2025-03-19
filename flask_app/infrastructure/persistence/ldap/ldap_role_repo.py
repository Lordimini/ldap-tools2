# flask_app/infrastructure/persistence/ldap/ldap_role_repo.py
from typing import List, Optional, Dict, Any, Tuple
from flask_app.domain.repositories.role_repository import RoleRepository
from flask_app.domain.models.role import Role
from flask_app.domain.models.result import Result
from flask_app.infrastructure.persistence.ldap.ldap_connection import LDAPConnection
from ldap3 import MODIFY_REPLACE, MODIFY_DELETE, MODIFY_ADD, SUBTREE


class LDAPRoleRepository(RoleRepository):
    """
    Implémentation LDAP pour le repository de rôle.
    Cette classe implémente les méthodes définies dans l'interface RoleRepository
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
    
    def find_by_cn(self, role_cn: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un rôle par son CN.
        
        Args:
            role_cn: CN du rôle à rechercher
            
        Returns:
            Données du rôle ou None si non trouvé
        """
        conn = self.connection_provider.get_connection()
        try:
            # Vérifier que role_base_dn est bien une liste
            base_dns = self.config['role_base_dn']
            if not isinstance(base_dns, list):
                base_dns = [base_dns]
            
            # Échapper les caractères spéciaux pour LDAP
            search_term_escaped = self._escape_ldap_filter(role_cn)
            
            # Parcourir tous les base_dn valides
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré: {base_dn}")
                    continue
                
                try:
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(cn={search_term_escaped})',
                        search_scope='SUBTREE',
                        attributes=['cn', 'description', 'equivalentToMe', 'nrfRoleCategoryKey']
                    )
                    
                    if conn.entries:
                        # Rôle trouvé, traiter les données
                        role_data = self._process_role_entry(conn.entries[0])
                        return role_data
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    continue
            
            # Rôle non trouvé
            return None
            
        except Exception as e:
            print(f"Erreur lors de la recherche du rôle {role_cn}: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_role_users(self, role_cn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les utilisateurs associés à un rôle.
        
        Args:
            role_cn: CN du rôle
            
        Returns:
            Dictionnaire contenant les informations du rôle et la liste des utilisateurs
        """
        conn = self.connection_provider.get_connection()
        try:
            # Rechercher d'abord le rôle pour obtenir son DN
            role_data = self.find_by_cn(role_cn)
            if not role_data:
                return None
            
            role_dn = role_data['role_dn']
            
            # Récupérer la liste des utilisateurs (equivalentToMe)
            conn.search(
                search_base=role_dn,
                search_filter='(objectClass=nrfRole)',
                search_scope='BASE',
                attributes=['equivalentToMe']
            )
            
            # Initialiser le résultat
            result = {
                'role_cn': role_cn,
                'role_dn': role_dn,
                'users': []
            }
            
            # Si le rôle a des utilisateurs équivalents
            if conn.entries and hasattr(conn.entries[0], 'equivalentToMe') and conn.entries[0].equivalentToMe:
                user_dns = conn.entries[0].equivalentToMe.values
                
                # Récupérer les détails de chaque utilisateur
                for user_dn in user_dns:
                    try:
                        conn.search(
                            search_base=user_dn,
                            search_filter='(objectClass=*)',
                            search_scope='BASE',
                            attributes=['cn', 'fullName', 'title', 'ou', 'nrfAssignedRoles']
                        )
                        
                        if conn.entries:
                            user = conn.entries[0]
                            
                            # Extraire <req_desc> pour le rôle actuel
                            req_desc = "No description available"
                            if hasattr(user, 'nrfAssignedRoles') and user.nrfAssignedRoles:
                                for role_assignment in user.nrfAssignedRoles.values:
                                    # Diviser le DN du rôle et la chaîne XML
                                    parts = role_assignment.split('#0#')
                                    if len(parts) >= 2:
                                        role_dn_part = parts[0].strip()  # DN du rôle
                                        xml_part = parts[1].strip()  # Partie XML
                                        
                                        # Vérifier si le DN du rôle correspond au rôle actuel
                                        if role_dn_part == role_dn:
                                            # Analyser la partie XML pour extraire <req_desc>
                                            start_index = xml_part.find('<req_desc>') + len('<req_desc>')
                                            end_index = xml_part.find('</req_desc>')
                                            if start_index != -1 and end_index != -1:
                                                req_desc = xml_part[start_index:end_index].strip()
                                                break
                            
                            # Ajouter les informations de l'utilisateur au résultat
                            result['users'].append({
                                'CN': user.cn.value if hasattr(user, 'cn') else 'Unknown',
                                'fullName': user.fullName.value if hasattr(user, 'fullName') else 'Unknown',
                                'ou': user.ou.value if hasattr(user, 'ou') else 'N/A',
                                'title': user.title.value if hasattr(user, 'title') else 'N/A',
                                'req_desc': req_desc
                            })
                    except Exception as e:
                        print(f"Erreur lors de la récupération des détails de l'utilisateur {user_dn}: {str(e)}")
            
            return result
            
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs du rôle: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_role_groups(self, role_cn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les groupes associés à un rôle.
        
        Args:
            role_cn: CN du rôle
            
        Returns:
            Dictionnaire contenant les informations du rôle et la liste des groupes
        """
        conn = self.connection_provider.get_connection()
        try:
            # Rechercher d'abord le rôle pour obtenir son DN
            role_data = self.find_by_cn(role_cn)
            if not role_data:
                return None
            
            role_dn = role_data['role_dn']
            
            # Rechercher les associations de ressources pour ce rôle
            resource_base_dn = self.config['resource_base_dn']
            
            conn.search(
                search_base=resource_base_dn,
                search_filter=f'(nrfRole={role_dn})',
                search_scope='SUBTREE',
                attributes=['nrfRole', 'nrfResource']
            )
            
            # Initialiser le résultat
            result = {
                'role_cn': role_cn,
                'groups': []
            }
            
            # Extraire les ressources (groupes)
            for entry in conn.entries:
                if hasattr(entry, 'nrfResource') and entry.nrfResource:
                    nrf_resource_dn = entry.nrfResource.value
                    
                    # Extraire le CN du DN
                    nrf_resource_cn = nrf_resource_dn.split(',')[0].split('=')[1] if '=' in nrf_resource_dn else 'Unknown'
                    
                    result['groups'].append({
                        'nrfResource': nrf_resource_cn,
                        'dn': nrf_resource_dn
                    })
            
            return result
            
        except Exception as e:
            print(f"Erreur lors de la récupération des groupes du rôle: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def view_role(self, dn: str) -> Optional[Dict[str, Any]]:
        """
        Affiche les détails d'un rôle, y compris ses utilisateurs.
        
        Args:
            dn: DN du rôle
            
        Returns:
            Dictionnaire détaillé des informations du rôle
        """
        conn = self.connection_provider.get_connection()
        try:
            # Récupérer les attributs du rôle
            conn.search(
                search_base=dn,
                search_filter='(objectClass=nrfRole)',
                search_scope='BASE',
                attributes=['cn', 'equivalentToMe']
            )
            
            if not conn.entries:
                return None
            
            role = conn.entries[0]
            role_cn = role.cn.value if hasattr(role, 'cn') else 'Unknown'
            equivalent_users = role.equivalentToMe.values if hasattr(role, 'equivalentToMe') and role.equivalentToMe else []
            
            # Récupérer les détails de chaque utilisateur
            users = []
            for user_dn in equivalent_users:
                try:
                    conn.search(
                        search_base=user_dn,
                        search_filter='(objectClass=*)',
                        search_scope='BASE',
                        attributes=['cn', 'fullName', 'ou', 'nrfAssignedRoles']
                    )
                    
                    if conn.entries:
                        user = conn.entries[0]
                        
                        # Extraire <req_desc> pour le rôle actuel
                        req_desc = "No description available"
                        if hasattr(user, 'nrfAssignedRoles') and user.nrfAssignedRoles:
                            for role_assignment in user.nrfAssignedRoles.values:
                                # Diviser le DN du rôle et la chaîne XML
                                parts = role_assignment.split('#0#')
                                if len(parts) >= 2:
                                    role_dn_part = parts[0].strip()  # DN du rôle
                                    xml_part = parts[1].strip()  # Partie XML
                                    
                                    # Vérifier si le DN du rôle correspond au rôle actuel
                                    if role_dn_part == dn:
                                        # Analyser la partie XML pour extraire <req_desc>
                                        start_index = xml_part.find('<req_desc>') + len('<req_desc>')
                                        end_index = xml_part.find('</req_desc>')
                                        if start_index != -1 and end_index != -1:
                                            req_desc = xml_part[start_index:end_index].strip()
                                            break
                        
                        # Ajouter les informations de l'utilisateur
                        users.append({
                            'CN': user.cn.value if hasattr(user, 'cn') else 'Unknown',
                            'fullName': user.fullName.value if hasattr(user, 'fullName') else 'Unknown',
                            'ou': user.ou.value if hasattr(user, 'ou') else 'N/A',
                            'req_desc': req_desc
                        })
                except Exception as e:
                    print(f"Erreur lors de la récupération des détails de l'utilisateur {user_dn}: {str(e)}")
            
            # Extraire le DN du conteneur parent
            parent_dn = ','.join(dn.split(',')[1:])  # Supprimer le premier RDN pour obtenir le DN parent
            
            return {
                'dn': dn,
                'role_cn': role_cn,
                'user_count': len(equivalent_users),
                'users': users,
                'parent_dn': parent_dn
            }
            
        except Exception as e:
            print(f"Erreur lors de l'affichage du rôle: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_ldap_children(self, current_dn: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Récupère les enfants d'un conteneur LDAP (rôles et conteneurs).
        
        Args:
            current_dn: DN du conteneur actuel
            
        Returns:
            Tuple (liste des enfants, dn_parent)
        """
        conn = self.connection_provider.get_connection()
        try:
            # Rechercher les entrées sous le DN actuel
            conn.search(
                search_base=current_dn,
                search_filter='(objectClass=*)',
                search_scope='LEVEL',
                attributes=['cn', 'objectClass', 'nrfLocalizedNames']
            )
            
            # Construire la liste des enfants
            children = []
            
            for entry in conn.entries:
                # Vérifier si c'est un conteneur (nrfRoleDefs)
                if 'nrfRoleDefs' in entry.objectClass.values:
                    # C'est un conteneur
                    children.append({
                        'type': 'container',
                        'name': entry.cn.value if hasattr(entry, 'cn') else 'Unknown',
                        'dn': entry.entry_dn
                    })
                elif 'nrfRole' in entry.objectClass.values:
                    # C'est un rôle
                    localized_name = None
                    
                    # Analyser les noms localisés
                    if hasattr(entry, 'nrfLocalizedNames') and entry.nrfLocalizedNames:
                        raw_localized_names = entry.nrfLocalizedNames.value
                        if raw_localized_names:
                            # Extraire la valeur après 'en~' et avant le premier '|'
                            parts = raw_localized_names.split('|')
                            for part in parts:
                                if part.startswith('en~'):
                                    localized_name = part[3:]  # Supprimer 'en~'
                                    break
                    
                    role_cn = entry.cn.value if hasattr(entry, 'cn') else 'Unknown'
                    children.append({
                        'type': 'role',
                        'name': localized_name or role_cn,  # Utiliser le nom localisé ou fallback sur CN
                        'dn': entry.entry_dn,
                        'role_cn': role_cn
                    })
            
            # Déterminer le DN parent
            parent_dn = None
            if current_dn != self.config['role_base_dn']:
                # Supprimer le premier RDN pour obtenir le DN parent
                parent_dn = ','.join(current_dn.split(',')[1:])
            
            return children, parent_dn
            
        except Exception as e:
            print(f"Erreur lors de la récupération des enfants LDAP: {str(e)}")
            return [], None
        finally:
            self.connection_provider.release_connection(conn)
    
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Recherche des rôles par nom.
        
        Args:
            search_term: Terme de recherche
            
        Returns:
            Liste des rôles correspondant au critère
        """
        conn = self.connection_provider.get_connection()
        try:
            results = []
            
            # Vérifier que role_base_dn est bien une liste
            base_dns = self.config['role_base_dn']
            if not isinstance(base_dns, list):
                base_dns = [base_dns]
            
            # Échapper les caractères spéciaux pour LDAP
            search_term_escaped = self._escape_ldap_filter(search_term)
            
            # Parcourir tous les base_dn valides
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré: {base_dn}")
                    continue
                
                try:
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(&(objectClass=nrfRole)(cn=*{search_term_escaped}*))',
                        search_scope='SUBTREE',
                        attributes=['cn', 'description', 'nrfRoleCategoryKey']
                    )
                    
                    # Traiter les résultats
                    for entry in conn.entries:
                        role_data = {
                            'name': entry.cn.value if hasattr(entry, 'cn') else 'Unknown',
                            'dn': entry.entry_dn,
                            'description': entry.description.value if hasattr(entry, 'description') else None,
                            'category': entry.nrfRoleCategoryKey.value if hasattr(entry, 'nrfRoleCategoryKey') else None
                        }
                        
                        # Vérifier si ce rôle n'est pas déjà dans les résultats
                        if not any(r['dn'] == role_data['dn'] for r in results):
                            results.append(role_data)
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Erreur lors de la recherche de rôles: {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def _process_role_entry(self, entry) -> Dict[str, Any]:
        """
        Traite une entrée LDAP de rôle et la convertit en dictionnaire.
        
        Args:
            entry: Entrée LDAP de rôle
            
        Returns:
            Dictionnaire des attributs du rôle
        """
        role_data = {
            'role_cn': entry.cn.value if hasattr(entry, 'cn') else 'Unknown',
            'role_dn': entry.entry_dn,
            'description': entry.description.value if hasattr(entry, 'description') else None,
            'category': entry.nrfRoleCategoryKey.value if hasattr(entry, 'nrfRoleCategoryKey') else None,
            'user_count': len(entry.equivalentToMe.values) if hasattr(entry, 'equivalentToMe') and entry.equivalentToMe else 0
        }
        
        return role_data
    
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