# flask_app/models/ldap/users/__init__.py
from .user_crud import LDAPUserCRUD
from .user_utils import LDAPUserUtils


class LDAPUserMixin(LDAPUserCRUD, LDAPUserUtils):
    
    def __init__(self, config):
        super().__init__(config)
    
    UserCRUD = LDAPUserCRUD
    UserUtils = LDAPUserUtils