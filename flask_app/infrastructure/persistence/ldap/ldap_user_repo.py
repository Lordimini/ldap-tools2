# flask_app/infrastructure/persistence/ldap/ldap_user_repo.py
from typing import List, Optional, Dict, Any
from flask_app.domain.repositories.user_repository import UserRepository
from flask_app.domain.models.user import User
from flask_app.domain.models.result import Result
from flask_app.infrastructure.persistence.ldap.ldap_connection import LDAPConnection
import unicodedata
import re
from ldap3 import MODIFY_REPLACE, MODIFY_DELETE, MODIFY_ADD, SUBTREE


class LDAPUserRepository(UserRepository):
    """
    Implémentation LDAP pour le repository utilisateur.
    Cette classe implémente les méthodes définies dans l'interface UserRepository
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
    
    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un utilisateur par son nom d'utilisateur (CN).
        
        Args:
            username: Le nom d'utilisateur à rechercher
            
        Returns:
            Les données de l'utilisateur ou None si non trouvé
        """
        conn = self.connection_provider.get_connection()
        try:
            # Construire le filtre LDAP pour rechercher par CN
            search_filter = f'(cn={self._escape_ldap_filter(username)})'
            
            # Rechercher dans le conteneur des utilisateurs actifs
            search_base = self.config['actif_users_dn']
            
            # Attributs à récupérer
            attributes = [
                'cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 
                'fullName', 'mail', 'workforceID', 'groupMembership', 
                'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 
                'loginDisabled', 'loginTime', 'passwordExpirationTime', 
                'generationQualifier'
            ]
            
            # Exécuter la recherche
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=attributes
            )
            
            # Si aucun résultat, chercher dans le conteneur des utilisateurs inactifs
            if not conn.entries:
                search_base = self.config['out_users_dn']
                conn.search(
                    search_base=search_base,
                    search_filter=search_filter,
                    search_scope='SUBTREE',
                    attributes=attributes
                )
            
            # Traiter le résultat
            if conn.entries:
                user_data = self._process_user_entry(conn.entries[0])
                return user_data
            
            return None
        
        except Exception as e:
            print(f"Erreur lors de la recherche de l'utilisateur {username}: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def find_by_dn(self, dn: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un utilisateur par son DN.
        
        Args:
            dn: Le DN de l'utilisateur
            
        Returns:
            Les données de l'utilisateur ou None si non trouvé
        """
        conn = self.connection_provider.get_connection()
        try:
            # Attributs à récupérer
            attributes = [
                'cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 
                'fullName', 'mail', 'workforceID', 'groupMembership', 
                'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 
                'loginDisabled', 'loginTime', 'passwordExpirationTime', 
                'generationQualifier'
            ]
            
            # Recherche par DN (recherche BASE)
            conn.search(
                search_base=dn,
                search_filter='(objectClass=*)',
                search_scope='BASE',
                attributes=attributes
            )
            
            # Traiter le résultat
            if conn.entries:
                user_data = self._process_user_entry(conn.entries[0])
                
                # Déterminer si l'utilisateur est inactif en fonction de son conteneur
                user_data['is_inactive'] = self.config['out_users_dn'] in dn
                
                return user_data
            
            return None
        
        except Exception as e:
            print(f"Erreur lors de la recherche de l'utilisateur par DN {dn}: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def search(self, search_term: str, search_type: str, return_list: bool = False) -> List[Dict[str, Any]]:
        """
        Recherche des utilisateurs selon différents critères.
        
        Args:
            search_term: Le terme de recherche
            search_type: Le type de recherche (cn, fullName, mail, etc.)
            return_list: Si True, retourne une liste simplifiée d'utilisateurs
            
        Returns:
            Liste des utilisateurs correspondant aux critères
        """
        conn = self.connection_provider.get_connection()
        try:
            # Échapper les caractères spéciaux pour LDAP
            search_term_escaped = self._escape_ldap_filter(search_term)
            
            # Construire le filtre LDAP en fonction du type de recherche
            if search_type == 'cn':
                search_filter = f'(cn={search_term_escaped})'
            elif search_type == 'fullName':
                # Utiliser des wildcards si retour_liste est True
                if return_list:
                    search_filter = f'(fullName=*{search_term_escaped}*)'
                else:
                    search_filter = f'(fullName={search_term_escaped})'
            elif search_type == 'mail':
                # Utiliser des wildcards si retour_liste est True
                if return_list:
                    search_filter = f'(mail=*{search_term_escaped}*)'
                else:
                    search_filter = f'(mail={search_term_escaped})'
            elif search_type == 'workforceID':
                search_filter = f'(workforceID={search_term_escaped})'
            elif search_type == 'FavvNatNr':
                search_filter = f'(FavvNatNr={search_term_escaped})'
            else:
                # Type de recherche non supporté
                return []
            
            # Attributs à récupérer
            if return_list:
                # Attributs de base pour une liste simplifiée
                attributes = ['cn', 'fullName', 'mail', 'ou', 'title']
            else:
                # Attributs complets pour un utilisateur détaillé
                attributes = [
                    'cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 
                    'fullName', 'mail', 'workforceID', 'groupMembership', 
                    'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 
                    'loginDisabled', 'loginTime', 'passwordExpirationTime',
                    'generationQualifier'
                ]
            
            # Définir les bases de recherche
            if return_list:
                search_bases = [self.config['actif_users_dn']]
            else:
                search_bases = [self.config['actif_users_dn'], self.config['out_users_dn']]
            
            # Liste pour stocker les résultats
            results = []
            
            # Effectuer la recherche dans chaque base
            for search_base in search_bases:
                conn.search(
                    search_base=search_base,
                    search_filter=search_filter,
                    search_scope='SUBTREE',
                    attributes=attributes
                )
                
                # Traiter les résultats
                for entry in conn.entries:
                    if return_list:
                        # Format simplifié pour une liste
                        user = {
                            'dn': entry.entry_dn,
                            'cn': entry.cn.value if hasattr(entry, 'cn') else '',
                            'fullName': entry.fullName.value if hasattr(entry, 'fullName') else '',
                            'mail': entry.mail.value if hasattr(entry, 'mail') else '',
                            'ou': entry.ou.value if hasattr(entry, 'ou') else '',
                            'title': entry.title.value if hasattr(entry, 'title') else ''
                        }
                        results.append(user)
                    else:
                        # Format complet pour un utilisateur détaillé
                        user_data = self._process_user_entry(entry)
                        results.append(user_data)
            
            return results
        
        except Exception as e:
            print(f"Erreur lors de la recherche d'utilisateurs: {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def create(self, user_data: Dict[str, Any], template_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crée un nouvel utilisateur.
        
        Args:
            user_data: Les données de l'utilisateur à créer
            template_details: Détails du template à appliquer (optionnel)
            
        Returns:
            Les données de l'utilisateur créé avec informations supplémentaires
        """
        conn = self.connection_provider.get_connection()
        try:
            # Extraire les données essentielles
            cn = user_data.get('cn')
            
            if not cn:
                raise ValueError("Le champ 'cn' est obligatoire pour créer un utilisateur")
            
            # Construire le DN de l'utilisateur
            user_dn = f"cn={cn},{self.config['usercreation_dn']}"
            
            # Ajouter les classes d'objet obligatoires
            ldap_attributes = user_data.copy()
            ldap_attributes['objectClass'] = [
                'inetOrgPerson', 
                'top',
                'pwmUser',
                'FavvAfscaUser'
            ]
            
            # Effectuer la création de l'utilisateur
            result = conn.add(user_dn, attributes=ldap_attributes)
            
            if not result:
                error_msg = f"Échec de création de l'utilisateur: {conn.result}"
                print(error_msg)
                return {'success': False, 'error': error_msg}
            
            # Ajouter l'utilisateur aux groupes si un template est fourni
            groups_added = 0
            groups_failed = 0
            
            if template_details and 'groupMembership' in template_details and template_details['groupMembership']:
                for group_dn in template_details['groupMembership']:
                    # Ajouter le DN de l'utilisateur à l'attribut member du groupe
                    group_modify = conn.modify(
                        group_dn, 
                        {'member': [(MODIFY_ADD, [user_dn])]}
                    )
                    
                    # Ajouter le DN du groupe à l'attribut groupMembership de l'utilisateur
                    user_modify = conn.modify(
                        user_dn, 
                        {'groupMembership': [(MODIFY_ADD, [group_dn])]}
                    )
                    
                    # Traiter le résultat
                    if group_modify and user_modify:
                        groups_added += 1
                    else:
                        groups_failed += 1
            
            # Préparer le résultat
            result_data = {
                'success': True,
                'cn': cn,
                'dn': user_dn,
                'groups_added': groups_added,
                'groups_failed': groups_failed
            }
            
            # Ajouter le mot de passe s'il est défini
            if 'userPassword' in ldap_attributes:
                result_data['password'] = ldap_attributes['userPassword'][0] if isinstance(ldap_attributes['userPassword'], list) else ldap_attributes['userPassword']
            
            return result_data
        
        except Exception as e:
            error_msg = f"Erreur lors de la création de l'utilisateur: {str(e)}"
            print(error_msg)
            return {'success': False, 'error': error_msg}
        finally:
            self.connection_provider.release_connection(conn)
    
    def update(self, user_dn: str, attributes: Dict[str, Any], 
              groups_to_add: Optional[List[Dict[str, str]]] = None, 
              groups_to_remove: Optional[List[Dict[str, str]]] = None,
              target_container: Optional[str] = None) -> tuple:
        """
        Met à jour un utilisateur existant.
        
        Args:
            user_dn: DN de l'utilisateur à mettre à jour
            attributes: Attributs à modifier
            groups_to_add: Groupes à ajouter
            groups_to_remove: Groupes à retirer
            target_container: Container cible pour déplacement (optionnel)
            
        Returns:
            Tuple (succès, message)
        """
        conn = self.connection_provider.get_connection()
        try:
            # Vérifier que l'utilisateur existe
            conn.search(
                search_base=user_dn,
                search_filter='(objectClass=*)',
                search_scope='BASE',
                attributes=['cn']
            )
            
            if not conn.entries:
                return False, "L'utilisateur n'existe pas"
            
            # Obtenir le CN de l'utilisateur
            user_cn = conn.entries[0].cn.value
            
            # Convertir les attributs pour LDAP
            ldap_changes = {}
            for attr_name, attr_value in attributes.items():
                # Vérifier si la valeur est vide (None ou chaîne vide)
                if attr_value is None or (isinstance(attr_value, str) and attr_value == ''):
                    # Pour supprimer l'attribut
                    ldap_changes[attr_name] = [(MODIFY_DELETE, [])]
                else:
                    # Pour mettre à jour l'attribut
                    ldap_changes[attr_name] = [(MODIFY_REPLACE, [attr_value])]
            
            # Appliquer les modifications d'attributs
            if ldap_changes:
                attr_result = conn.modify(user_dn, changes=ldap_changes)
                if not attr_result:
                    print(f"Erreur lors de la modification des attributs: {conn.result}")
            
            # Gérer les groupes à ajouter
            if groups_to_add:
                for group in groups_to_add:
                    group_dn = group.get('dn')
                    if not group_dn:
                        # Si aucun DN n'est fourni, rechercher le groupe par son nom
                        group_name = group.get('name')
                        if group_name:
                            # Rechercher le groupe dans les différents containers
                            search_bases = [
                                'ou=Groups,ou=IAM-Security,o=COPY', 
                                self.config['app_base_dn'], 
                                'ou=GROUPS,ou=SYNC,o=COPY'
                            ]
                            
                            for base_dn in search_bases:
                                conn.search(
                                    search_base=base_dn,
                                    search_filter=f'(cn={group_name})',
                                    search_scope='SUBTREE',
                                    attributes=['cn']
                                )
                                
                                if conn.entries:
                                    group_dn = conn.entries[0].entry_dn
                                    break
                    
                    if group_dn:
                        # Ajouter l'utilisateur au groupe
                        self._add_user_to_group(conn, user_dn, group_dn)
            
            # Gérer les groupes à supprimer
            if groups_to_remove:
                for group in groups_to_remove:
                    group_dn = group.get('dn')
                    if group_dn:
                        # Supprimer l'utilisateur du groupe
                        self._remove_user_from_group(conn, user_dn, group_dn)
            
            # Gérer le déplacement vers un autre container si spécifié
            new_dn = user_dn
            if target_container:
                # Construire le nouveau DN
                new_dn = f"cn={user_cn},{target_container}"
                
                # Déplacer l'utilisateur
                move_result = conn.modify_dn(
                    user_dn,
                    f"cn={user_cn}",
                    new_superior=target_container
                )
                
                if not move_result:
                    print(f"Erreur lors du déplacement de l'utilisateur: {conn.result}")
                    return False, f"Erreur lors du déplacement de l'utilisateur: {conn.result}"
            
            return True, f"Utilisateur {user_cn} mis à jour avec succès"
        
        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}"
            print(error_msg)
            return False, error_msg
        finally:
            self.connection_provider.release_connection(conn)
    
    def delete(self, user_dn: str) -> tuple:
        """
        Supprime un utilisateur.
        
        Args:
            user_dn: DN de l'utilisateur à supprimer
            
        Returns:
            Tuple (succès, message)
        """
        conn = self.connection_provider.get_connection()
        try:
            # Vérifier que l'utilisateur existe
            conn.search(
                search_base=user_dn,
                search_filter='(objectClass=*)',
                search_scope='BASE',
                attributes=['cn']
            )
            
            if not conn.entries:
                return False, "L'utilisateur n'existe pas"
            
            # Obtenir le CN de l'utilisateur pour le message
            user_cn = conn.entries[0].cn.value
            
            # Supprimer l'utilisateur
            result = conn.delete(user_dn)
            
            if result:
                return True, f"Utilisateur {user_cn} supprimé avec succès"
            else:
                return False, f"Échec de la suppression: {conn.result}"
        
        except Exception as e:
            error_msg = f"Erreur lors de la suppression de l'utilisateur: {str(e)}"
            print(error_msg)
            return False, error_msg
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_pending_users(self) -> List[Dict[str, Any]]:
        """
        Récupère les utilisateurs en attente dans le container to-process.
        
        Returns:
            Liste des utilisateurs en attente
        """
        conn = self.connection_provider.get_connection()
        try:
            # Définir le DN du conteneur to-process
            to_process_dn = self.config['toprocess_users_dn']
            
            # Rechercher tous les utilisateurs dans le conteneur
            conn.search(
                search_base=to_process_dn,
                search_filter='(objectClass=Person)',
                search_scope='SUBTREE',
                attributes=['cn', 'fullName']
            )
            
            users = []
            for entry in conn.entries:
                users.append({
                    'dn': entry.entry_dn,
                    'cn': entry.cn.value if hasattr(entry, 'cn') else 'Unknown',
                    'fullName': entry.fullName.value if hasattr(entry, 'fullName') else 'Unknown'
                })
            
            return users
        
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs en attente: {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def complete_user_creation(self, user_dn: str, target_container: str, 
                             attributes: Dict[str, Any], groups: List[Dict[str, Any]],
                             set_password: bool = False) -> tuple:
        """
        Finalise la création d'un utilisateur en le déplaçant et en définissant des attributs.
        
        Args:
            user_dn: DN de l'utilisateur
            target_container: Container de destination
            attributes: Attributs à définir
            groups: Groupes à ajouter
            set_password: Si True, définit un mot de passe par défaut
            
        Returns:
            Tuple (succès, message)
        """
        conn = self.connection_provider.get_connection()
        try:
            # Vérifier que l'utilisateur existe
            conn.search(
                search_base=user_dn,
                search_filter='(objectClass=*)',
                search_scope='BASE',
                attributes=['cn']
            )
            
            if not conn.entries:
                return False, "L'utilisateur n'existe pas"
            
            # Obtenir le CN de l'utilisateur
            user_cn = conn.entries[0].cn.value
            
            # Construire le nouveau DN
            new_dn = f"cn={user_cn},{target_container}"
            
            # Créer un dictionnaire pour les attributs non vides
            filtered_attributes = {}
            for k, v in attributes.items():
                if v:  # Si la valeur n'est pas vide
                    filtered_attributes[k] = [(MODIFY_REPLACE, [v])]
            
            # Déplacer l'utilisateur vers le container cible
            move_result = conn.modify_dn(
                user_dn,
                f"cn={user_cn}",
                new_superior=target_container
            )
            
            if not move_result:
                error_msg = f"Erreur lors du déplacement de l'utilisateur: {conn.result}"
                print(error_msg)
                return False, error_msg
            
            # Définir les attributs
            if filtered_attributes:
                attr_result = conn.modify(new_dn, changes=filtered_attributes)
                if not attr_result:
                    print(f"Erreur lors de la définition des attributs: {conn.result}")
            
            # Définir le mot de passe si demandé
            if set_password:
                # Générer ou définir un mot de passe (implémentation à compléter)
                password = self._generate_password(user_cn)
                password_result = conn.modify(
                    new_dn,
                    {'userPassword': [(MODIFY_REPLACE, [password])]}
                )
                
                if not password_result:
                    print(f"Erreur lors de la définition du mot de passe: {conn.result}")
            
            # Compteurs pour le rapport
            groups_added = 0
            groups_failed = 0
            
            # Ajouter l'utilisateur aux groupes
            for group_data in groups:
                group_dn = None
                
                # Obtenir le nom du groupe
                group_name = None
                if 'name' in group_data:
                    group_name = group_data['name']
                elif 'cn' in group_data:
                    group_name = group_data['cn']
                
                if not group_name:
                    groups_failed += 1
                    continue
                
                # Rechercher le DN du groupe
                search_bases = [
                    'ou=Groups,ou=IAM-Security,o=COPY', 
                    self.config['app_base_dn'], 
                    'ou=GROUPS,ou=SYNC,o=COPY'
                ]
                
                for base_dn in search_bases:
                    conn.search(
                        search_base=base_dn,
                        search_filter=f'(cn={group_name})',
                        search_scope='SUBTREE',
                        attributes=['cn']
                    )
                    
                    if conn.entries:
                        group_dn = conn.entries[0].entry_dn
                        break
                
                if not group_dn:
                    groups_failed += 1
                    continue
                
                # Ajouter l'utilisateur au groupe
                group_success = self._add_user_to_group(conn, new_dn, group_dn)
                
                if group_success:
                    groups_added += 1
                else:
                    groups_failed += 1
            
            success_message = f"Utilisateur {user_cn} déplacé avec succès vers {target_container}. "
            if groups_added > 0:
                success_message += f"Ajouté à {groups_added} groupes. "
            if groups_failed > 0:
                success_message += f"Échec d'ajout à {groups_failed} groupes."
            
            return True, success_message
        
        except Exception as e:
            error_msg = f"Erreur lors de la finalisation de la création de l'utilisateur: {str(e)}"
            print(error_msg)
            return False, error_msg
        finally:
            self.connection_provider.release_connection(conn)
    
    def check_name_exists(self, given_name: str, sn: str) -> tuple:
        """
        Vérifie si un utilisateur avec ce prénom et nom existe déjà.
        
        Args:
            given_name: Prénom
            sn: Nom de famille
            
        Returns:
            Tuple (existe, dn_si_existe)
        """
        conn = self.connection_provider.get_connection()
        try:
            # Créer un filtre LDAP pour rechercher par prénom et nom
            search_filter = f'(&(givenName={self._escape_ldap_filter(given_name)})(sn={self._escape_ldap_filter(sn)}))'
            
            # Rechercher dans les conteneurs d'utilisateurs
            search_base = self.config['all_users_dn']
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn', 'givenName', 'sn', 'fullName']
            )
            
            if conn.entries:
                # Utilisateur déjà existant, retourner le DN du premier utilisateur correspondant
                user_dn = conn.entries[0].entry_dn
                return True, user_dn
            
            return False, ""
        
        except Exception as e:
            print(f"Erreur lors de la vérification du nom: {str(e)}")
            return False, ""
        finally:
            self.connection_provider.release_connection(conn)
    
    def check_favvnatnr_exists(self, favvnatnr: str) -> tuple:
        """
        Vérifie si un utilisateur avec ce numéro national existe déjà.
        
        Args:
            favvnatnr: Numéro de registre national
            
        Returns:
            Tuple (existe, dn_si_existe, nom_complet)
        """
        conn = self.connection_provider.get_connection()
        try:
            # Normaliser le FavvNatNr (enlever espaces et tirets)
            normalized_favvnatnr = favvnatnr.replace(' ', '').replace('-', '')
            
            # Créer un filtre LDAP pour rechercher par FavvNatNr
            search_filter = f'(FavvNatNr={self._escape_ldap_filter(normalized_favvnatnr)})'
            
            # Rechercher dans le conteneur des utilisateurs
            search_base = self.config['all_users_dn']
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['cn', 'FavvNatNr', 'fullName']
            )
            
            if conn.entries:
                # L'utilisateur existe déjà, retourner le DN du premier utilisateur correspondant
                user_dn = conn.entries[0].entry_dn
                fullname = conn.entries[0].fullName.value if hasattr(conn.entries[0], 'fullName') else "Unknown"
                return True, user_dn, fullname
            
            return False, "", ""
        
        except Exception as e:
            print(f"Erreur lors de la vérification du FavvNatNr: {str(e)}")
            return False, "", ""
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
    
    def _add_user_to_group(self, conn, user_dn: str, group_dn: str) -> bool:
        """
        Ajoute un utilisateur à un groupe.
        
        Args:
            conn: Connexion LDAP active
            user_dn: DN de l'utilisateur à ajouter
            group_dn: DN du groupe auquel ajouter l'utilisateur
            
        Returns:
            True si l'opération a réussi, False sinon
        """
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
            
            # 3. Vérifier si c'est un groupe de type rôle, et si oui, mettre à jour equivalentToMe
            conn.search(group_dn, '(objectClass=nrfRole)', search_scope='BASE')
            if conn.entries:
                # C'est un groupe de type rôle, mettre à jour equivalentToMe
                equiv_modify = conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_ADD, [user_dn])]}
                )
            else:
                # Pas un groupe de type rôle
                equiv_modify = True
            
            # Vérifier si toutes les opérations ont réussi
            return user_modify and group_modify and equiv_modify
        
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'utilisateur au groupe: {str(e)}")
            return False
    
    def _remove_user_from_group(self, conn, user_dn: str, group_dn: str) -> bool:
        """
        Supprime un utilisateur d'un groupe.
        
        Args:
            conn: Connexion LDAP active
            user_dn: DN de l'utilisateur à supprimer
            group_dn: DN du groupe duquel supprimer l'utilisateur
            
        Returns:
            True si l'opération a réussi, False sinon
        """
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
            
            # 3. Vérifier si c'est un groupe de type rôle, et si oui, supprimer de equivalentToMe
            conn.search(group_dn, '(objectClass=nrfRole)', search_scope='BASE')
            if conn.entries:
                # C'est un groupe de type rôle, mettre à jour equivalentToMe
                conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_DELETE, [user_dn])]}
                )
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de l'utilisateur du groupe: {str(e)}")
            return False
    
    def _generate_password(self, cn: str) -> str:
        """
        Génère un mot de passe pour un utilisateur basé sur son CN.
        
        Args:
            cn: Common Name de l'utilisateur
            
        Returns:
            Mot de passe généré
        """
        # Vérifier si le CN a moins de 5 caractères
        if len(cn) < 5:
            return cn + 'x4$*987'  # Ajouter une complexité supplémentaire
        
        # Vérifier si un des noms est court (3 caractères ou moins)
        has_short_name = False
        name_parts = re.findall(r'[A-Za-z]+', cn)
        if any(len(part) <= 3 for part in name_parts):
            has_short_name = True
        
        # Si nom court, ajouter une complexité supplémentaire
        if has_short_name:
            if len(cn) == 5:
                # Pour un CN de 5 caractères
                first_part = cn[:3]
                second_part = cn[3:] + 'x3'
                return (second_part + first_part[0:2]).lower() + '$*987'
            else:
                # Pour un CN de 6+ caractères
                first_part = cn[:3]
                second_part = cn[3:6] + 'x3'
                return (second_part + first_part[0:2]).lower() + '$*987'
        
        # Pour les noms normaux
        if len(cn) == 5:
            # Pour un CN de 5 caractères
            first_part = cn[:3]
            second_part = cn[3:]
            return (second_part + first_part).lower() + '*987'
        else:
            # Pour un CN de 6+ caractères
            first_part = cn[:3]
            second_part = cn[3:6]
            return (second_part + first_part).lower() + '*987'
    
    def _process_user_entry(self, entry) -> Dict[str, Any]:
        """
        Traite une entrée LDAP d'utilisateur et la convertit en dictionnaire.
        
        Args:
            entry: Entrée LDAP d'utilisateur
            
        Returns:
            Dictionnaire des attributs de l'utilisateur
        """
        user_data = {
            'dn': entry.entry_dn,
            'CN': entry.cn.value if hasattr(entry, 'cn') else '',
            'favvEmployeeType': entry.favvEmployeeType.value if hasattr(entry, 'favvEmployeeType') else '',
            'fullName': entry.fullName.value if hasattr(entry, 'fullName') else '',
            'mail': entry.mail.value if hasattr(entry, 'mail') else '',
            'sn': entry.sn.value if hasattr(entry, 'sn') else '',
            'givenName': entry.givenName.value if hasattr(entry, 'givenName') else '',
            'workforceID': entry.workforceID.value if hasattr(entry, 'workforceID') else '',
            'title': entry.title.value if hasattr(entry, 'title') else '',
            'service': entry.ou.value if hasattr(entry, 'ou') else '',
            'FavvNatNr': entry.FavvNatNr.value if hasattr(entry, 'FavvNatNr') else '',
            'groupMembership': [],
            'DirXMLAssociations': entry['DirXML-Associations'].values if hasattr(entry, 'DirXML-Associations') else [],
            'FavvHierarMgrDN': entry.FavvHierarMgrDN.value if hasattr(entry, 'FavvHierarMgrDN') else None,
            'nrfMemberOf': [],
            'loginDisabled': 'YES' if hasattr(entry, 'loginDisabled') and entry.loginDisabled.value else 'NO',
            'loginTime': entry.loginTime.value if hasattr(entry, 'loginTime') else '',
            'passwordExpirationTime': entry.passwordExpirationTime.value if hasattr(entry, 'passwordExpirationTime') else '',
            'is_inactive': False,  # Sera défini plus tard en fonction du conteneur
            'generationQualifier': entry.generationQualifier.value if hasattr(entry, 'generationQualifier') else ''
        }
        
        # Récupérer les groupes (groupMembership)
        if hasattr(entry, 'groupMembership') and entry.groupMembership:
            group_memberships = []
            for group_dn in entry.groupMembership.values:
                conn = self.connection_provider.get_connection()
                try:
                    conn.search(group_dn, '(objectClass=groupOfNames)', attributes=['cn'])
                    if conn.entries:
                        group_cn = conn.entries[0].cn.value
                        group_memberships.append({
                            'dn': group_dn,
                            'cn': group_cn,
                        })
                finally:
                    self.connection_provider.release_connection(conn)
            user_data['groupMembership'] = group_memberships
        
        # Récupérer le nom du manager si un DN est présent
        if user_data['FavvHierarMgrDN']:
            conn = self.connection_provider.get_connection()
            try:
                conn.search(user_data['FavvHierarMgrDN'], '(objectClass=*)', attributes=['fullName'])
                if conn.entries:
                    manager_name = conn.entries[0].fullName.value
                    user_data['ChefHierarchique'] = manager_name
                    user_data['manager_name'] = manager_name  # Pour compatibilité
                else:
                    user_data['ChefHierarchique'] = 'Manager not found'
                    user_data['manager_name'] = 'Manager not found'
            except Exception as e:
                error_msg = f'Error fetching manager: {str(e)}'
                user_data['ChefHierarchique'] = error_msg
                user_data['manager_name'] = error_msg
            finally:
                self.connection_provider.release_connection(conn)
        else:
            user_data['ChefHierarchique'] = 'No manager specified'
            user_data['manager_name'] = 'No manager specified'
        
        return user_data