# flask_app/models/ldap/users.py
# Ce fichier est maintenu pour la compatibilité avec le code existant
# Il importe et expose simplement la classe LDAPUserMixin du package users

from flask_app.models.ldap.users import LDAPUserMixin

# La classe LDAPUserMixin est maintenant définie dans users/__init__.py
# Mais elle est importée ici pour maintenir la compatibilité avec le code existant

# Pour les nouvelles implémentations, il est recommandé d'utiliser directement les classes:
# - from flask_app.models.ldap.users import LDAPUserMixin
# - from flask_app.models.ldap.users import LDAPUserCRUD
# - from flask_app.models.ldap.users import LDAPUserUtils