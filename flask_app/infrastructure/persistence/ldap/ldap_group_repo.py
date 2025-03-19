# flask_app/infrastructure/persistence/ldap/ldap_group_repo.py
from typing import List, Optional, Dict, Any
from flask_app.domain.repositories.group_repository import GroupRepository
from flask_app.domain.models.result import Result
from ldap3 import MODIFY_ADD, MODIFY_DELETE, SUBTREE

class LDAPGroupRepository(GroupRepository):
    """
    Implémentation LDAP pour le repository de groupes.
    Cette classe implémente les méthodes définies dans l'interface GroupRepository
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
    
    def find_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un groupe par son nom.
        
        Args:
            group_name: Nom du groupe à rechercher
            
        Returns:
            Données du groupe ou None si non trouvé
        """
        conn = self.connection_provider.get_connection()
        try:
            group_dn = None
            
            # Liste des bases de recherche où chercher les groupes
            search_bases = [
                'ou=Groups,ou=IAM-Security,o=COPY', 
                self.config['app_base_dn'], 
                'ou=GROUPS,ou=SYNC,o=COPY'
            ]
            
            # Échapper les caractères spéciaux
            group_name_escaped = self._escape_ldap_filter(group_name)
            
            # Rechercher le groupe dans chaque base
            for base_dn in search_bases:
                conn.search(
                    search_base=base_dn,
                    search_filter=f'(cn={group_name_escaped})',
                    search_scope='SUBTREE',
                    attributes=['cn', 'description']
                )
                
                if conn.entries:
                    group_dn = conn.entries[0].entry_dn
                    
                    # Récupérer les attributs du groupe
                    group_data = {
                        'group_name': group_name,
                        'group_dn': group_dn,
                        'description': conn.entries[0].description.value if hasattr(conn.entries[0], 'description') else None,
                        'users': []  # Sera rempli par get_members si nécessaire
                    }
                    
                    return group_data
            
            # Aucun groupe trouvé
            return None
        
        except Exception as e:
            print(f"Erreur lors de la recherche du groupe {group_name}: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def find_by_dn(self, group_dn: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un groupe par son DN.
        
        Args:
            group_dn: DN du groupe
            
        Returns:
            Données du groupe ou None si non trouvé
        """
        conn = self.connection_provider.get_connection()
        try:
            # Vérifier si le groupe existe
            conn.search(
                search_base=group_dn,
                search_filter='(objectClass=groupOfNames)',
                search_scope='BASE',
                attributes=['cn', 'description']
            )
            
            if not conn.entries:
                return None
            
            # Récupérer les attributs du groupe
            group_name = conn.entries[0].cn.value
            
            group_data = {
                'group_name': group_name,
                'group_dn': group_dn,
                'description': conn.entries[0].description.value if hasattr(conn.entries[0], 'description') else None,
                'users': []  # Sera rempli par get_members si nécessaire
            }
            
            return group_data
        
        except Exception as e:
            print(f"Erreur lors de la recherche du groupe avec DN {group_dn}: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_members(self, group_name: str = None, group_dn: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les membres d'un groupe.
        
        Args:
            group_name: Nom du groupe (optionnel si group_dn est fourni)
            group_dn: DN du groupe (optionnel si group_name est fourni)
            
        Returns:
            Dictionnaire contenant les informations du groupe et la liste des membres
        """
        if not group_name and not group_dn:
            return None
        
        conn = self.connection_provider.get_connection()
        try:
            # Si le DN n'est pas fourni, trouver le groupe par nom
            if not group_dn and group_name:
                group_info = self.find_by_name(group_name)
                if not group_info:
                    return None
                group_dn = group_info['group_dn']
                group_name = group_info['group_name']
            
            # Vérifier que le groupe existe
            conn.search(
                search_base=group_dn,
                search_filter='(objectClass=groupOfNames)',
                search_scope='BASE',
                attributes=['cn', 'description', 'member']
            )
            
            if not conn.entries:
                return None
            
            entry = conn.entries[0]
            
            # Si group_name n'est pas fourni, le récupérer
            if not group_name:
                group_name = entry.cn.value
            
            # Initialiser les données du groupe
            group_data = {
                'group_name': group_name,
                'group_dn': group_dn,
                'description': entry.description.value if hasattr(entry, 'description') else None,
                'users': []
            }
            
            # Récupérer les membres du groupe
            if hasattr(entry, 'member') and entry.member:
                members = entry.member.values
                
                # Récupérer les détails de chaque membre
                for member_dn in members:
                    conn.search(
                        search_base=member_dn,
                        search_filter='(objectClass=*)',
                        search_scope='BASE',
                        attributes=['cn', 'fullName', 'title', 'ou']
                    )
                    
                    if conn.entries:
                        user = conn.entries[0]
                        user_data = {
                            'dn': member_dn,
                            'CN': user.cn.value if hasattr(user, 'cn') else 'Unknown',
                            'fullName': user.fullName.value if hasattr(user, 'fullName') else 'Unknown',
                            'title': user.title.value if hasattr(user, 'title') else 'N/A',
                            'service': user.ou.value if hasattr(user, 'ou') else 'N/A'
                        }
                        group_data['users'].append(user_data)
            
            return group_data
        
        except Exception as e:
            print(f"Erreur lors de la récupération des membres du groupe: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def add_user_to_group(self, user_dn: str, group_dn: str) -> bool:
        """
        Ajoute un utilisateur à un groupe.
        
        Args:
            user_dn: DN de l'utilisateur
            group_dn: DN du groupe
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        conn = self.connection_provider.get_connection()
        try:
            # 1. Ajouter le DN du groupe à l'attribut groupMembership de l'utilisateur
            user_modify = conn.modify(
                user_dn, 
                {'groupMembership': [(MODIFY_ADD, [group_dn])]}
            )
            
            # 2. Ajouter le DN de l'utilisateur à l'attribut member du groupe
            group_modify = conn.modify(
                group_dn, 
                {'member': [(MODIFY_ADD, [user_dn])]}
            )
            
            # 3. Ajouter le DN de l'utilisateur à l'attribut equivalentToMe du groupe (si c'est un groupe de type rôle)
            conn.search(
                search_base=group_dn,
                search_filter='(objectClass=nrfRole)',
                search_scope='BASE'
            )
            
            if conn.entries:
                # C'est un groupe de type rôle, mettre à jour equivalentToMe
                equiv_modify = conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_ADD, [user_dn])]}
                )
            else:
                # Pas un groupe de type rôle, pas besoin de mettre à jour equivalentToMe
                equiv_modify = True
            
            # Vérifier si toutes les opérations ont réussi
            success = user_modify and group_modify and equiv_modify
            
            return success
        
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'utilisateur au groupe: {str(e)}")
            return False
        finally:
            self.connection_provider.release_connection(conn)
    
    def remove_user_from_group(self, user_dn: str, group_dn: str) -> bool:
        """
        Retire un utilisateur d'un groupe.
        
        Args:
            user_dn: DN de l'utilisateur
            group_dn: DN du groupe
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        conn = self.connection_provider.get_connection()
        try:
            # 1. Supprimer le DN du groupe de l'attribut groupMembership de l'utilisateur
            conn.modify(
                user_dn, 
                {'groupMembership': [(MODIFY_DELETE, [group_dn])]}
            )
            
            # 2. Supprimer le DN de l'utilisateur de l'attribut member du groupe
            conn.modify(
                group_dn, 
                {'member': [(MODIFY_DELETE, [user_dn])]}
            )
            
            # 3. Supprimer le DN de l'utilisateur de l'attribut equivalentToMe du groupe (si c'est un groupe de type rôle)
            conn.search(
                search_base=group_dn,
                search_filter='(objectClass=nrfRole)',
                search_scope='BASE'
            )
            
            if conn.entries:
                conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_DELETE, [user_dn])]}
                )
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de l'utilisateur du groupe: {str(e)}")
            return False
        finally:
            self.connection_provider.release_connection(conn)
    
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Recherche des groupes par nom.
        
        Args:
            search_term: Terme de recherche
            
        Returns:
            Liste des groupes correspondant au critère
        """
        conn = self.connection_provider.get_connection()
        try:
            results = []
            
            # Échapper les caractères spéciaux pour LDAP
            search_term_escaped = self._escape_ldap_filter(search_term)
            
            # Définir les bases de recherche
            search_bases = [
                'ou=Groups,ou=IAM-Security,o=COPY', 
                self.config['app_base_dn'], 
                'ou=GROUPS,ou=SYNC,o=COPY'
            ]
            
            # Rechercher dans chaque base
            for base_dn in search_bases:
                conn.search(
                    search_base=base_dn,
                    search_filter=f'(&(objectClass=groupOfNames)(cn=*{search_term_escaped}*))',
                    search_scope='SUBTREE',
                    attributes=['cn', 'description']
                )
                
                # Traiter les résultats
                for entry in conn.entries:
                    if ('cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY' not in entry.entry_dn):
                        group_data = {
                            'group_name': entry.cn.value,
                            'group_dn': entry.entry_dn,
                            'description': entry.description.value if hasattr(entry, 'description') else None
                        }
                        results.append(group_data)
            
            return results
        
        except Exception as e:
            print(f"Erreur lors de la recherche de groupes: {str(e)}")
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