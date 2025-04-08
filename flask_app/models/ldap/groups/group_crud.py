# flask_app/models/ldap/users/user_crud.py
from ldap3 import MODIFY_REPLACE, MODIFY_DELETE, MODIFY_ADD
# from flask import flash, redirect, url_for
from ..base import LDAPBase
from .group_utils import LDAPGroupUtils


class LDAPGroupCRUD(LDAPBase):
    
    def create_group (self,group_name, target_dn):
        pass
    
    def read_group (self, group_name):
        pass
    
    def delete_group (self, group_name, target_dn):
        pass
    
    def update_group (self, group_name, options):
        pass
    