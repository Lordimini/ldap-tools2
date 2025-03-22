# flask_app/models/ldap/template.py
from .base import LDAPBase
from ldap3 import Connection, SUBTREE

class LDAPTemplate(LDAPBase):
    def get_template_details(self, template_cn):
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