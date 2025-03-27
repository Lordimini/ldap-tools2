# flask_app/models/ldap/users.py
import unicodedata
from ldap3 import Connection, MODIFY_REPLACE, MODIFY_DELETE, SUBTREE, MODIFY_ADD
import json
from .base import LDAPBase
from flask import flash,redirect,url_for

class LDAPUserMixin(LDAPBase):
    def search_user_final(self, search_param, search_type=None, simplified=False, search_active_only=False, return_list=False):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Define attributes based on the search mode
            if return_list:
                # Basic attributes for list-style results (like search_active_users)
                attributes = ['cn', 'fullName', 'mail', 'ou', 'title']
            else:
                # Comprehensive attributes for detailed user info
                attributes = [
                    'cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 
                    'fullName', 'mail', 'workforceID', 'groupMembership', 
                    'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 
                    'nrfMemberOf', 'loginDisabled', 'loginTime', 'passwordExpirationTime',
                    'generationQualifier'
                ]
            
            # Determine search parameters based on mode
            if search_type is None and not return_list:
                # Direct DN search
                user_dn = search_param
                search_scope = 'BASE'
                search_filter = '(objectClass=*)'
                search_base = user_dn
            else:
                # Construct search filter based on search_type
                if search_type == 'cn':
                    search_filter = f'(cn={search_param})'
                elif search_type == 'fullName':
                    # Use wildcards for fullName search when return_list is True (like search_active_users)
                    if return_list:
                        search_filter = f'(fullName=*{search_param}*)'
                    else:
                        search_filter = f'(fullName={search_param})'
                elif search_type == 'mail':
                    # Use wildcards for mail search when return_list is True
                    if return_list:
                        search_filter = f'(mail=*{search_param}*)'
                    else:
                        search_filter = f'(mail={search_param})'  
                elif search_type == 'workforceID':
                    search_filter = f'(workforceID={search_param})'
                elif search_type == 'FavvNatNr':
                    search_filter = f'(FavvNatNr={search_param})'
                else:
                    flash('Invalid search type.', 'danger')
                    return redirect(url_for('search_user'))
                
                search_scope = 'SUBTREE'
                
                # Determine which containers to search
                if search_active_only or return_list:
                    # Only search active users container
                    search_bases = [self.actif_users_dn]
                else:
                    # Search both active and inactive user containers
                    search_bases = [self.actif_users_dn, self.out_users_dn]
            
            # Handle list-style searches (similar to search_active_users)
            if return_list:
                users = []
                for search_base in search_bases:
                    conn.search(search_base, 
                            search_filter, 
                            search_scope=search_scope,
                            attributes=attributes)
                    
                    # Add results to the list
                    for entry in conn.entries:
                        users.append({
                            'dn': entry.entry_dn,
                            'cn': entry.cn.value if hasattr(entry, 'cn') else '',
                            'fullName': entry.fullName.value if hasattr(entry, 'fullName') else '',
                            'mail': entry.mail.value if hasattr(entry, 'mail') else '',
                            'ou': entry.ou.value if hasattr(entry, 'ou') else '',
                            'title': entry.title.value if hasattr(entry, 'title') else ''
                        })
                
                conn.unbind()
                return users
                
            # Handle single-user search (original search_user, search_user_by_dn, and get_user_details functionality)
            else:
                user_dn = None
                user_container = None
                
                # If not direct DN search, find the user first
                if search_type is not None:
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
                        if not return_list:  # Only flash message for single-user search
                            flash('User not found.', 'danger')
                        conn.unbind()
                        return None
                else:
                    # For direct DN search, search_base was already set to user_dn
                    conn.search(search_base, 
                            search_filter, 
                            search_scope=search_scope,
                            attributes=attributes)
                    
                    if not conn.entries:
                        conn.unbind()
                        return None
                        
                    # Determine which container the user is in
                    if self.out_users_dn in search_base:
                        user_container = self.out_users_dn
                    else:
                        user_container = self.actif_users_dn
                        
                # Determine if user is inactive
                is_inactive = user_container == self.out_users_dn
                
                # Get the user attributes
                user_attributes = conn.entries[0]
                
                # Build the result dictionary
                result = {
                    'dn': user_dn if search_type is not None else search_base,
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
                    'generationQualifier': getattr(user_attributes, 'generationQualifier', {}).value if hasattr(user_attributes, 'generationQualifier') else ''
                }
                
                # Fetch the manager's full name
                if result['FavvHierarMgrDN']:
                    try:
                        conn.search(result['FavvHierarMgrDN'], '(objectClass=*)', attributes=['fullName'])
                        if conn.entries:
                            # Standardize on field names for manager
                            manager_name = conn.entries[0].fullName.value
                            result['ChefHierarchique'] = manager_name
                            result['manager_name'] = manager_name  # For compatibility
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
                
                # Fetch the groups (groupMembership)
                if hasattr(user_attributes, 'groupMembership') and user_attributes.groupMembership:
                    for group_dn in user_attributes.groupMembership.values:
                        conn.search(group_dn, '(objectClass=groupOfNames)', attributes=['cn'])
                        if conn.entries:
                            group_cn = conn.entries[0].cn.value
                            result['groupMembership'].append({
                                'dn': group_dn,
                                'cn': group_cn,
                            })
                
                # Fetch the roles (nrfMemberOf)
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
                
                # Apply simplified format if requested
                if simplified:
                    # Create a simplified version with only essential fields
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
                        'generationQualifier': result['generationQualifier']
                    }
                    result = simplified_result
                
                conn.unbind()
                return result
            
        except Exception as e:
            print(f"Error searching for user: {str(e)}")
            return None
        
    def generate_unique_cn(self, given_name, sn):
        # Keep a copy of the original surname
        original_sn = sn

        # Load prefix options from JSON file
        with open('flask_app/config/prefix.json', 'r') as f:
            prefix_list = json.load(f)
    
        # Sort prefixes by length in descending order (longest first)
        prefix_list.sort(key=lambda x: len(x.get('prefix', '')), reverse=True)
    
        # Remove prefixes from surname
        for prefix_obj in prefix_list:
            prefix = prefix_obj.get('prefix', '')
            if prefix and sn.lower().startswith(prefix.lower()):
                # Remove the prefix and trim any leading whitespace
                sn = sn[len(prefix):].strip()
                # Once a prefix is found and removed, exit the loop
                break
    
        # If surname becomes empty after prefix removal (rare edge case)
        if not sn:
            sn = original_sn
    
        # Construct initial CN with first 3 chars of given_name and first 3 chars of sn (without prefix)
        # Handle short names gracefully
        first_part = given_name[:min(3, len(given_name))]
        second_part = sn[:min(3, len(sn))]
        cn_temp = f"{first_part}{second_part}"
    
        # Function to normalize and format in uppercase
        def normalize_cn(cn_string):
            normalized = unicodedata.normalize('NFD', cn_string)
            return ''.join(c for c in normalized if c.isalnum() and not unicodedata.combining(c)).upper()
    
        # Normalize the initial CN for the search
        cn = normalize_cn(cn_temp)
    
        # Check for uniqueness
        conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True) 
        i = 2
    
        while True:
            # Check if CN already exists
            search_result = conn.search(
                search_base=self.all_users_dn,
                search_filter=f'(cn={cn})',
                search_scope=SUBTREE
            )
        
            # If CN doesn't exist, return it
            if not conn.entries:
                break
        
            # If we've exhausted all available characters in the surname
            i += 1
            if i >= len(original_sn):
                print("All surname characters have been tried. Creating a 5-character CN.")
                # Create a 5-char CN (3 from given name + 2 from surname)
                cn_temp = f"{given_name[:min(3, len(given_name))]}{sn[:min(2, len(sn))]}"
                cn = normalize_cn(cn_temp)
                break
        
            # Generate a new CN by replacing the 3rd character of the second part with the next character from surname
            if len(sn) > 2:  # Make sure surname has at least 3 chars
                new_sn = sn[:2] + original_sn[i]
            else:
                new_sn = sn + original_sn[i]
        
            cn_temp = f"{first_part}{new_sn}"
            cn = normalize_cn(cn_temp)
    
        # Debug output
        print(f"Final CN: {cn}")
    
        return cn
   
    
    def generate_password_from_cn(self, cn, short_name=False):
        if len(cn) < 5:
            # Handle case with very short CN
            return cn + 'x4$*987'  # Added extra complexity
        
        # Check if short_name flag is True
        if short_name:
            # Add extra complexity to avoid password containing the original short name
            first_part = cn[:3]
            if len(cn) == 5:
                second_part = cn[3:] + 'x3'  # Add extra characters
            else:
                second_part = cn[3:6] + 'x3'  # Add extra characters
                
            return (second_part + first_part[0:2]).lower() + '$*987'
        else:
            # Original logic for normal names
            if len(cn) == 5:
                # For 5-character CN, swap first 3 with last 2
                first_part = cn[:3]
                second_part = cn[3:]
                return (second_part + first_part).lower() + '*987'
            else:
                # For 6+ character CN, swap first 3 with next 3
                first_part = cn[:3]
                second_part = cn[3:6]
                return (second_part + first_part).lower() + '*987'
    
    def create_user(self, cn, ldap_attributes, template_details=None):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            # Bind to the server
            conn.bind()

            # Prepare the user DN
            user_dn = f"cn={cn},{self.usercreation_dn}"

            # Check if the user has a short name or surname (3 characters or less)
            has_short_name = False
            if 'givenName' in ldap_attributes and len(ldap_attributes['givenName']) <= 3:
                has_short_name = True
            elif 'sn' in ldap_attributes and len(ldap_attributes['sn']) <= 3:
                has_short_name = True
                
            # Generate password from CN
            password = self.generate_password_from_cn(cn, short_name=has_short_name)
        
            # Add userPassword attribute
            ldap_attributes['userPassword'] = [password]
            # Ajouter l'attribut UniqueID
            ldap_attributes['UniqueID'] = [cn]    
            
            # Ensure proper objectClass values - make sure FavvAfscaUser is included
            ldap_attributes['objectClass'] = [
                'inetOrgPerson', 
                'top',
                'pwmUser',
                'FavvAfscaUser'
            ]

            # Add the user to the LDAP server
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
        
    def update_user(self, user_dn, attributes, groups_to_add=None, groups_to_remove=None, reset_password=False, expire_password=False, target_container=None, change_reason=None):
        try:
            # Messages de journalisation pour le suivi des modifications
            log_messages = []
            if change_reason:
                log_messages.append(f"Reason for changes: {change_reason}")
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Vérifier que l'utilisateur existe
            conn.search(user_dn, 
                    '(objectClass=*)', 
                    search_scope='BASE',
                    attributes=['cn'])
            
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
                
            # Définir les attributs à modifier
            changes = {}
            for attr_name, attr_value in attributes.items():
                changes[attr_name] = [(MODIFY_REPLACE, [attr_value])]
                log_messages.append(f"Updated attribute {attr_name} to {attr_value}")
            
            # Appliquer les changements d'attributs
            if changes:
                conn.modify(user_dn, changes)
            
            # Gérer la réinitialisation du mot de passe
            if reset_password:
                # Générer un mot de passe à partir du CN
                password = self.generate_password_from_cn(user_cn, short_name=has_short_name)
                conn.modify(user_dn, {'userPassword': [(MODIFY_REPLACE, [password])]})
                log_messages.append(f"Reset password to default")
            
            # Gérer l'expiration du mot de passe
            if expire_password:
                # Dans certains systèmes LDAP, il peut être nécessaire de supprimer l'attribut passwordExpirationTime
                # ou de le définir à une date dans le passé pour forcer le changement
                conn.modify(user_dn, {'passwordExpirationTime': [(MODIFY_DELETE, [])]})
                log_messages.append(f"Forced password change at next login")
            
            # Ajouter l'utilisateur aux nouveaux groupes
            if groups_to_add:
                for group_data in groups_to_add:
                    group_name = group_data.get('name')
                    if group_name:
                        # Rechercher le DN du groupe si non fourni
                        group_dn = group_data.get('dn')
                        if not group_dn:
                            # Rechercher le groupe dans les différents containers
                            search_bases = ['ou=Groups,ou=IAM-Security,o=COPY', self.app_base_dn, 'ou=GROUPS,ou=SYNC,o=COPY']
                            for base_dn in search_bases:
                                conn.search(base_dn, 
                                        f'(cn={group_name})', 
                                        search_scope='SUBTREE',
                                        attributes=['cn'])
                                if conn.entries:
                                    group_dn = conn.entries[0].entry_dn
                                    break
                        
                        if group_dn:
                            # Ajouter l'utilisateur au groupe
                            self.add_user_to_group(user_dn, group_dn)
                            log_messages.append(f"Added to group {group_name}")
            
            # Supprimer l'utilisateur des groupes
            if groups_to_remove:
                for group_data in groups_to_remove:
                    group_name = group_data.get('name')
                    group_dn = group_data.get('dn')
                    
                    if group_dn:
                        # Supprimer l'utilisateur du groupe
                        self.remove_user_from_group(user_dn, group_dn)
                        log_messages.append(f"Removed from group {group_name}")
            
            # Déplacer l'utilisateur vers un autre container si spécifié
            new_dn = user_dn
            if target_container:
                # Construire le nouveau DN
                new_dn = f"cn={user_cn},{target_container}"
                
                # Déplacer l'utilisateur
                conn.modify_dn(user_dn, f"cn={user_cn}", new_superior=target_container)
                log_messages.append(f"Moved user to container {target_container}")
            
            conn.unbind()
            
            # Construire le message de succès
            if len(log_messages) > 0:
                success_message = f"User {user_cn} updated successfully: " + "; ".join(log_messages)
            else:
                success_message = f"User {user_cn} updated successfully (no changes made)"
            
            return True, success_message
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}")
            return False, f"Error updating user: {str(e)}"

    def check_name_combination_exists(self, given_name, sn):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Create a search filter that combines both first name and last name
            search_filter = f'(&(givenName={given_name})(sn={sn}))'
            
            # Search in the users container
            search_base = self.all_users_dn
            
            conn.search(search_base=search_base,
                       search_filter=search_filter,
                       search_scope=SUBTREE,
                       attributes=['cn', 'givenName', 'sn', 'fullName'])
            
            if conn.entries:
                # User already exists, return the first matching user's DN
                user_dn = conn.entries[0].entry_dn
                conn.unbind()
                return True, user_dn
            
            conn.unbind()
            return False, ""
            
        except Exception as e:
            print(f"An error occurred while checking for name combination: {str(e)}")
            return False, ""
    
    def check_favvnatnr_exists(self, favvnatnr):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
        
            # Normaliser le FavvNatNr (enlever espaces et tirets)
            normalized_favvnatnr = favvnatnr.replace(' ', '').replace('-', '')
        
            # Créer un filtre de recherche pour le FavvNatNr
            search_filter = f'(FavvNatNr={normalized_favvnatnr})'
        
            # Rechercher dans le conteneur d'utilisateurs
            search_base = self.all_users_dn
        
            conn.search(search_base=search_base,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=['cn', 'FavvNatNr', 'fullName'])
        
            if conn.entries:
                # L'utilisateur existe déjà, retourner le DN du premier utilisateur correspondant
                user_dn = conn.entries[0].entry_dn
                fullname = conn.entries[0].fullName.value if hasattr(conn.entries[0], 'fullName') else "Unknown"
                conn.unbind()
                return True, user_dn, fullname
        
            conn.unbind()
            return False, "", ""
        
        except Exception as e:
            print(f"Une erreur s'est produite lors de la vérification du FavvNatNr: {str(e)}")
            return False, "", ""
        
    def get_pending_users(self):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Définir le DN du conteneur to-process
            to_process_dn = self.toprocess_users_dn
            
            # Rechercher tous les utilisateurs dans le conteneur
            conn.search(to_process_dn, 
                    '(objectClass=Person)', 
                    search_scope='SUBTREE',
                    attributes=['cn', 'fullName', 'title', 'favvEmployeeType'])
                                    
            users = []
            for entry in conn.entries:
                users.append({
                    'dn': entry.entry_dn,
                    'cn': entry.cn.value if hasattr(entry, 'cn') else 'Unknown',
                    'fullName': entry.fullName.value if hasattr(entry, 'fullName') else 'Unknown',
                    'title': entry.title.value if hasattr(entry, 'title') else 'Unknown',
                    'favvEmployeeType': entry.favvEmployeeType.value if hasattr(entry, 'favvEmployeeType') else 'Unknown'
                })
             
            conn.unbind()
            return users
            
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs en attente: {str(e)}")
            return []
        
    
    def complete_user_creation(self, user_dn, target_container, attributes, groups, set_password=False):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Vérifier que l'utilisateur existe
            conn.search(user_dn, 
                    '(objectClass=*)', 
                    search_scope='BASE',
                    attributes=['cn'])
            
            if not conn.entries:
                conn.unbind()
                return False, "Utilisateur non trouvé."
            
            # Obtenir le CN de l'utilisateur
            user_cn = conn.entries[0].cn.value
            
            # Vérifier si l'utilisateur a un nom ou prénom court
            has_short_name = False
            if hasattr(conn.entries[0], 'givenName') and len(conn.entries[0].givenName.value) <= 3:
                has_short_name = True
            elif hasattr(conn.entries[0], 'sn') and len(conn.entries[0].sn.value) <= 3:
                has_short_name = True
            
            # Construire le nouveau DN
            new_dn = f"cn={user_cn},{target_container}"
            
            # Créer un dictionnaire pour filtrer les attributs vides
            filtered_attributes = {}
            for k, v in attributes.items():
                if v:  # Si la valeur n'est pas vide
                    filtered_attributes[k] = [(MODIFY_REPLACE, [v])]
            
            # Déplacer l'utilisateur vers le container cible
            move_result = conn.modify_dn(user_dn, f"cn={user_cn}", new_superior=target_container)
            if not move_result:
                print(f"Error moving user: {conn.result}")
                conn.unbind()
                return False, f"Error moving user: {conn.result}"
            
            # Définir les attributs
            if filtered_attributes:
                attr_result = conn.modify(new_dn, changes=filtered_attributes)
                if not attr_result:
                    print(f"Error setting attributes: {conn.result}")
            
            # Définir le mot de passe si demandé
            if set_password:
                # Générer un mot de passe basé sur le CN
                password = self.generate_password_from_cn(user_cn, short_name=has_short_name)
                password_result = conn.modify(new_dn, {'userPassword': [(MODIFY_REPLACE, [password])]})
                if not password_result:
                    print(f"Error setting password: {conn.result}")
            
            # Log pour debugging
            print(f"Groups to add: {groups}")
            
            # Compteurs pour le rapport
            groups_added = 0
            groups_failed = 0
            
            # Ajouter l'utilisateur aux groupes
            for group_data in groups:
                print(f"Processing group data: {group_data}")
                
                # Vérifier que group_data est un dictionnaire
                if not isinstance(group_data, dict):
                    print(f"Warning: group_data is not a dict: {group_data}")
                    groups_failed += 1
                    continue
                
                # Obtenir le nom du groupe
                group_name = None
                if 'name' in group_data:
                    group_name = group_data['name']
                elif 'cn' in group_data:
                    group_name = group_data['cn']
                
                if not group_name:
                    print(f"Warning: no group name found in group data: {group_data}")
                    groups_failed += 1
                    continue
                
                print(f"Looking for group with name: {group_name}")
                
                # Rechercher le DN du groupe
                group_dn = None
                search_bases = ['ou=Groups,ou=IAM-Security,o=COPY', self.app_base_dn, 'ou=GROUPS,ou=SYNC,o=COPY']
                
                for base_dn in search_bases:
                    conn.search(base_dn, 
                            f'(cn={group_name})', 
                            search_scope='SUBTREE',
                            attributes=['cn'])
                    if conn.entries:
                        group_dn = conn.entries[0].entry_dn
                        print(f"Found group DN: {group_dn}")
                        break
                
                if not group_dn:
                    print(f"Warning: could not find group DN for name: {group_name}")
                    groups_failed += 1
                    continue
                
                # Ajouter l'utilisateur au groupe
                try:
                    # 1. Ajouter le DN du groupe à l'attribut groupMembership de l'utilisateur
                    user_modify = conn.modify(
                        new_dn, 
                        {'groupMembership': [(MODIFY_ADD, [group_dn])]}
                    )
                    
                    if not user_modify:
                        print(f"Error adding group to user's groupMembership: {conn.result}")
                    
                    # 2. Ajouter le DN de l'utilisateur à l'attribut member du groupe
                    group_modify = conn.modify(
                        group_dn, 
                        {'member': [(MODIFY_ADD, [new_dn])]}
                    )
                    
                    if not group_modify:
                        print(f"Error adding user to group's member attribute: {conn.result}")
                    
                    # Si les deux opérations ont réussi, incrémenter le compteur
                    if user_modify and group_modify:
                        print(f"Successfully added user to group: {group_name}")
                        groups_added += 1
                    else:
                        groups_failed += 1
                    
                except Exception as e:
                    print(f"Error adding user to group {group_name}: {str(e)}")
                    groups_failed += 1
            
            conn.unbind()
            success_message = f"User {user_cn} moved successfully to {target_container}. "
            if groups_added > 0:
                success_message += f"Added to {groups_added} groups. "
            if groups_failed > 0:
                success_message += f"Failed to add to {groups_failed} groups."
            
            return True, success_message
            
        except Exception as e:
            print(f"Error completing user creation: {str(e)}")
            return False, f"Error: {str(e)}"
            
    def delete_user(self, user_dn):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Vérifier que l'utilisateur existe
            conn.search(user_dn, 
                    '(objectClass=*)', 
                    search_scope='BASE',
                    attributes=['cn'])
            
            if not conn.entries:
                conn.unbind()
                return False, "Utilisateur non trouvé."
            
            # Obtenir le CN de l'utilisateur pour le message
            user_cn = conn.entries[0].cn.value
            
            # Supprimer l'utilisateur
            conn.delete(user_dn)
            
            conn.unbind()
            return True, f"Utilisateur {user_cn} supprimé avec succès."
            
        except Exception as e:
            print(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
            return False, f"Erreur: {str(e)}"
