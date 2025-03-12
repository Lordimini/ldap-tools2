import csv, time
from ldap3 import Server, Connection, ALL, MODIFY_ADD, SUBTREE
from flask_app.models.meta_model import METAModel

def validate_entries(csv_file_path, group_dn_structure):
    valid_entries = []
    invalid_entries = []

    # Connect to the eDirectory server
    ldap_model = METAModel()
    #ldap_model.authenticate(self.bind_dn, self.password)
    conn = ldap_model.authenticate_admin(ldap_model.bind_dn, ldap_model.password) 

    # Read the CSV file with user CNs and group names
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        
        # Iterate over each row in the CSV
        for row in reader:
            user_cn = row['cn']
            group_name = row['group_name']

            # Construct the DNs for the user and group
            user_dn = f'cn={user_cn},ou=users,ou=sync,o=COPY'  # Adjust to your directory structure
            group_dn = f'cn={group_name},{group_dn_structure}'  # Adjust to your directory structure

            # Check if the user and group exist in LDAP
            user_exists = conn.search(user_dn, '(objectClass=*)', search_scope='BASE')
            print(f"Le user exist: {user_exists}")
            group_exists = conn.search(group_dn, '(objectClass=*)', search_scope='BASE')

            if user_exists and group_exists:
                valid_entries.append({'user_cn': user_cn, 'group_name': group_name})
            else:
                invalid_entries.append({'user_cn': user_cn, 'group_name': group_name, 
                                       'error': 'User or group does not exist'})

    # Unbind the connection
    conn.unbind()

    return valid_entries, invalid_entries

def apply_changes(valid_entries, group_dn_structure):
    success_count = 0
    failure_count = 0
    failures = []

   # Connect to the eDirectory server
    ldap_model = METAModel()
    #ldap_model.authenticate(self.bind_dn, self.password)
    conn = ldap_model.authenticate_admin(ldap_model.bind_dn, ldap_model.password) 

    # Iterate over valid entries and apply changes
    for entry in valid_entries:
        user_cn = entry['user_cn']
        group_name = entry['group_name']

        # Construct the DNs for the user and group
        user_dn = f'cn={user_cn},ou=users,ou=sync,o=COPY'
        group_dn = f'cn={group_name},{group_dn_structure}'

        # Add user to the group (modify the group's member attribute)
        group_modify = conn.modify(
            group_dn, 
            {'member': [(MODIFY_ADD, [user_dn])]})
        
        # Update the user's memberOf attribute (to reflect the new group membership)
        user_modify = conn.modify(
            user_dn, 
            {'groupMembership': [(MODIFY_ADD, [group_dn])]})

        # Check if the operations were successful
        if group_modify and user_modify:
            success_count += 1
        else:
            failure_count += 1
            failures.append(f"Failed to add {user_cn} to {group_name}. Error: {conn.result['description']}")

        # Wait for 2 seconds before processing the next user
        time.sleep(2)

    # Unbind the connection
    conn.unbind()

    return success_count, failure_count, failures