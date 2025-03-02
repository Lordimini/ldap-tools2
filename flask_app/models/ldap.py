from ldap3 import Server, Connection, ALL, MODIFY_ADD, SUBTREE
from flask_app.config.ldap_config import ldap_login_config
#from flask_app.models.ldap import LDAPModel
from flask import Blueprint, redirect, url_for, flash, json, render_template
import unicodedata

class LDAPModel:
    def __init__(self):
        self.ldap_server = ldap_login_config['ldap_server']
        self.bind_dn = ldap_login_config['bind_dn']
        self.password = ldap_login_config['bind_password']
        self.base_dn = ldap_login_config['base_dn']
        self.template_dn = ldap_login_config['template_dn']
        self.usercreation_dn = ldap_login_config['usercreation_dn']
        self.admin_group_dn = ldap_login_config['admin_group_dn']
        self.reader_group_dn = ldap_login_config['reader_group_dn']
        
    def authenticate(self, username, password):
        user_dn = f'cn={username},ou=users,ou=sync,o=COPY'
        try:
            server = Server(self.ldap_server, get_info=ALL)
            conn = Connection(server, user=user_dn, password=password, auto_bind=True)
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
            
            #ldap_model = LDAPModel()
            #conn = ldap_model.authenticate(self.bind_dn, self.password)
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True) 
            #print(f"password: {session_password}")
        # Construct the search filter based on the search type
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
           
            for base_dn in ['ou=users,ou=sync,o=COPY']:
                conn.search(base_dn, search_filter, search_scope='SUBTREE', attributes=['cn', 'favvEmployeeType', 'sn', 'givenName', 'FavvNatNr', 'fullName', 'mail', 'workforceID', 'groupMembership', 'DirXML-Associations', 'ou', 'title', 'FavvHierarMgrDN', 'nrfMemberOf', 'loginDisabled', 'loginTime', 'passwordExpirationTime'])

                if conn.entries:
                    user_dn = conn.entries[0].entry_dn
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
                    'passwordExpirationTime': user_attributes.passwordExpirationTime.value
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
            for base_dn in ['ou=Groups,ou=IAM-Security,o=COPY', 'o=FAVV', 'ou=GROUPS,ou=SYNC,o=COPY']:
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
            for base_dn in ['cn=RoleDefs,cn=RoleConfig,cn=AppConfig,cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY']:
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
                role_base_dn = 'cn=RoleDefs,cn=RoleConfig,cn=AppConfig,cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY'
                conn.search(role_base_dn, f'(cn={role_cn})', search_scope='SUBTREE', attributes=['entryDN'])

                if not conn.entries:
                    print(f'Role "{role_cn}" not found.', 'danger')
                    return render_template('role_groups.html', result=None, prefill_role_cn=role_cn)

                role_dn = conn.entries[0].entry_dn
                print(f"Role DN: {role_dn}")

                # Step 2: Search for nrfResourceAssociation objects in the ResourceAssociations container
                resource_base_dn = 'cn=ResourceAssociations,cn=RoleConfig,cn=AppConfig,cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY'
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
            for base_dn in ['ou=users,ou=sync,o=COPY']:
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
            for base_dn in ['o=FAVV', 'o=COPY']:
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
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, 
                              password=self.password, auto_bind=True)
            
            fullName = []
            for base_dn in ['o=FAVV', 'o=COPY']:
                conn.search(base_dn, f'(fullName=*{search_term}*)', 
                           search_scope='SUBTREE', attributes=['fullName', 'mail', 'ou'])
                
                for entry in conn.entries:
                    if ('cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY' 
                        not in entry.entry_dn):
                        fullName.append({
                            'label': f"{entry.fullName.value} - {entry.mail.value} - ({entry.ou.value}) - ({entry.entry_dn})",
                            'value': entry.fullName.value
                        })
            
            conn.unbind()
            return fullName
            
        except Exception as e:
            raise e
        
    
    def autocomplete_role(self, search_term):
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, 
                              password=self.password, auto_bind=True)
            
            roles = []
            for base_dn in ['cn=RoleDefs,cn=RoleConfig,cn=AppConfig,cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY']:
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
            for base_dn in ['o=FAVV', 'o=COPY']:
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
        if current_dn == 'cn=RoleDefs,cn=RoleConfig,cn=AppConfig,cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY':
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
                search_base="ou=users,ou=sync,o=copy",
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
    
    def create_user(self, cn, ldap_attributes):
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
                return True, password
            else:
                print(f"Failed to create user: {conn.result}", 'error')
                return False, None

        except Exception as e:
            print(f"An error occurred: {str(e)}", 'error')
            return False, None
    
    
        
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
            search_base = "ou=users,ou=sync,o=COPY"
            
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
        Get details of a specific template by its CN
    
        Parameters:
        template_cn (str): The CN of the template to retrieve
    
        Returns:
        dict: Template attributes or None if not found
        """
        try:
            conn = Connection(self.ldap_server, user=self.bind_dn, password=self.password, auto_bind=True)
    
            search_base = "ou=tpl,ou=sync,o=copy"  # Base DN for templates
            search_filter = f'(cn={template_cn})'
    
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['cn', 'description', 'title', 'objectClass', 'ou', 
                            'FavvExtDienstMgrDn', 'FavvEmployeeType', 'FavvEmployeeSubType']
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
                    'FavvEmployeeSubType': entry.FavvEmployeeSubType.value if hasattr(entry, 'FavvEmployeeSubType') and entry.FavvEmployeeSubType else None
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
            search_base = "ou=users,ou=sync,o=COPY"
        
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
            search_base = "ou=users,ou=sync,o=COPY"
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
            search_base = "ou=users,ou=sync,o=COPY"
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