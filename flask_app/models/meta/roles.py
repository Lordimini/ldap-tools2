# flask_app/models/ldap/roles.py
from .base import METABase
from flask import flash, render_template
from ldap3 import Connection

class METARoleMixin(METABase):
    def get_role_users(self, role_cn):
        """
        Obtient les utilisateurs associés à un rôle, avec validation des DNs.
        """
        try:
            conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Search for the role in the entire subtree of o=FAVV and o=COPY
            role_dn = None
            
            # Vérifier que role_base_dn est une liste
            base_dns = self.role_base_dn if isinstance(self.role_base_dn, list) else [self.role_base_dn]
            
            # Parcourir tous les base_dn valides
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré dans get_role_users: {base_dn}")
                    continue
                    
                try:
                    print(f"Recherche du rôle '{role_cn}' dans {base_dn}")
                    conn.search(base_dn, f'(cn={role_cn})', search_scope='SUBTREE', attributes=['equivalentToMe'])
                    
                    if conn.entries:
                        role_dn = conn.entries[0].entry_dn
                        print(f"Rôle trouvé: {role_dn}")
                        break
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    continue
                    
            if role_dn:
                print(f"Recherche des utilisateurs pour le rôle: {role_dn}")

                # Fetch the role's equivalentToMe attribute (list of user DNs)
                conn.search(role_dn, '(objectClass=nrfRole)', attributes=['equivalentToMe'])
                if conn.entries and hasattr(conn.entries[0], 'equivalentToMe') and conn.entries[0].equivalentToMe:
                    user_dns = conn.entries[0].equivalentToMe.values
                    users = []

                    # Fetch details for each user
                    for user_dn in user_dns:
                        try:
                            conn.search(user_dn, '(objectClass=*)', attributes=['cn', 'fullName', 'title', 'ou'])
                            if conn.entries:
                                user = conn.entries[0]
                                
                                users.append({
                                    'CN': user.cn.value if hasattr(user, 'cn') and user.cn else 'Unknown',
                                    'fullName': user.fullName.value if hasattr(user, 'fullName') and user.fullName else 'Unknown',
                                    'ou': user.ou.value if hasattr(user, 'ou') and user.ou else 'N/A',
                                    'title': user.title.value if hasattr(user, 'title') and user.title else 'N/A'
                                })
                            else:
                                print(f"Utilisateur non trouvé pour DN: {user_dn}")
                        except Exception as e:
                            print(f"Erreur lors de la récupération des détails de l'utilisateur {user_dn}: {str(e)}")
                            continue

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
                    print('Le rôle n\'a pas d\'utilisateurs équivalents.')
            else:
                result = None
                print(f"Rôle non trouvé: {role_cn}")

            # Unbind the connection
            conn.unbind()
            return result
                
        except Exception as e:
            import traceback
            print(f"Erreur dans get_role_users: {str(e)}")
            print(traceback.format_exc())
            conn.unbind() if 'conn' in locals() and conn else None
            return None
        
    def get_role_groups(self, role_cn):
        if role_cn:
            try:
                # Connect to the LDAP server
                conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
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
        
    def view_role(self, dn):
        conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
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
        
    def get_ldap_children(self, current_dn):
        conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True) 
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

    
    # ... autres méthodes liées aux rôles