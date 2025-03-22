# Guide d'implémentation: Ajout de nouveaux rôles dans LDAP Manager

Ce document explique comment ajouter de nouveaux rôles personnalisés au système LDAP Manager et leur attribuer des autorisations spécifiques pour gérer certains types d'utilisateurs.

## Table des matières

1. [Introduction](#introduction)
2. [Vue d'ensemble du système de rôles](#vue-densemble-du-système-de-rôles)
3. [Étapes pour l'ajout d'un nouveau rôle](#étapes-pour-lajout-dun-nouveau-rôle)
   - [Étape 1: Configuration LDAP](#étape-1-configuration-ldap)
   - [Étape 2: Mise à jour des fichiers de configuration](#étape-2-mise-à-jour-des-fichiers-de-configuration)
   - [Étape 3: Mise à jour du modèle User](#étape-3-mise-à-jour-du-modèle-user)
   - [Étape 4: Mise à jour de l'authentification](#étape-4-mise-à-jour-de-lauthentification)
   - [Étape 5: Configuration des permissions par rôle](#étape-5-configuration-des-permissions-par-rôle)
4. [Test et validation](#test-et-validation)
5. [Personnalisation du template post-creation](#personnalisation-du-template-post-creation)
6. [Dépannage](#dépannage)
7. [Annexes](#annexes)

## Introduction

Dans LDAP Manager, les rôles déterminent quels types d'utilisateurs peuvent être gérés par un administrateur. Par exemple, un administrateur OCI ne devrait voir et gérer que les utilisateurs de type OCI. Ce document explique comment ajouter un nouveau rôle, tel que "OCI-admin" ou "STAG-admin", et comment configurer les autorisations associées.

## Vue d'ensemble du système de rôles

Le système LDAP Manager utilise un mécanisme de rôles basé sur l'appartenance à des groupes LDAP:

1. **Détection des rôles**: Lors de l'authentification, l'application vérifie l'appartenance de l'utilisateur à des groupes LDAP spécifiques.
2. **Attribution des permissions**: En fonction des rôles détectés, l'application attribue des permissions à l'utilisateur.
3. **Filtrage des utilisateurs**: Les utilisateurs en attente de finalisation sont filtrés en fonction des permissions associées au rôle.
4. **Personnalisation de l'interface**: L'interface utilisateur est adaptée en fonction des rôles (par exemple, n'afficher que certains types d'utilisateurs dans la liste déroulante).

## Étapes pour l'ajout d'un nouveau rôle

### Étape 1: Configuration LDAP

Créez d'abord un groupe LDAP pour le nouveau rôle:

1. Connectez-vous à votre serveur LDAP avec les outils d'administration appropriés.
2. Créez un nouveau groupe avec un nom correspondant au rôle (par exemple, "OCI-Admin"):
   ```
   dn: cn=OCI-Admin,ou=GROUPS,ou=SYNC,o=COPY
   objectClass: groupOfNames
   cn: OCI-Admin
   description: Administrators for OCI user types
   ```
3. Ajoutez les utilisateurs appropriés comme membres de ce groupe.

### Étape 2: Mise à jour des fichiers de configuration

Ajoutez le nouveau groupe à vos fichiers de configuration LDAP:

1. Ouvrez les fichiers de configuration (`flask_app/config/meta_config.py` et équivalents):

```python
# flask_app/config/meta_config.py
meta_login_config = {
    # Configurations existantes...
    "admin_group_dn": "cn=LDAP-Admin,ou=GROUPS,ou=SYNC,o=COPY",
    "reader_group_dn": "cn=LDAP-Reader,ou=GROUPS,ou=SYNC,o=COPY",
    # Ajoutez votre nouveau groupe ici:
    "oci_admin_group_dn": "cn=OCI-Admin,ou=GROUPS,ou=SYNC,o=COPY",
}
```

2. Si vous avez d'autres sources LDAP (comme `idme_config.py`), mettez-les également à jour.

### Étape 3: Mise à jour du modèle User

Modifiez la classe LDAPBase pour inclure les nouveaux attributs de groupe:

1. Ouvrez `flask_app/models/ldap/base.py`:

```python
class LDAPBase:
    def __init__(self, config):
        # Attributs existants...
        self.admin_group_dn = config['admin_group_dn']
        self.reader_group_dn = config['reader_group_dn']
        # Ajoutez le nouveau groupe (avec valeur par défaut pour compatibilité)
        self.oci_admin_group_dn = config.get('oci_admin_group_dn', '')
```

2. Ensuite, mettez à jour la méthode `from_ldap_data` dans `flask_app/models/user_model.py`:

```python
@classmethod
def from_ldap_data(cls, username, user_data, ldap_source='meta'):
    # Extraire les appartenances aux groupes
    groups = []
    if 'groupMembership' in user_data and user_data['groupMembership']:
        groups = [group['cn'] for group in user_data['groupMembership']]
    
    # Extraire les rôles basés sur l'appartenance aux groupes
    roles = []
    
    # Vérifier le rôle admin
    if 'admin_group_dn' in user_data and user_data.get('is_admin_member', False):
        roles.append('admin')
    
    # Vérifier le rôle reader
    if 'reader_group_dn' in user_data and user_data.get('is_reader_member', False):
        roles.append('reader')
    
    # Vérifier le nouveau rôle (par exemple, OCI-admin)
    if 'oci_admin_group_dn' in user_data and user_data.get('is_oci_admin_member', False):
        roles.append('OCI-admin')
    
    # Définir les permissions basées sur les rôles
    permissions = set()
    
    if 'admin' in roles:
        permissions.update([
            'view_users', 'create_users', 'edit_users', 'delete_users',
            # Autres permissions existantes...
        ])
    elif 'reader' in roles:
        permissions.update([
            'view_users', 'view_groups', 'view_roles', 'view_services'
        ])
    # Ajouter les permissions pour le nouveau rôle
    elif 'OCI-admin' in roles:
        permissions.update([
            'view_oci', 'edit_oci'
        ])
    
    return cls(
        username=username,
        dn=user_data.get('dn', ''),
        display_name=user_data.get('fullName', username),
        email=user_data.get('mail', None),
        ldap_source=ldap_source,
        roles=roles,
        permissions=permissions,
        groups=groups
    )
```

### Étape 4: Mise à jour de l'authentification

Modifiez la fonction d'authentification pour détecter l'appartenance au nouveau groupe:

1. Ouvrez `flask_app/services/login_manager.py` et mettez à jour `authenticate_user`:

```python
def authenticate_user(username, password, ldap_source='meta'):
    try:
        # Créer le modèle LDAP pour la source spécifiée
        ldap_model = LDAPModel(source=ldap_source)
        
        # Authentifier contre LDAP
        conn = ldap_model.authenticate(username, password)
        if not conn:
            return None
        
        # Vérifier l'appartenance aux groupes
        is_admin_member = False
        is_reader_member = False
        is_oci_admin_member = False  # Nouvelle variable
        
        admin_group_dn = ldap_model.admin_group_dn
        reader_group_dn = ldap_model.reader_group_dn
        oci_admin_group_dn = ldap_model.oci_admin_group_dn  # Nouveau groupe
        
        # Vérifier l'appartenance au groupe admin
        if admin_group_dn:
            conn.search(admin_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_admin_member = True
        
        # Vérifier l'appartenance au groupe reader
        if reader_group_dn:
            conn.search(reader_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_reader_member = True
        
        # Vérifier l'appartenance au nouveau groupe
        if oci_admin_group_dn:
            conn.search(oci_admin_group_dn, f'(member={conn.user})', search_scope='BASE')
            if conn.entries:
                is_oci_admin_member = True
        
        # Obtenir les détails de l'utilisateur
        user_data = ldap_model.search_user_final(username, 'cn')
        if not user_data:
            return None
            
        # Ajouter les informations d'appartenance aux groupes
        user_data['is_admin_member'] = is_admin_member
        user_data['is_reader_member'] = is_reader_member
        user_data['is_oci_admin_member'] = is_oci_admin_member  # Nouveau flag
        user_data['admin_group_dn'] = admin_group_dn
        user_data['reader_group_dn'] = reader_group_dn
        user_data['oci_admin_group_dn'] = oci_admin_group_dn  # Nouveau DN
        
        # Stocker les données dans la session
        session['user_data'] = user_data
        session['ldap_source'] = ldap_source
        
        # Créer et retourner l'utilisateur
        user = User.from_ldap_data(username, user_data, ldap_source)
        return user
    
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None
```

### Étape 5: Configuration des permissions par rôle

Créez ou mettez à jour le fichier de configuration JSON pour les types d'utilisateurs par rôle:

1. Créez un fichier `flask_app/config/role_user_types.json`:

```json
{
  "role_permissions": {
    "admin": {
      "user_types": ["*"],
      "permissions": ["view_all", "edit_all", "delete_all"]
    },
    "reader": {
      "user_types": ["*"],
      "permissions": ["view_all"]
    },
    "OCI-admin": {
      "user_types": ["OCI", "BOODOCI"],
      "permissions": ["view_oci", "edit_oci"]
    }
  }
}
```

2. Créez un service pour gérer ces configurations:

Créez un fichier `flask_app/services/role_config_service.py`:

```python
import json
import os

class RoleConfigService:
    def __init__(self, app=None):
        self.app = app
        self.config = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        self._load_role_config()
        
        # Enregistrer avec le contexte d'application
        app.role_config = self
    
    def _load_role_config(self):
        """Charger la configuration des rôles depuis le fichier JSON"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'config', 
            'role_user_types.json'
        )
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
    
    def get_allowed_user_types(self, roles):
        """Obtenir les types d'utilisateurs autorisés pour les rôles donnés"""
        allowed_types = set()
        
        # Par défaut retourner une liste vide si roles est None
        if not roles:
            return []
            
        for role in roles:
            role_config = self.config.get('role_permissions', {}).get(role, {})
            types = role_config.get('user_types', [])
            
            # Si '*' est dans types, l'utilisateur peut accéder à tous les types
            if '*' in types:
                return ['*']
                
            # Sinon ajouter les types spécifiques
            allowed_types.update(types)
            
        return list(allowed_types)
    
    def can_manage_user_type(self, roles, user_type):
        """Vérifier si un utilisateur avec les rôles donnés peut gérer un type d'utilisateur spécifique"""
        allowed_types = self.get_allowed_user_types(roles)
        
        # Si '*' est dans allowed_types, l'utilisateur peut gérer tous les types
        if '*' in allowed_types:
            return True
            
        return user_type in allowed_types
```

3. Initialisez ce service dans la factory d'application:

Modifiez `flask_app/__init__.py`:

```python
def create_app():
    app = Flask(__name__, static_folder='static')
    app.secret_key = 'eyqscmnc'  # À remplacer par une clé sécurisée en production
    
    # Initialiser LDAP config manager
    ldap_config_manager.init_app(app)
    app.ldap_config_manager = ldap_config_manager
    
    # Initialiser role config service
    from flask_app.services.role_config_service import RoleConfigService
    role_config = RoleConfigService()
    role_config.init_app(app)
    
    # Initialiser login manager
    init_login_manager(app)
    
    # Enregistrer les blueprints...
    
    return app
```

## Test et validation

Pour tester le nouveau rôle:

1. Assurez-vous que le groupe LDAP est correctement créé et qu'au moins un utilisateur en est membre.
2. Redémarrez l'application Flask.
3. Connectez-vous avec un utilisateur membre du nouveau groupe.
4. Vérifiez que le badge de rôle s'affiche correctement dans l'interface.
5. Accédez à la page de post-création et vérifiez que seuls les types d'utilisateurs autorisés sont visibles.

## Personnalisation du template post-creation

Pour que la page post-creation ne montre que les utilisateurs du type approprié:

1. Modifiez `flask_app/routes/postcreation.py`:

```python
@postcreation_bp.route('/post_creation', methods=['GET', 'POST'])
@login_required
def post_creation():
    # Obtenir la source LDAP
    ldap_source = request.args.get('source', session.get('ldap_source', 'meta'))
    session['ldap_source'] = ldap_source
    
    # Créer le modèle LDAP
    ldap_model = LDAPModel(source=ldap_source)
    
    # Obtenir tous les utilisateurs en attente
    all_pending_users = ldap_model.get_pending_users()
    
    # Obtenir le service de configuration des rôles
    role_config = current_app.role_config
    
    # Obtenir les types d'utilisateurs autorisés pour les rôles de l'utilisateur courant
    allowed_types = role_config.get_allowed_user_types(current_user.roles)
    
    # Filtrer les utilisateurs en fonction des types autorisés
    if '*' in allowed_types:
        # L'administrateur peut voir tous les utilisateurs
        pending_users = all_pending_users
    else:
        # Filtrer les utilisateurs par type
        pending_users = []
        for user in all_pending_users:
            # Vous devrez peut-être modifier get_pending_users pour inclure le type d'utilisateur
            # ou récupérer les détails de l'utilisateur ici
            user_details = ldap_model.search_user_final(user['dn'])
            if user_details and 'title' in user_details:
                user_type = user_details['title']
                if user_type in allowed_types:
                    pending_users.append(user)
    
    # Reste de la logique existante...
```

2. Vous pouvez également personnaliser le template post-creation.html pour afficher des éléments spécifiques au rôle:

```html
{% if 'OCI-admin' in current_user.roles %}
    <div class="alert alert-info">
        Vous êtes un administrateur OCI et ne pouvez voir que les utilisateurs de type OCI.
    </div>
{% endif %}
```

## Dépannage

Si vous rencontrez des problèmes:

1. **Le rôle n'apparaît pas**: Vérifiez l'appartenance au groupe LDAP et assurez-vous que les DNs sont corrects.
2. **Les permissions ne sont pas appliquées**: Vérifiez la méthode `from_ldap_data` pour vous assurer que les permissions sont correctement attribuées.
3. **Le filtrage des utilisateurs ne fonctionne pas**: Vérifiez que le type d'utilisateur est correctement extrait et comparé aux types autorisés.
4. **Erreurs dans le template**: Utilisez l'inspection du navigateur et les logs Flask pour identifier les erreurs.

## Annexes

### Exemple complet pour un nouveau rôle "STAG-admin"

Voici un exemple complet pour ajouter un rôle "STAG-admin" qui ne peut gérer que les stagiaires:

1. **Groupe LDAP**:
   ```
   dn: cn=STAG-Admin,ou=GROUPS,ou=SYNC,o=COPY
   objectClass: groupOfNames
   cn: STAG-Admin
   description: Administrators for trainee user types
   ```

2. **Configuration LDAP**:
   ```python
   meta_login_config = {
       # Configurations existantes...
       "stag_admin_group_dn": "cn=STAG-Admin,ou=GROUPS,ou=SYNC,o=COPY",
   }
   ```

3. **Détection du rôle**:
   ```python
   # Dans authenticate_user
   is_stag_admin_member = False
   stag_admin_group_dn = ldap_model.stag_admin_group_dn
   
   if stag_admin_group_dn:
       conn.search(stag_admin_group_dn, f'(member={conn.user})', search_scope='BASE')
       if conn.entries:
           is_stag_admin_member = True
   
   # Ajouter aux données utilisateur
   user_data['is_stag_admin_member'] = is_stag_admin_member
   user_data['stag_admin_group_dn'] = stag_admin_group_dn
   ```

4. **Attribution du rôle**:
   ```python
   # Dans from_ldap_data
   if 'stag_admin_group_dn' in user_data and user_data.get('is_stag_admin_member', False):
       roles.append('STAG-admin')
   ```

5. **Permissions**:
   ```python
   # Dans from_ldap_data
   elif 'STAG-admin' in roles:
       permissions.update([
           'view_stag', 'edit_stag'
       ])
   ```

6. **Configuration JSON**:
   ```json
   "STAG-admin": {
     "user_types": ["STAG", "EMP - STAG"],
     "permissions": ["view_stag", "edit_stag"]
   }
   ```

---

Cette documentation devrait vous permettre d'ajouter facilement de nouveaux rôles à votre application LDAP Manager. En suivant ces étapes, vous pourrez créer un système très flexible où différents administrateurs peuvent gérer différents types d'utilisateurs de manière isolée.