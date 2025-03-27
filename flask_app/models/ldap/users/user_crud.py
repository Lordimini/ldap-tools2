# flask_app/models/ldap/users/user_crud.py
from ldap3 import MODIFY_REPLACE, MODIFY_DELETE, MODIFY_ADD
from flask import flash, redirect, url_for
from ..base import LDAPBase


class LDAPUserCRUD(LDAPBase):
    """
    Classe pour gérer les opérations CRUD sur les utilisateurs LDAP.
    """
    
    def _get_config_for_utils(self):
        """
        Helper method to provide config to the UserUtils class.
        This is a temporary solution until we have proper dependency injection.
        """
        config = {
            'ldap_server': self.ldap_server,
            'bind_dn': self.bind_dn,
            'bind_password': self.password,
            'base_dn': self.base_dn,
            'actif_users_dn': self.actif_users_dn,
            'out_users_dn': self.out_users_dn,
            'all_users_dn': self.all_users_dn,
            'template_dn': self.template_dn,
            'usercreation_dn': self.usercreation_dn,
            'admin_group_dn': self.admin_group_dn,
            'reader_group_dn': self.reader_group_dn,
            'oci_admin_group_dn': self.oci_admin_group_dn,
            'oci_reader_group_dn': self.oci_reader_group_dn,
            'role_base_dn': self.role_base_dn,
            'resource_base_dn': self.resource_base_dn,
            'app_base_dn': self.app_base_dn,
            'toprocess_users_dn': self.toprocess_users_dn
        }
        return config
    
    def get_user(self, search_param, options=None):
        """
        Args:
            search_param (str): Paramètre de recherche (CN, mail, DN, etc.)
            options (dict, optional): Options de recherche avec les clés suivantes:
                - search_type (str): Type de recherche ('cn', 'fullName', 'mail', etc.)
                - container (str): Container spécifique ('active', 'inactive', 'toprocess', 'all')
                - simplified (bool): Format simplifié des résultats
                - return_list (bool): Retourner une liste d'utilisateurs au lieu d'un seul
                - filter_attributes (dict): Attributs pour filtrer les résultats
                - attributes (list): Liste des attributs à retourner

        Returns:
            dict/list: Données utilisateur ou liste d'utilisateurs selon options
        """
        # Initialiser options avec valeurs par défaut si non spécifiées
        if options is None:
            options = {}
        
        search_type = options.get('search_type')
        container = options.get('container', 'active')
        simplified = options.get('simplified', False)
        return_list = options.get('return_list', False)
        filter_attributes = options.get('filter_attributes', {})
        custom_attributes = options.get('attributes')

        try:
            conn = self._get_connection()
            
            # Définir les attributs à retourner selon le mode de recherche
            if custom_attributes:
                # Utiliser les attributs personnalisés si spécifiés
                attributes = custom_attributes
            elif return_list:
                # Attributs de base pour les résultats en style liste
                attributes = ['cn', 'fullName', 'mail', 'ou', 'title']
            else:
                # Attributs complets pour les informations détaillées sur l'utilisateur
                attributes = [
                    'cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 
                    'fullName', 'mail', 'workforceID', 'groupMembership', 
                    'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 
                    'nrfMemberOf', 'loginDisabled', 'loginTime', 'passwordExpirationTime',
                    'generationQualifier'
                ]
            
            # Déterminer les paramètres de recherche en fonction du mode
            if search_type is None and not return_list and container != 'toprocess':
                # Recherche directe par DN
                user_dn = search_param
                search_scope = 'BASE'
                search_filter = '(objectClass=*)'
                search_base = user_dn
            else:
                # Construire le filtre de recherche selon search_type
                if search_type == 'cn':
                    search_filter = f'(cn={search_param})'
                elif search_type == 'fullName':
                    # Utiliser des jokers pour la recherche fullName quand return_list est True
                    if return_list:
                        search_filter = f'(fullName=*{search_param}*)'
                    else:
                        search_filter = f'(fullName={search_param})'
                elif search_type == 'mail':
                    # Utiliser des jokers pour la recherche mail quand return_list est True
                    if return_list:
                        search_filter = f'(mail=*{search_param}*)'
                    else:
                        search_filter = f'(mail={search_param})'  
                elif search_type == 'workforceID':
                    search_filter = f'(workforceID={search_param})'
                elif search_type == 'FavvNatNr':
                    search_filter = f'(FavvNatNr={search_param})'
                else:
                    # Recherche générique (traiter search_param comme le filtre)
                    search_filter = search_param if search_param.startswith('(') else f'({search_param})'
                
                # Ajouter des filtres supplémentaires si spécifiés
                if filter_attributes:
                    additional_filters = []
                    for attr, value in filter_attributes.items():
                        additional_filters.append(f'({attr}={value})')
                    
                    # Combiner avec le filtre principal en utilisant &
                    combined_filters = ''.join(additional_filters)
                    search_filter = f'(&{search_filter}{combined_filters})'
                
                search_scope = 'SUBTREE'
                
                # Déterminer quels conteneurs rechercher
                search_bases = []
                if container == 'active' or (container == 'all' and return_list):
                    search_bases.append(self.actif_users_dn)
                elif container == 'inactive':
                    search_bases.append(self.out_users_dn)
                elif container == 'toprocess':
                    search_bases.append(self.toprocess_users_dn)
                elif container == 'all':
                    search_bases = [self.actif_users_dn, self.out_users_dn]
            
            # Gérer les recherches de style liste
            if return_list:
                users = []
                for search_base in search_bases:
                    conn.search(search_base, 
                            search_filter, 
                            search_scope=search_scope,
                            attributes=attributes)
                    
                    # Ajouter les résultats à la liste
                    for entry in conn.entries:
                        user_data = {
                            'dn': entry.entry_dn
                        }
                        # Ajouter tous les attributs disponibles
                        for attr in attributes:
                            if hasattr(entry, attr):
                                user_data[attr] = getattr(entry, attr).value
                            else:
                                user_data[attr] = ''
                        
                        users.append(user_data)
                
                conn.unbind()
                return users
                
            # Gérer la recherche d'un seul utilisateur
            else:
                user_dn = None
                user_container = None
                
                # Si ce n'est pas une recherche directe par DN, trouver d'abord l'utilisateur
                if search_type is not None or container == 'toprocess':
                    for search_base in search_bases:
                        conn.search(search_base, 
                                search_filter, 
                                search_scope=search_scope,
                                attributes=attributes)
                        
                        if conn.entries:
                            user_dn = conn.entries[0].entry_dn
                            user_container = search_base
                            break
                            
                    if not user_dn:
                        print("User not found.")
                        # Ne pas afficher de message flash ici pour éviter les dépendances
                        conn.unbind()
                        return None
                else:
                    # Pour la recherche directe par DN, search_base a déjà été défini sur user_dn
                    conn.search(search_base, 
                            search_filter, 
                            search_scope=search_scope,
                            attributes=attributes)
                    
                    if not conn.entries:
                        conn.unbind()
                        return None
                        
                    # Déterminer dans quel conteneur se trouve l'utilisateur
                    if self.out_users_dn in search_base:
                        user_container = self.out_users_dn
                    elif self.toprocess_users_dn in search_base:
                        user_container = self.toprocess_users_dn
                    else:
                        user_container = self.actif_users_dn
                        
                # Déterminer si l'utilisateur est inactif
                is_inactive = user_container == self.out_users_dn
                is_pending = user_container == self.toprocess_users_dn
                
                # Obtenir les attributs de l'utilisateur
                user_attributes = conn.entries[0]
                
                # Construire le dictionnaire de résultats
                result = {
                    'dn': user_dn if search_type is not None or container == 'toprocess' else search_base,
                    'CN': getattr(user_attributes, 'cn', {}).value if hasattr(user_attributes, 'cn') else '',
                    'favvEmployeeType': getattr(user_attributes, 'favvEmployeeType', {}).value if hasattr(user_attributes, 'favvEmployeeType') else '',
                    'fullName': getattr(user_attributes, 'fullName', {}).value if hasattr(user_attributes, 'fullName') else '',
                    'mail': getattr(user_attributes, 'mail', {}).value if hasattr(user_attributes, 'mail') else '',
                    'sn': getattr(user_attributes, 'sn', {}).value if hasattr(user_attributes, 'sn') else '',
                    'givenName': getattr(user_attributes, 'givenName', {}).value if hasattr(user_attributes, 'givenName') else '',
                    'workforceID': getattr(user_attributes, 'workforceID', {}).value if hasattr(user_attributes, 'workforceID') else '',
                    'title': getattr(user_attributes, 'title', {}).value if hasattr(user_attributes, 'title') else '',
                    'service': getattr(user_attributes, 'ou', {}).value if hasattr(user_attributes, 'ou') else '',
                    'FavvNatNr': getattr(user_attributes, 'FavvNatNr', {}).value if hasattr(user_attributes, 'FavvNatNr') else '',
                    'groupMembership': [],
                    'DirXMLAssociations': getattr(user_attributes, 'DirXML-Associations', {}).values if hasattr(user_attributes, 'DirXML-Associations') else [],
                    'FavvHierarMgrDN': getattr(user_attributes, 'FavvHierarMgrDN', {}).value if hasattr(user_attributes, 'FavvHierarMgrDN') else None,
                    'nrfMemberOf': [],
                    'loginDisabled': 'YES' if hasattr(user_attributes, 'loginDisabled') and user_attributes.loginDisabled.value else 'NO',
                    'loginTime': getattr(user_attributes, 'loginTime', {}).value if hasattr(user_attributes, 'loginTime') else '',
                    'passwordExpirationTime': getattr(user_attributes, 'passwordExpirationTime', {}).value if hasattr(user_attributes, 'passwordExpirationTime') else '',
                    'is_inactive': is_inactive,
                    'is_pending': is_pending,
                    'generationQualifier': getattr(user_attributes, 'generationQualifier', {}).value if hasattr(user_attributes, 'generationQualifier') else ''
                }
                
                # Récupérer le nom complet du manager
                if result['FavvHierarMgrDN']:
                    try:
                        conn.search(result['FavvHierarMgrDN'], '(objectClass=*)', attributes=['fullName'])
                        if conn.entries:
                            # Standardiser les noms de champs pour le manager
                            manager_name = conn.entries[0].fullName.value
                            result['ChefHierarchique'] = manager_name
                            result['manager_name'] = manager_name  # Pour la compatibilité
                        else:
                            result['ChefHierarchique'] = 'Manager not found'
                            result['manager_name'] = 'Manager not found'
                    except Exception as e:
                        error_msg = f'Error fetching manager: {str(e)}'
                        result['ChefHierarchique'] = error_msg
                        result['manager_name'] = error_msg
                else:
                    result['ChefHierarchique'] = 'No manager specified'
                    result['manager_name'] = 'No manager specified'
                
                # Récupérer les groupes (groupMembership)
                if hasattr(user_attributes, 'groupMembership') and user_attributes.groupMembership:
                    for group_dn in user_attributes.groupMembership.values:
                        conn.search(group_dn, '(objectClass=groupOfNames)', attributes=['cn'])
                        if conn.entries:
                            group_cn = conn.entries[0].cn.value
                            result['groupMembership'].append({
                                'dn': group_dn,
                                'cn': group_cn,
                            })
                
                # Récupérer les rôles (nrfMemberOf)
                if hasattr(user_attributes, 'nrfMemberOf') and user_attributes.nrfMemberOf:
                    for role_dn in user_attributes.nrfMemberOf.values:
                        conn.search(role_dn, '(objectClass=nrfRole)', attributes=['cn', 'nrfRoleCategoryKey'])
                        if conn.entries:
                            role_cn = conn.entries[0].cn.value
                            role_catKey = conn.entries[0].nrfRoleCategoryKey.value if hasattr(conn.entries[0], 'nrfRoleCategoryKey') else 'N/A'
                            result['nrfMemberOf'].append({
                                'dn': role_dn,
                                'cn': role_cn,
                                'category': role_catKey
                            })
                
                # Appliquer le format simplifié si demandé
                if simplified:
                    # Créer une version simplifiée avec uniquement les champs essentiels
                    simplified_result = {
                        'dn': result['dn'],
                        'cn': result['CN'],
                        'fullName': result['fullName'],
                        'givenName': result['givenName'],
                        'sn': result['sn'],
                        'mail': result['mail'],
                        'FavvNatNr': result['FavvNatNr'],
                        'title': result['title'],
                        'ou': result['service'],
                        'FavvEmployeeType': result['favvEmployeeType'],
                        'workforceID': result['workforceID'],
                        'loginDisabled': result['loginDisabled'] == 'YES',
                        'FavvHierarMgrDN': result['FavvHierarMgrDN'],
                        'ChefHierarchique': result['ChefHierarchique'],
                        'groupMembership': result['groupMembership'],
                        'generationQualifier': result['generationQualifier'],
                        'is_inactive': result['is_inactive'],
                        'is_pending': result['is_pending']
                    }
                    result = simplified_result
                
                conn.unbind()
                return result
            
        except Exception as e:
            print(f"Error searching for user: {str(e)}")
            return None
    
    def create_user(self, cn, ldap_attributes, template_details=None):
        """
        Crée un nouvel utilisateur dans LDAP avec les attributs spécifiés.
        
        Args:
            cn (str): CN de l'utilisateur à créer
            ldap_attributes (dict): Attributs LDAP pour l'utilisateur
            template_details (dict, optional): Détails du template à utiliser (groupes, etc.)
            
        Returns:
            tuple: (bool, str, int, int) - Succès, mot de passe, groupes ajoutés, groupes échoués
        """
        try:
            conn = self._get_connection()

            # Préparer le DN de l'utilisateur
            user_dn = f"cn={cn},{self.usercreation_dn}"

            # Vérifier si l'utilisateur a un nom ou prénom court (3 caractères ou moins)
            has_short_name = False
            if 'givenName' in ldap_attributes and len(ldap_attributes['givenName']) <= 3:
                has_short_name = True
            elif 'sn' in ldap_attributes and len(ldap_attributes['sn']) <= 3:
                has_short_name = True
                
            # Nous avons besoin d'une référence à LDAPUserUtils pour générer le mot de passe
            # Cela sera résolu dans la classe wrapper (LDAPUserMixin)
            # Pour l'instant, nous utilisons une méthode locale pour générer le mot de passe
            # Cette méthode sera remplacée par l'appel à la méthode de LDAPUserUtils
            from .user_utils import LDAPUserUtils
            user_utils = LDAPUserUtils(self._get_config_for_utils())
            password = user_utils.generate_password_from_cn(cn, short_name=has_short_name)
        
            # Ajouter l'attribut userPassword
            ldap_attributes['userPassword'] = [password]
            # Ajouter l'attribut uid (UniqueID dans ConsoleOne)
            ldap_attributes['uid'] = [cn]
            
            # Assurer les valeurs d'objectClass appropriées - s'assurer que FavvAfscaUser est inclus
            ldap_attributes['objectClass'] = [
                'inetOrgPerson', 
                'top',
                'pwmUser',
                'FavvAfscaUser'
            ]

            # Ajouter l'utilisateur au serveur LDAP
            result = conn.add(user_dn, attributes=ldap_attributes)

            if result:
                print(f"User created successfully with password {password}! {conn.result}", 'success')
                
                # Si le template contient des groupes, ajouter l'utilisateur à ces groupes
                groups_added = 0
                groups_failed = 0
                
                if template_details and 'groupMembership' in template_details and template_details['groupMembership']:
                    for group_dn in template_details['groupMembership']:
                        group_result = self.add_user_to_group(user_dn, group_dn)
                        if group_result:
                            groups_added += 1
                        else:
                            groups_failed += 1
                
                return True, password, groups_added, groups_failed
            else:
                print(f"Failed to create user: {conn.result}", 'error')
                return False, None, 0, 0

        except Exception as e:
            print(f"An error occurred: {str(e)}", 'error')
            return False, None, 0, 0
            
    def add_user_to_group(self, user_dn, group_dn):
        """
        Ajoute un utilisateur à un groupe LDAP.
        
        Args:
            user_dn (str): DN de l'utilisateur
            group_dn (str): DN du groupe
            
        Returns:
            bool: Succès de l'opération
        """
        try:
            conn = self._get_connection()
            
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
            
            conn.unbind()
            return user_modify and group_modify
            
        except Exception as e:
            print(f"Error adding user to group: {str(e)}")
            return False
            
    def remove_user_from_group(self, user_dn, group_dn):
        """
        Retire un utilisateur d'un groupe LDAP.
        
        Args:
            user_dn (str): DN de l'utilisateur
            group_dn (str): DN du groupe
            
        Returns:
            bool: Succès de l'opération
        """
        try:
            conn = self._get_connection()
            
            # 1. Retirer le DN du groupe de l'attribut groupMembership de l'utilisateur
            user_modify = conn.modify(
                user_dn, 
                {'groupMembership': [(MODIFY_DELETE, [group_dn])]}
            )
            
            # 2. Retirer le DN de l'utilisateur de l'attribut member du groupe
            group_modify = conn.modify(
                group_dn, 
                {'member': [(MODIFY_DELETE, [user_dn])]}
            )
            
            conn.unbind()
            return user_modify and group_modify
            
        except Exception as e:
            print(f"Error removing user from group: {str(e)}")
            return False
            
    def update_user(self, user_dn, attributes=None, options=None):
        """
        Méthode étendue pour mettre à jour les utilisateurs, englobant aussi
        la fonctionnalité de complete_user_creation.
        
        Args:
            user_dn (str): DN de l'utilisateur à mettre à jour
            attributes (dict): Dictionnaire d'attributs à modifier
            options (dict): Options pour la mise à jour:
                - groups_to_add (list): Liste des groupes à ajouter
                - groups_to_remove (list): Liste des groupes à supprimer
                - reset_password (bool): Réinitialiser le mot de passe
                - expire_password (bool): Forcer l'expiration du mot de passe
                - target_container (str): Container cible pour déplacer l'utilisateur
                - change_reason (str): Raison du changement (pour journalisation)
                - is_completion (bool): Indique si c'est une opération de complétion
                
        Returns:
            tuple: (bool, str) - Succès de l'opération et message de statut
        """
        try:
            # Initialiser options et attributes avec des valeurs par défaut si non spécifiés
            if options is None:
                options = {}
            if attributes is None:
                attributes = {}
                
            # Extraire les options
            groups_to_add = options.get('groups_to_add', [])
            groups_to_remove = options.get('groups_to_remove', [])
            reset_password = options.get('reset_password', False)
            expire_password = options.get('expire_password', False)
            target_container = options.get('target_container')
            change_reason = options.get('change_reason')
            is_completion = options.get('is_completion', False)
            
            # Messages de journalisation pour le suivi des modifications
            log_messages = []
            if change_reason:
                log_messages.append(f"Reason for changes: {change_reason}")
            
            conn = self._get_connection()
            
            # Vérifier que l'utilisateur existe
            conn.search(user_dn, 
                    '(objectClass=*)', 
                    search_scope='BASE',
                    attributes=['cn', 'givenName', 'sn'])
            
            if not conn.entries:
                conn.unbind()
                return False, "User not found"
            
            # Récupérer le CN de l'utilisateur
            user_cn = conn.entries[0].cn.value
            
            # Vérifier si l'utilisateur a un nom ou prénom court
            has_short_name = False
            if hasattr(conn.entries[0], 'givenName') and len(conn.entries[0].givenName.value) <= 3:
                has_short_name = True
            elif hasattr(conn.entries[0], 'sn') and len(conn.entries[0].sn.value) <= 3:
                has_short_name = True
                
            # Si nous déplaçons l'utilisateur (is_completion ou target_container spécifié)
            new_dn = user_dn
            if target_container:
                # Construire le nouveau DN
                new_dn = f"cn={user_cn},{target_container}"
                
                # Déplacer l'utilisateur
                move_result = conn.modify_dn(user_dn, f"cn={user_cn}", new_superior=target_container)
                if not move_result:
                    print(f"Error moving user: {conn.result}")
                    conn.unbind()
                    return False, f"Error moving user: {conn.result}"
                
                log_messages.append(f"Moved user to container {target_container}")
            
            # Définir les attributs à modifier
            changes = {}
            for attr_name, attr_value in attributes.items():
                if attr_value:  # Ignorer les valeurs vides
                    changes[attr_name] = [(MODIFY_REPLACE, [attr_value])]
                    log_messages.append(f"Updated attribute {attr_name} to {attr_value}")
            
            # Appliquer les changements d'attributs
            if changes:
                conn.modify(new_dn, changes)
            
            # Gérer la réinitialisation du mot de passe
            if reset_password:
                # Générer un mot de passe à partir du CN
                from .user_utils import LDAPUserUtils
                user_utils = LDAPUserUtils(self._get_config_for_utils())
                password = user_utils.generate_password_from_cn(user_cn, short_name=has_short_name)
                
                conn.modify(new_dn, {'userPassword': [(MODIFY_REPLACE, [password])]})
                log_messages.append(f"Reset password to default")
            
            # Gérer l'expiration du mot de passe
            if expire_password:
                # Dans certains systèmes LDAP, il peut être nécessaire de supprimer l'attribut passwordExpirationTime
                # ou de le définir à une date dans le passé pour forcer le changement
                conn.modify(new_dn, {'passwordExpirationTime': [(MODIFY_DELETE, [])]})
                log_messages.append(f"Forced password change at next login")
            
            # Ajouter l'utilisateur aux nouveaux groupes
            for group_data in groups_to_add:
                # Déterminer le group_dn
                group_dn = None
                group_name = None
                
                if isinstance(group_data, str):
                    # Si group_data est une chaîne, supposer que c'est le DN complet du groupe
                    group_dn = group_data
                    # Extraire le CN du groupe à partir du DN
                    import re
                    match = re.search(r"cn=([^,]+)", group_dn, re.IGNORECASE)
                    if match:
                        group_name = match.group(1)
                    else:
                        group_name = "Unknown Group"
                elif isinstance(group_data, dict):
                    # Si group_data est un dictionnaire, chercher 'dn' puis 'cn' ou 'name'
                    group_dn = group_data.get('dn')
                    group_name = group_data.get('cn') or group_data.get('name')
                    
                    # Si aucun DN n'est trouvé mais qu'un nom est fourni, rechercher le groupe
                    if not group_dn and group_name:
                        search_bases = ['ou=Groups,ou=IAM-Security,o=COPY', self.app_base_dn, 'ou=GROUPS,ou=SYNC,o=COPY']
                        for base_dn in search_bases:
                            conn.search(base_dn, 
                                    f'(cn={group_name})', 
                                    search_scope='SUBTREE',
                                    attributes=['cn'])
                            if conn.entries:
                                group_dn = conn.entries[0].entry_dn
                                break
                
                # Si nous avons trouvé un DN de groupe, ajouter l'utilisateur
                if group_dn:
                    add_result = self.add_user_to_group(new_dn, group_dn)
                    if add_result:
                        log_messages.append(f"Added to group {group_name or group_dn}")
            
            # Supprimer l'utilisateur des groupes
            for group_data in groups_to_remove:
                # Déterminer le group_dn
                group_dn = None
                group_name = None
                
                if isinstance(group_data, str):
                    # Si group_data est une chaîne, supposer que c'est le DN du groupe
                    group_dn = group_data
                elif isinstance(group_data, dict):
                    # Si group_data est un dictionnaire, utiliser 'dn' et 'name'/'cn'
                    group_dn = group_data.get('dn')
                    group_name = group_data.get('name') or group_data.get('cn')
                
                # Si nous avons un DN de groupe, retirer l'utilisateur
                if group_dn:
                    remove_result = self.remove_user_from_group(new_dn, group_dn)
                    if remove_result:
                        log_messages.append(f"Removed from group {group_name or group_dn}")
            
            conn.unbind()
            
            # Construire le message de succès
            if len(log_messages) > 0:
                success_message = f"User {user_cn} updated successfully: " + "; ".join(log_messages)
            else:
                success_message = f"User {user_cn} updated successfully (no changes made)"
            
            return True, success_message
            
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return False, f"Error updating user: {str(e)}"
            
    def delete_user(self, user_dn):
        try:
            conn = self._get_connection()
            
            # Vérifier que l'utilisateur existe
            conn.search(user_dn, 
                    '(objectClass=*)', 
                    search_scope='BASE',
                    attributes=['cn'])
            
            if not conn.entries:
                conn.unbind()
                return False, "User not found."
            
            # Obtenir le CN de l'utilisateur pour le message
            user_cn = conn.entries[0].cn.value
            
            # Supprimer l'utilisateur
            conn.delete(user_dn)
            
            conn.unbind()
            return True, f"User {user_cn} deleted successfully."
            
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            return False, f"Error: {str(e)}"