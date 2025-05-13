from ldap3 import Server, Connection, ALL, MODIFY_ADD, SUBTREE
from flask_app.config.ldap_config import ldap_login_config
from flask import redirect, url_for, flash, json, render_template
import unicodedata

class LDAPModel:
    def __init__(self):
        self.ldap_server = ldap_login_config['ldap_server']
        self.bind_dn = ldap_login_config['bind_dn']
        self.password = ldap_login_config['bind_password']
        self.base_dn = ldap_login_config['base_dn']
        self.actif_users_dn = ldap_login_config['actif_users_dn']
        self.out_users_dn = ldap_login_config['out_users_dn']
        self.all_users_dn = ldap_login_config['all_users_dn']
        self.template_dn = ldap_login_config['template_dn']
        self.usercreation_dn = ldap_login_config['usercreation_dn']
        self.admin_group_dn = ldap_login_config['admin_group_dn']
        self.reader_group_dn = ldap_login_config['reader_group_dn']
        self.role_base_dn = ldap_login_config['role_base_dn']
        self.resource_base_dn = ldap_login_config['resource_base_dn']
        self.app_base_dn = ldap_login_config['app_base_dn']
        self.toprocess_users_dn = ldap_login_config['toprocess_users_dn']
        
    def authenticate(self, username, password):
        user_dn = f'cn={username},{self.actif_users_dn}'
        try:
            # Set up the server with a timeout
            server = Server(self.ldap_server, get_info=ALL, connect_timeout=10)
            
            # Connect with timeout parameters
            conn = Connection(
                server, 
                user=user_dn, 
                password=password, 
                auto_bind=True,
                check_names=True,
                read_only=False,
                client_strategy='SYNC',
                receive_timeout=10
            )
            
            # If we get here without an exception, authentication succeeded
            return conn
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None
    
    def authenticate_admin(self, username, password):
        try:
            server = Server(self.ldap_server, get_info=ALL)
            conn = Connection(server, username, password=password, auto_bind=True)
            return conn
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None

    
####################################################################
####################################################################
####################################################################

    def search_user(self, search_term, search_type):
            
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True) 
            
            if search_type == 'cn':
                search_filter = f'(cn={search_term})'
            elif search_type == 'fullName':
                search_filter = f'(fullName={search_term})'    
            elif search_type == 'workforceID':
                search_filter = f'(workforceID={search_term})'
            elif search_type == 'FavvNatNr':
                search_filter = f'(FavvNatNr={search_term})'
            else:
                flash('Invalid search type.', 'danger')
                return redirect(url_for('search_user'))
        
        # Search for the user in the entire subtree of o=FAVV and o=COPY
            user_dn = None
           
            for base_dn in [self.actif_users_dn, self.out_users_dn]:
                conn.search(base_dn, search_filter, search_scope='SUBTREE', attributes=['cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 'fullName', 'mail', 'workforceID', 'groupMembership', 'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 'nrfMemberOf', 'loginDisabled', 'loginTime', 'passwordExpirationTime'])

                if conn.entries:
                    user_dn = conn.entries[0].entry_dn
                    # Store which base DN the user was found in
                    user_container = base_dn
                    break    
            if user_dn:
                # Extract the attributes
                user_attributes = conn.entries[0]
                result = {
                    'CN': user_attributes.cn.value,
                    'favvEmployeeType': user_attributes.favvEmployeeType.value,
                    'fullName': user_attributes.fullName.value,
                    'mail': user_attributes.mail.value,
                    'sn': user_attributes.sn.value,
                    'givenName': user_attributes.givenName.value,
                    'workforceID': user_attributes.workforceID.value,
                    'title': user_attributes.title.value,
                    'service': user_attributes.ou.value,
                    'FavvNatNr': user_attributes.FavvNatNr.value,
                    'groupMembership': [],
                    'DirXMLAssociations': user_attributes['DirXML-Associations'].values if user_attributes['DirXML-Associations'] else [],
                    'FavvHierarMgrDN': user_attributes['FavvHierarMgrDN'].value if user_attributes['FavvHierarMgrDN'] else None,
                    'nrfMemberOf': [],
                    'loginDisabled': 'YES' if user_attributes.loginDisabled.value else 'NO',  # Convert boolean to YES/NO
                    'loginTime': user_attributes.loginTime.value,
                    'passwordExpirationTime': user_attributes.passwordExpirationTime.value,
                    'is_inactive': user_container == self.out_users_dn
                }
                # Fetch the manager's full name
                if result['FavvHierarMgrDN']:
                    try:
                        conn.search(result['FavvHierarMgrDN'], '(objectClass=*)', attributes=['fullName'])
                        if conn.entries:
                            result['ChefHierarchique'] = conn.entries[0].fullName.value
                        else:
                            result['ChefHierarchique'] = 'Manager not found'
                    except Exception as e:
                        result['ChefHierarchique'] = f'Error fetching manager: {str(e)}'
                else:
                    result['ChefHierarchique'] = 'No manager specified'

                # Fetch the groups (groupMembership)
                if user_attributes['groupMembership']:
                    for group_dn in user_attributes['groupMembership'].values:
                        conn.search(group_dn, '(objectClass=groupOfNames)', attributes=['cn'])
                        if conn.entries:
                            group_cn = conn.entries[0].cn.value
                            result['groupMembership'].append({
                                'dn': group_dn,
                                'cn': group_cn,
                            })
                
                # Fetch the roles (nrfMemberOf)
                if user_attributes['nrfMemberOf']:
                    for role_dn in user_attributes['nrfMemberOf'].values:
                        conn.search(role_dn, '(objectClass=nrfRole)', attributes=['cn', 'nrfRoleCategoryKey'])
                        if conn.entries:
                            role_cn = conn.entries[0].cn.value
                            role_catKey = conn.entries[0].nrfRoleCategoryKey.value
                            result['nrfMemberOf'].append({
                                'dn': role_dn,
                                'cn': role_cn,
                                'category': role_catKey
                            })

            else:
                result = None
                print("User not found.")
                flash('User not found.', 'danger')

            # Unbind the connection
            conn.unbind()    
            return result
            
####################################################################
####################################################################
####################################################################


    def get_group_users(self, group_name):
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True) 
            group_dn = None
            for base_dn in ['ou=Groups,ou=IAM-Security,o=COPY', self.app_base_dn, 'ou=GROUPS,ou=SYNC,o=COPY']:
                conn.search(base_dn, f'(cn={group_name})', search_scope='SUBTREE', attributes=['cn'])
                if conn.entries:
                    group_dn = conn.entries[0].entry_dn
                    break

            if group_dn:
                # Fetch the group's members
                conn.search(group_dn, '(objectClass=*)', attributes=['member'])
                if conn.entries and conn.entries[0].member:
                    members = conn.entries[0].member.values
                    users = []
                    # Fetch details for each member
                    for member_dn in members:
                        conn.search(member_dn, '(objectClass=*)', attributes=['cn', 'fullName', 'title', 'ou'])
                        if conn.entries:
                            user = conn.entries[0]
                            users.append({
                                'CN': user.cn.value,
                                'fullName': user.fullName.value,
                                'title': user.title.value if user.title else 'N/A',
                                'service': user.ou.value if user.ou else 'N/A'
                            })
                        else:
                            print(f"User not found for DN: {member_dn}")
                    result = {
                        'group_name': group_name,
                        'group_dn': group_dn,
                        'users': users
                    }
                else:
                    result = {
                        'group_name': group_name,
                        'group_dn': group_dn,
                        'users': []
                    }
                    flash('Group has no members.', 'info')
            else:
                result = None
                flash('Group not found.', 'danger')

            # Unbind the connection
            conn.unbind()
            return result
####################################################################
####################################################################
####################################################################        

    def get_role_users(self, role_cn):
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True) 
            # Search for the role in the entire subtree of o=FAVV and o=COPY
            role_dn = None
            for base_dn in self.role_base_dn:
                conn.search(base_dn, f'(cn={role_cn})', search_scope='SUBTREE', attributes=['equivalentToMe'])
                
                if conn.entries:
                    role_dn = conn.entries[0].entry_dn
                    break        
            if role_dn:
                print(f"Role found: {role_dn}")

                # Fetch the role's equivalentToMe attribute (list of user DNs)
                conn.search(role_dn, '(objectClass=nrfRole)', attributes=['equivalentToMe'])
                if conn.entries and conn.entries[0].equivalentToMe:
                    user_dns = conn.entries[0].equivalentToMe.values
                    #print(f"User DNs: {user_dns}")
                    users = []

                    # Fetch details for each user
                    for user_dn in user_dns:
                        conn.search(user_dn, '(objectClass=*)', attributes=['cn', 'fullName', 'title', 'ou'])
                        if conn.entries:
                            user = conn.entries[0]
                            
                            users.append({
                                'CN': user.cn.value,
                                'fullName': user.fullName.value,
                                'ou': user.ou.value,
                                'title': user.title.value if user.title else 'N/A'
                            })
                        else:
                            print(f"User not found for DN: {user_dn}")

                    result = {
                        'role_cn': role_cn,
                        'role_dn': role_dn,
                        'users': users
                    }
                else:
                    result = {
                        'role_cn': role_cn,
                        'role_dn': role_dn,
                        'users': []
                    }
                    flash('Role has no equivalent users.', 'info')
            else:
                result = None
                print("Role not found dans ldap.py.")
                flash('Role not found.', 'danger')

            # Unbind the connection
            conn.unbind()
            return result
            
####################################################################
####################################################################
####################################################################
    
    def get_role_groups(self, role_cn):
        
        if role_cn:
            try:
                # Connect to the LDAP server
                conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
                # Step 1: Search for the role in the RoleDefs container to get its DN
                role_base_dn = self.role_base_dn
                conn.search(role_base_dn, f'(cn={role_cn})', search_scope='SUBTREE', attributes=['entryDN'])

                if not conn.entries:
                    print(f'Role "{role_cn}" not found.', 'danger')
                    return render_template('role_groups.html', result=None, prefill_role_cn=role_cn)

                role_dn = conn.entries[0].entry_dn
                print(f"Role DN: {role_dn}")

                # Step 2: Search for nrfResourceAssociation objects in the ResourceAssociations container
                resource_base_dn = self.resource_base_dn
                conn.search(resource_base_dn, f'(nrfRole={role_dn})', search_scope='SUBTREE', attributes=['nrfRole', 'nrfResource'])

                # Step 3: Extract the cn of the nrfResource values
                groups = []
                for entry in conn.entries:
                    nrf_resource_dn = entry.nrfResource.value
                    if nrf_resource_dn:
                        # Extract the cn from the DN (e.g., "cn=GroupName,..." -> "GroupName")
                        nrf_resource_cn = nrf_resource_dn.split(',')[0].split('=')[1]
                        groups.append({
                            'nrfResource': nrf_resource_cn
                        })

                if groups:
                    result = {
                        'role_cn': role_cn,
                        'groups': groups
                    }
                else:
                    result = None
                    flash('No groups found for this role.', 'info')

                # Unbind the connection
                conn.unbind()
                return result
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'danger')
        

####################################################################
####################################################################
####################################################################
    
    
    def view_role(self, dn):
        conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
    
    # Fetch the role's attributes
        conn.search(dn, '(objectClass=nrfRole)', search_scope='BASE', attributes=['cn', 'equivalentToMe'])

        if conn.entries:
            role = conn.entries[0]
            role_cn = role.cn.value
            equivalent_users = role.equivalentToMe.values if role.equivalentToMe else []

            # Fetch details for each user
            users = []
            for user_dn in equivalent_users:
                conn.search(user_dn, '(objectClass=*)', attributes=['cn', 'fullName', 'ou', 'nrfAssignedRoles'])
                if conn.entries:
                    user = conn.entries[0]
                    nrf_assigned_roles = user.nrfAssignedRoles.values if user.nrfAssignedRoles else []

                    # Extract <req_desc> for the current role
                    req_desc = "No description available"
                    for role_assignment in nrf_assigned_roles:
                        # Split the role DN and XML string
                        parts = role_assignment.split('#0#')
                        if len(parts) >= 2:
                            role_dn_part = parts[0].strip()  # Role DN
                            xml_part = parts[1].strip()  # XML part

                            # Check if the role DN matches the current role
                            if role_dn_part == dn:
                                # Parse the XML part to extract <req_desc>
                                start_index = xml_part.find('<req_desc>') + len('<req_desc>')
                                end_index = xml_part.find('</req_desc>')
                                if start_index != -1 and end_index != -1:
                                    req_desc = xml_part[start_index:end_index].strip()
                                    break

                    users.append({
                    'CN': user.cn.value,
                    'fullName': user.fullName.value,
                    'ou': user.ou.value if user.ou else 'N/A',
                    'req_desc': req_desc  # Add the extracted <req_desc>
                    })
            # Extract the parent container DN
            parent_dn = ','.join(dn.split(',')[1:])  # Remove the first RDN to get the parent DN
        
            conn.unbind()
        
            return {
                'dn': dn, 
                'role_cn': role_cn, 
                'user_count': len(equivalent_users), 
                'users': users, 
                'parent_dn': parent_dn
            }
        else:
            conn.unbind()
            return None
   
  
    def get_service_users(self, service_name):
            users = []
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True) 
            for base_dn in self.actif_users_dn:
                conn.search(base_dn, f'(ou={service_name})', search_scope='SUBTREE', attributes=['cn', 'fullName', 'title', 'mail'])
                for entry in conn.entries:
                    users.append({
                        'CN': entry.cn.value,
                        'fullName': entry.fullName.value,
                        'title': entry.title.value if entry.title else 'N/A',
                        'mail': entry.mail.value if entry.mail else 'N/A'
                    })

            if users:
                result = {
                    'service_name': service_name,
                    'users': users
                }
            else:
                result = None
                flash('No users found in this service.', 'info')

            # Unbind the connection
            conn.unbind()
            return result
        
        
    def autocomplete_group(self, search_term):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, 
                              password=self.password, auto_bind=True)
            
            groups = []
            for base_dn in [self.base_dn, self.app_base_dn]:
                conn.search(base_dn, f'(cn=*{search_term}*)', 
                           search_scope='SUBTREE', attributes=['cn'])
                
                for entry in conn.entries:
                    if ('cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY' 
                        not in entry.entry_dn):
                        groups.append({
                            'label': f"{entry.cn.value} ({entry.entry_dn})",
                            'value': entry.cn.value
                        })
            
            conn.unbind()
            return groups
            
        except Exception as e:
            raise e

    def autocomplete_fullName(self, search_term):
        """
        Méthode optimisée pour l'autocomplétion du champ fullName.
        
        Args:
            search_term (str): Le terme de recherche saisi par l'utilisateur
            
        Returns:
            list: Liste des correspondances trouvées
        """
        # Ne pas effectuer de recherche si le terme est trop court
        if len(search_term) < 3:
            return []
        
        # Échapper les caractères spéciaux de LDAP dans le terme de recherche
        search_term_escaped = self._escape_ldap_filter(search_term)
        
        # Construire un filtre LDAP optimisé
        # Utiliser un filtre qui commence par pour être plus efficace
        ldap_filter = f'(&(objectClass=Person)(fullName=*{search_term_escaped}*))'
        
        # Définir les attributs spécifiques à récupérer (au lieu de tous)
        attributes = ['cn', 'fullName']
        
        # Établir la connexion LDAP
        conn = self._get_connection()
        
        try:
            # Effectuer la recherche avec une limite de taille pour éviter de récupérer trop de résultats
            conn.search(
                search_base= self.all_users_dn,  # Base de recherche appropriée 
                search_filter=ldap_filter,
                search_scope='SUBTREE',
                attributes=attributes,
                size_limit=20,  # Limiter à 20 résultats
                time_limit=5    # Limiter le temps de recherche à 5 secondes
            )
            
            # Transformer les résultats pour l'autocomplétion
            results = []
            for entry in conn.entries:
                if hasattr(entry, 'fullName') and entry.fullName.value:
                    results.append({
                        'label': entry.fullName.value,
                        'value': entry.fullName.value
                    })
                    
            # Limiter le nombre de résultats retournés
            return results[:20]
        
        except Exception as e:
            print(f"Erreur lors de l'autocomplétion: {str(e)}")
            return []
        finally:
            # S'assurer que la connexion est fermée
            conn.unbind()
        
    def _escape_ldap_filter(self, input_string):
        """
        Échapper les caractères spéciaux dans un filtre LDAP.
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

    def _get_connection(self):
        """
        Obtenir une connexion LDAP déjà établie pour réutilisation.
        """
        # On pourrait implémenter un pool de connexions ici
        return Connection(
            self.ldap_server,
            user=self.bind_dn,
            password=self.password,
            auto_bind=True
        )   
    
    def autocomplete_role(self, search_term):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, 
                              password=self.password, auto_bind=True)
            
            roles = []
            for base_dn in self.role_base_dn:
                conn.search(base_dn, f'(cn=*{search_term}*)', search_scope='SUBTREE', attributes=['cn'])
            for entry in conn.entries:
                roles.append({
                    'label': f"{entry.cn.value} ({entry.entry_dn})",
                    'value': entry.cn.value
                })
            
            conn.unbind()
            return roles
            
        except Exception as e:
            raise e

    
    def autocomplete_services(self, search_term):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, 
                              password=self.password, auto_bind=True)
            # Search for services (OUs) in the entire subtree of o=FAVV and o=COPY
            services = []
            for base_dn in [self.app_base_dn, self.base_dn]:
                conn.search(base_dn, f'(ou=*{search_term}*)', search_scope='SUBTREE', attributes=['ou'])
            for entry in conn.entries:
                services.append({
                    'label': entry.ou.value,
                    'value': entry.ou.value
                })

        # Unbind the connection
            conn.unbind()
            return services

        except Exception as e:
            raise e

    

####################################################################
####################################################################
####################################################################

    def get_ldap_children(self, current_dn):
        conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True) 
        # Search for entries under the current DN
        conn.search(current_dn, '(objectClass=*)', search_scope='LEVEL', attributes=['cn', 'objectClass'])

        # Build the list of child entries
        children = []
        for entry in conn.entries:
            if 'nrfRoleDefs' in entry.objectClass.values:
                # This is a container (nrfRoleDefs)
                children.append({
                    'type': 'container',
                    'name': entry.cn.value,
                    'dn': entry.entry_dn
                })
            elif 'nrfRole' in entry.objectClass.values:
                # This is a role (nrfRole)
                localized_name = None
                if 'nrfLocalizedNames' in entry.entry_attributes:
                    # Parse the nrfLocalizedNames attribute
                    raw_localized_names = entry.nrfLocalizedNames.value
                    if raw_localized_names:
                        # Extract the value after 'en~' and before the first '|'
                        parts = raw_localized_names.split('|')
                        for part in parts:
                            if part.startswith('en~'):
                                localized_name = part[3:]  # Remove 'en~'
                                break
                role_cn = entry.cn.value
                children.append({
                    'type': 'role',
                    'name': localized_name or entry.cn.value,  # Use parsed name or fallback to CN
                    'dn': entry.entry_dn,
                    'role_cn': role_cn
                })

        # Determine the parent DN
        if current_dn == self.role_base_dn:
            parent_dn = None  # Already at the root container
        else:
            parent_dn = ','.join(current_dn.split(',')[1:])  # Remove the first RDN to get the parent DN

        # Unbind the connection
        conn.unbind()
        return children, parent_dn

    def generate_unique_cn(self, given_name, sn):
        """
        Generate a unique CN (Common Name) for a new user based on their given name and surname.
        Handles prefixes in surnames and normalizes special characters.
    
        Parameters:
        given_name (str): User's first name
        sn (str): User's surname (last name)
    
        Returns:
        str: A unique CN for the user in UPPERCASE
        """
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
    
    def create_user(self, cn, ldap_attributes, template_details=None):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            # Bind to the server
            conn.bind()

            # Prepare the user DN
            user_dn = f"cn={cn},{self.usercreation_dn}"

            # Generate password from CN
            password = self.generate_password_from_cn(cn)
        
            # Add userPassword attribute
            ldap_attributes['userPassword'] = [password]

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
        
    
        
    def get_user_types_from_ldap(self, dn):
        conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
    
        search_base = dn
        attributes = ['cn', 'description', 'title']
    
        conn.search(search_base=search_base,
                    search_filter='(objectClass=template)',
                    search_scope=SUBTREE,
                    attributes=attributes)
    
        # Use a dictionary to ensure uniqueness by cn
        unique_types = {}
        for entry in conn.entries:
            if hasattr(entry, 'description') and entry.description:
                title_value = entry.title.value if hasattr(entry, 'title') and entry.title else None
                unique_types[entry.cn.value] = {
                    'description': entry.description.value,
                    'title': title_value
                }
    
        # Convert to the list of dictionaries format
        user_types = [{'value': cn, 'label': data['description'], 'title': data['title']} 
                      for cn, data in unique_types.items()]
    
        conn.unbind()
        return user_types
    
    def check_name_combination_exists(self, given_name, sn):
        """
        Check if a user with the given first name and last name already exists in LDAP.
        
        Parameters:
        given_name (str): The given name (first name) to check
        sn (str): The surname (last name) to check
        
        Returns:
        tuple: (bool, str) - (True if exists + user DN, False if not exists + empty string)
        """
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
        
    
    def get_template_details(self, template_cn):
        """
        Get details of a specific template by its CN including associated groups
        
        Parameters:
        template_cn (str): The CN of the template to retrieve
        
        Returns:
        dict: Template attributes or None if not found
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
        
            search_base = self.template_dn  # Base DN for templates
            search_filter = f'(cn={template_cn})'
        
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['cn', 'description', 'title', 'objectClass', 'ou', 
                            'FavvExtDienstMgrDn', 'FavvEmployeeType', 'FavvEmployeeSubType',
                            'groupMembership']  # Ajout de l'attribut groupMembership
            )
        
            if conn.entries:
                entry = conn.entries[0]
                template_data = {
                    'cn': entry.cn.value,
                    'description': entry.description.value if hasattr(entry, 'description') and entry.description else None,
                    'title': entry.title.value if hasattr(entry, 'title') and entry.title else None,
                    'objectClass': entry.objectClass.values if hasattr(entry, 'objectClass') and entry.objectClass else [],
                    'ou': entry.ou.value if hasattr(entry, 'ou') and entry.ou else None,
                    'FavvExtDienstMgrDn': entry.FavvExtDienstMgrDn.value if hasattr(entry, 'FavvExtDienstMgrDn') and entry.FavvExtDienstMgrDn else None,
                    'FavvEmployeeType': entry.FavvEmployeeType.value if hasattr(entry, 'FavvEmployeeType') and entry.FavvEmployeeType else None,
                    'FavvEmployeeSubType': entry.FavvEmployeeSubType.value if hasattr(entry, 'FavvEmployeeSubType') and entry.FavvEmployeeSubType else None,
                    'groupMembership': entry.groupMembership.values if hasattr(entry, 'groupMembership') and entry.groupMembership else []
                }
                conn.unbind()
                return template_data
        
            conn.unbind()
            return None
        
        except Exception as e:
            print(f"Error retrieving template details: {str(e)}")
            return None
        

    def generate_password_from_cn(self, cn):
        """
        Generate a password from a CN by swapping the first 3 characters with the next 3 
        (or 2 if CN is only 5 characters long) and adding '*987'
    
        Example: 
        - For CN 'AUDRIG', password would be 'RIGAUD*987'
        - For CN 'ABCDE', password would be 'DEABC*987'
        """
        if len(cn) < 5:
            # Handle case with very short CN
            return cn + '*987'
    
        # Check if CN is 5 characters or 6+ characters
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
    
    
    def check_favvnatnr_exists(self, favvnatnr):
        """
        Vérifie si un utilisateur avec le numéro FavvNatNr donné existe déjà dans LDAP.
    
        Parameters:
        favvnatnr (str): Le numéro FavvNatNr à vérifier
    
        Returns:
        tuple: (bool, str) - (True si existe + user DN, False si n'existe pas + chaîne vide)
        """
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
        
        
    def get_managers(self):
        """
        Récupère la liste des utilisateurs ayant FavvDienstHoofd=YES
    
        Returns:
        list: Liste des utilisateurs chefs hiérarchiques avec leur fullName et DN
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
        
            # Rechercher les utilisateurs avec FavvDienstHoofd=YES
            search_base = self.actif_users_dn
            search_filter = '(FavvDienstHoofd=YES)'
        
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope=SUBTREE,
                        attributes=['cn', 'fullName', 'title', 'mail'])
        
            managers = []
            for entry in conn.entries:
                managers.append({
                    'dn': entry.entry_dn,
                    'fullName': entry.fullName.value if entry.fullName else '',
                    'title': entry.title.value if entry.title else '',
                    'mail': entry.mail.value if entry.mail else ''
                })
        
            conn.unbind()
            return managers
        
        except Exception as e:
            print(f"Erreur lors de la récupération des chefs hiérarchiques: {str(e)}")
            return []
        
    def autocomplete_managers(self, search_term):
        """
        Fournit une fonctionnalité d'autocomplétion pour les chefs hiérarchiques
    
        Parameters:
        search_term (str): Terme de recherche pour filtrer les chefs hiérarchiques
    
        Returns:
        list: Liste des chefs hiérarchiques correspondant au terme de recherche
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
        
            managers = []
            search_base = self.actif_users_dn
            search_filter = f'(&(FavvDienstHoofd=YES)(fullName=*{search_term}*))'
        
            conn.search(search_base=search_base,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=['cn', 'fullName', 'title', 'mail'])
        
            for entry in conn.entries:
                managers.append({
                    'label': f"{entry.fullName.value} - {entry.mail.value if entry.mail else 'No email'} - {entry.title.value if entry.title else 'No title'}",
                    'value': entry.fullName.value
                })
        
            conn.unbind()
            return managers
        
        except Exception as e:
            print(f"Erreur lors de l'autocomplétion des chefs hiérarchiques: {str(e)}")
            return []

    def get_total_users_count(self):
        """
        Récupère le nombre total d'utilisateurs dans la base de recherche
        
        Returns:
            int: Nombre total d'utilisateurs
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Recherche tous les utilisateurs dans la base spécifiée
            search_base = self.actif_users_dn
            search_filter = '(objectClass=Person)'
            
            # Effectuer la recherche avec l'option paged_size pour gérer un grand nombre d'utilisateurs
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn'],
                        paged_size=1000)
                        
            # Compter le nombre total d'entrées
            total_entries = len(conn.entries)
            
            # Si la recherche est paginée, récupérer toutes les pages
            cookie = conn.result.get('controls', {}).get('1.2.840.113556.1.4.319', {}).get('value', {}).get('cookie')
            while cookie:
                conn.search(search_base=search_base,
                            search_filter=search_filter,
                            search_scope='SUBTREE',
                            attributes=['cn'],
                            paged_size=1000,
                            paged_cookie=cookie)
                total_entries += len(conn.entries)
                cookie = conn.result.get('controls', {}).get('1.2.840.113556.1.4.319', {}).get('value', {}).get('cookie')
            
            conn.unbind()
            return total_entries
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs: {str(e)}")
            return 0

    def get_recent_logins_count(self, days=7):
        """
        Récupère le nombre d'utilisateurs qui se sont connectés récemment
        
        Args:
            days (int): Nombre de jours à considérer pour 'récent'
            
        Returns:
            int: Nombre d'utilisateurs récemment connectés
        """
        try:
            import time
            from datetime import datetime, timedelta
            
            # Calculer la date limite (timestamp en format GeneralizedTime)
            limit_date = datetime.now() - timedelta(days=days)
            limit_timestamp = limit_date.strftime("%Y%m%d%H%M%SZ")
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs avec une date de connexion récente
            search_base = self.actif_users_dn
            search_filter = f'(&(objectClass=Person)(loginTime>={limit_timestamp}))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn', 'loginTime'])
            
            recent_logins = len(conn.entries)
            
            conn.unbind()
            return recent_logins
            
        except Exception as e:
            print(f"Erreur lors du comptage des connexions récentes: {str(e)}")
            return 0

    def get_disabled_accounts_count(self):
        """
        Récupère le nombre de comptes désactivés
        
        Returns:
            int: Nombre de comptes désactivés
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs avec loginDisabled=TRUE
            search_base = self.actif_users_dn
            search_filter = '(&(objectClass=Person)(loginDisabled=TRUE))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn'])
            
            disabled_count = len(conn.entries)
            
            conn.unbind()
            return disabled_count
            
        except Exception as e:
            print(f"Erreur lors du comptage des comptes désactivés: {str(e)}")
            return 0

    def get_inactive_users_count(self, months=3):
        """
        Récupère le nombre d'utilisateurs actifs (loginDisabled=FALSE) qui ne se sont pas 
        connectés depuis plus de X mois
        
        Args:
            months (int): Nombre de mois d'inactivité
            
        Returns:
            int: Nombre d'utilisateurs inactifs
        """
        try:
            #import time
            from datetime import datetime, timedelta
            
            # Calculer la date limite (timestamp en format GeneralizedTime)
            limit_date = datetime.now() - timedelta(days=30*months)
            limit_timestamp = limit_date.strftime("%Y%m%d%H%M%SZ")
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs actifs mais avec une ancienne date de connexion
            search_base = self.actif_users_dn
            search_filter = f'(&(objectClass=Person)(loginDisabled=FALSE)(loginTime<={limit_timestamp}))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn', 'loginTime'])
            
            inactive_users = len(conn.entries)
            
            conn.unbind()
            return inactive_users
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs inactifs: {str(e)}")
            return 0
    
    def get_expired_password_users_count(self):
        """
        Récupère le nombre d'utilisateurs actifs (loginDisabled=FALSE) dont le mot de passe est expiré
        
        Returns:
            int: Nombre d'utilisateurs avec mot de passe expiré
        """
        try:
            import time
            from datetime import datetime
            
            # Obtenir la date actuelle au format LDAP GeneralizedTime
            current_date = datetime.now().strftime("%Y%m%d%H%M%SZ")
            
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs actifs avec un mot de passe expiré
            search_base = self.actif_users_dn
            search_filter = f'(&(objectClass=Person)(loginDisabled=FALSE)(passwordExpirationTime<={current_date}))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn', 'passwordExpirationTime'])
            
            expired_password_users = len(conn.entries)
            
            conn.unbind()
            return expired_password_users
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs avec mot de passe expiré: {str(e)}")
            return 0
    
    def get_never_logged_in_users_count(self):
        """
        Récupère le nombre d'utilisateurs actifs (loginDisabled=FALSE) qui n'ont jamais effectué de connexion
        (absence de l'attribut loginTime ou valeur vide)
        
        Returns:
            int: Nombre d'utilisateurs qui ne se sont jamais connectés
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher les utilisateurs actifs sans attribut loginTime
            search_base = self.actif_users_dn
            search_filter = '(&(objectClass=Person)(loginDisabled=FALSE)(!(loginTime=*)))'
            
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope='SUBTREE',
                        attributes=['cn'])
            
            never_logged_in = len(conn.entries)
            
            conn.unbind()
            return never_logged_in
            
        except Exception as e:
            print(f"Erreur lors du comptage des utilisateurs n'ayant jamais effectué de connexion: {str(e)}")
            return 0
    
    def add_user_to_group(self, user_dn, group_dn):
        """
        Ajoute un utilisateur à un groupe et met à jour les attributs correspondants
        
        Parameters:
        user_dn (str): DN de l'utilisateur à ajouter
        group_dn (str): DN du groupe auquel ajouter l'utilisateur
        
        Returns:
        bool: True si l'opération a réussi, False sinon
        """
        try:
            # Établir une connexion au serveur LDAP
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
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
            # Vérifions d'abord si c'est un groupe de type rôle
            conn.search(group_dn, '(objectClass=nrfRole)', search_scope='BASE')
            if conn.entries:
                # C'est un groupe de type rôle, mettons à jour equivalentToMe
                equiv_modify = conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_ADD, [user_dn])]}
                )
            else:
                # Pas un groupe de type rôle, pas besoin de mettre à jour equivalentToMe
                equiv_modify = True
            
            # Vérifier si toutes les opérations ont réussi
            success = user_modify and group_modify and equiv_modify
            
            # Fermer la connexion
            conn.unbind()
            
            return success
        
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'utilisateur au groupe: {str(e)}")
            return False
    
    def get_pending_users(self):
        """
        Récupère la liste des utilisateurs en attente dans le conteneur to-process.
        
        Returns:
            list: Liste d'objets utilisateur avec dn, cn et fullName
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Définir le DN du conteneur to-process
            to_process_dn = self.toprocess_users_dn
            
            # Rechercher tous les utilisateurs dans le conteneur
            conn.search(to_process_dn, 
                    '(objectClass=Person)', 
                    search_scope='SUBTREE',
                    attributes=['cn', 'fullName'])
            
            users = []
            for entry in conn.entries:
                users.append({
                    'dn': entry.entry_dn,
                    'cn': entry.cn.value if hasattr(entry, 'cn') else 'Unknown',
                    'fullName': entry.fullName.value if hasattr(entry, 'fullName') else 'Unknown'
                })
            
            conn.unbind()
            return users
            
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs en attente: {str(e)}")
            return []
        
    def get_user_details(self, user_dn):
        """
        Récupère les détails complets d'un utilisateur à partir de son DN.
        
        Args:
            user_dn (str): DN de l'utilisateur
            
        Returns:
            dict: Détails de l'utilisateur
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Rechercher l'utilisateur
            conn.search(user_dn, 
                    '(objectClass=*)', 
                    search_scope='BASE',
                    attributes=['cn', 'fullName', 'givenName', 'sn', 'mail', 
                                'FavvNatNr', 'title', 'ou', 'FavvEmployeeType', 
                                'workforceID', 'FavvHierarMgrDN', 'loginDisabled', 
                                'groupMembership','generationQualifier'])
            
            if not conn.entries:
                conn.unbind()
                return None
            
            entry = conn.entries[0]
            
            # Construire l'objet utilisateur
            user = {
                'dn': user_dn,
                'cn': entry.cn.value if hasattr(entry, 'cn') else '',
                'fullName': entry.fullName.value if hasattr(entry, 'fullName') else '',
                'givenName': entry.givenName.value if hasattr(entry, 'givenName') else '',
                'sn': entry.sn.value if hasattr(entry, 'sn') else '',
                'mail': entry.mail.value if hasattr(entry, 'mail') else '',
                'FavvNatNr': entry.FavvNatNr.value if hasattr(entry, 'FavvNatNr') else '',
                'title': entry.title.value if hasattr(entry, 'title') else '',
                'ou': entry.ou.value if hasattr(entry, 'ou') else '',
                'FavvEmployeeType': entry.FavvEmployeeType.value if hasattr(entry, 'FavvEmployeeType') else '',
                'workforceID': entry.workforceID.value if hasattr(entry, 'workforceID') else '',
                'loginDisabled': entry.loginDisabled.value if hasattr(entry, 'loginDisabled') else False,
                'manager_dn': entry.FavvHierarMgrDN.value if hasattr(entry, 'FavvHierarMgrDN') else '',
                'manager_name': '',
                'group_memberships': [],
                'generationQualifier': entry.generationQualifier.value if hasattr(entry, 'generationQualifier') else ''
            }
            
            # Récupérer le nom du manager si présent
            if user['manager_dn']:
                conn.search(user['manager_dn'], 
                        '(objectClass=*)', 
                        attributes=['fullName'])
                if conn.entries:
                    user['manager_name'] = conn.entries[0].fullName.value
            
            # Récupérer les groupes si présents
            if hasattr(entry, 'groupMembership') and entry.groupMembership:
                for group_dn in entry.groupMembership.values:
                    conn.search(group_dn, 
                            '(objectClass=*)', 
                            attributes=['cn'])
                    if conn.entries:
                        user['group_memberships'].append({
                            'dn': group_dn,
                            'cn': conn.entries[0].cn.value
                        })
            
            conn.unbind()
            return user
            
        except Exception as e:
            print(f"Erreur lors de la récupération des détails de l'utilisateur: {str(e)}")
            return None
    
    def complete_user_creation(self, user_dn, target_container, attributes, groups, set_password=False):
        """
        Complète la création d'un utilisateur en le déplaçant vers le container cible
        et en définissant les attributs supplémentaires.
        
        Args:
            user_dn (str): DN de l'utilisateur
            target_container (str): DN du container cible
            attributes (dict): Attributs à définir
            groups (list): Liste des groupes à ajouter (format: [{'name': 'group_name'}])
            set_password (bool): Si True, définit un mot de passe par défaut
            
        Returns:
            tuple: (success, message)
        """
        # Import the necessary constants
        from ldap3 import MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
        
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
                password = self.generate_password_from_cn(user_cn)
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
        """
        Supprime un utilisateur du répertoire.
        
        Args:
            user_dn (str): DN de l'utilisateur à supprimer
            
        Returns:
            tuple: (success, message)
        """
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
    
    # Ces méthodes doivent être ajoutées à la classe LDAPModel dans flask_app/models/ldap.py

    def search_active_users(self, search_term, search_type):
        """
        Recherche d'utilisateurs actifs dans le répertoire LDAP en fonction du terme et du type de recherche.
        
        Args:
            search_term (str): Le terme à rechercher
            search_type (str): Le type de recherche (cn, fullName, mail, workforceID)
            
        Returns:
            list: Liste des utilisateurs correspondants avec informations de base
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Construction du filtre de recherche en fonction du type
            if search_type == 'cn':
                search_filter = f'(cn={search_term})'
            elif search_type == 'fullName':
                search_filter = f'(fullName=*{search_term}*)'
            elif search_type == 'mail':
                search_filter = f'(mail=*{search_term}*)'
            elif search_type == 'workforceID':
                search_filter = f'(workforceID={search_term})'
            else:
                # Type de recherche non valide
                conn.unbind()
                return []
            
            # Recherche dans le container des utilisateurs actifs
            search_base = self.actif_users_dn
            conn.search(search_base, 
                    search_filter, 
                    search_scope='SUBTREE',
                    attributes=['cn', 'fullName', 'mail', 'ou', 'title'])
            
            # Formater les résultats
            users = []
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
            
        except Exception as e:
            print(f"Erreur lors de la recherche d'utilisateurs actifs: {str(e)}")
            return []

    def search_user_by_dn(self, user_dn):
        """
        Recherche un utilisateur par son DN et retourne ses informations détaillées.
        Similaire à search_user mais accepte un DN directement.
        
        Args:
            user_dn (str): DN de l'utilisateur à rechercher
            
        Returns:
            dict: Informations de l'utilisateur ou None si non trouvé
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Vérifier si l'utilisateur existe
            conn.search(user_dn, 
                    '(objectClass=*)', 
                    search_scope='BASE',
                    attributes=['cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 
                                'fullName', 'mail', 'workforceID', 'groupMembership', 
                                'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 
                                'nrfMemberOf', 'loginDisabled', 'loginTime', 'passwordExpirationTime'])
            
            if not conn.entries:
                conn.unbind()
                return None
            
            # Extraire les attributs
            user_attributes = conn.entries[0]
            result = {
                'dn': user_dn,
                'CN': user_attributes.cn.value,
                'favvEmployeeType': user_attributes.favvEmployeeType.value if hasattr(user_attributes, 'favvEmployeeType') else '',
                'fullName': user_attributes.fullName.value if hasattr(user_attributes, 'fullName') else '',
                'mail': user_attributes.mail.value if hasattr(user_attributes, 'mail') else '',
                'sn': user_attributes.sn.value if hasattr(user_attributes, 'sn') else '',
                'givenName': user_attributes.givenName.value if hasattr(user_attributes, 'givenName') else '',
                'workforceID': user_attributes.workforceID.value if hasattr(user_attributes, 'workforceID') else '',
                'title': user_attributes.title.value if hasattr(user_attributes, 'title') else '',
                'service': user_attributes.ou.value if hasattr(user_attributes, 'ou') else '',
                'FavvNatNr': user_attributes.FavvNatNr.value if hasattr(user_attributes, 'FavvNatNr') else '',
                'groupMembership': [],
                'DirXMLAssociations': user_attributes['DirXML-Associations'].values if hasattr(user_attributes, 'DirXML-Associations') else [],
                'FavvHierarMgrDN': user_attributes['FavvHierarMgrDN'].value if hasattr(user_attributes, 'FavvHierarMgrDN') else None,
                'nrfMemberOf': [],
                'loginDisabled': 'YES' if hasattr(user_attributes, 'loginDisabled') and user_attributes.loginDisabled.value else 'NO',
                'loginTime': user_attributes.loginTime.value if hasattr(user_attributes, 'loginTime') else '',
                'passwordExpirationTime': user_attributes.passwordExpirationTime.value if hasattr(user_attributes, 'passwordExpirationTime') else ''
            }
            
            # Rechercher le nom du manager
            if result['FavvHierarMgrDN']:
                try:
                    conn.search(result['FavvHierarMgrDN'], '(objectClass=*)', attributes=['fullName'])
                    if conn.entries:
                        result['ChefHierarchique'] = conn.entries[0].fullName.value
                    else:
                        result['ChefHierarchique'] = 'Manager not found'
                except Exception as e:
                    result['ChefHierarchique'] = f'Error fetching manager: {str(e)}'
            else:
                result['ChefHierarchique'] = 'No manager specified'
            
            # Récupérer les adhésions aux groupes
            if hasattr(user_attributes, 'groupMembership') and user_attributes.groupMembership:
                for group_dn in user_attributes.groupMembership.values:
                    conn.search(group_dn, '(objectClass=groupOfNames)', attributes=['cn'])
                    if conn.entries:
                        group_cn = conn.entries[0].cn.value
                        result['groupMembership'].append({
                            'dn': group_dn,
                            'cn': group_cn,
                        })
            
            # Récupérer les adhésions aux rôles
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
            
            conn.unbind()
            return result
            
        except Exception as e:
            print(f"Erreur lors de la recherche de l'utilisateur par DN: {str(e)}")
            return None

    def update_user(self, user_dn, attributes, groups_to_add=None, groups_to_remove=None, reset_password=False, expire_password=False, target_container=None, change_reason=None):
        """
        Met à jour les attributs d'un utilisateur, ses groupes, et peut déplacer l'utilisateur vers un autre container.
        
        Args:
            user_dn (str): DN de l'utilisateur à mettre à jour
            attributes (dict): Dictionnaire des attributs à mettre à jour
            groups_to_add (list): Liste des groupes à ajouter (dicts avec 'name' et 'dn')
            groups_to_remove (list): Liste des groupes à supprimer (dicts avec 'name' et 'dn')
            reset_password (bool): Si True, réinitialise le mot de passe de l'utilisateur
            expire_password (bool): Si True, expire le mot de passe pour forcer le changement
            target_container (str): Si spécifié, déplace l'utilisateur vers ce container
            change_reason (str): Raison des changements (pour journalisation)
            
        Returns:
            tuple: (success, message)
        """
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
                password = self.generate_password_from_cn(user_cn)
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

    def remove_user_from_group(self, user_dn, group_dn):
        """
        Supprime un utilisateur d'un groupe.
        
        Args:
            user_dn (str): DN de l'utilisateur à supprimer
            group_dn (str): DN du groupe duquel supprimer l'utilisateur
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Établir une connexion au serveur LDAP
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
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
            conn.search(group_dn, '(objectClass=nrfRole)', search_scope='BASE')
            if conn.entries:
                conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_DELETE, [user_dn])]}
                )
            
            # Fermer la connexion
            conn.unbind()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de l'utilisateur du groupe: {str(e)}")
            return False

    def get_dashboard_stats(self):
        """
        Récupère toutes les statistiques nécessaires pour le tableau de bord
        
        Returns:
            dict: Dictionnaire contenant toutes les statistiques
        """
        return {
            'total_users': self.get_total_users_count(),
            # 'total_groups': self.get_total_groups_count(),
            # 'total_roles': self.get_total_roles_count(),
            # 'services_count': self.get_services_count(),
            'recent_logins': self.get_recent_logins_count(),
            'disabled_accounts': self.get_disabled_accounts_count()
        }