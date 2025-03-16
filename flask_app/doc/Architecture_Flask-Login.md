# Architecture Flask-Login dans LDAP Manager

## Table des matières

1. [Introduction](#introduction)
2. [Vue d'ensemble de l'architecture](#vue-d'ensemble-de-l'architecture)
3. [Configuration initiale](#configuration-initiale)
4. [Modèle d'utilisateur](#modèle-d'utilisateur)
5. [Processus d'authentification](#processus-d'authentification)
6. [Sessions et gestion des utilisateurs](#sessions-et-gestion-des-utilisateurs)
7. [Contrôle d'accès basé sur les rôles](#contrôle-d'accès-basé-sur-les-rôles)
8. [Intégration avec le système de menus dynamiques](#intégration-avec-le-système-de-menus-dynamiques)
9. [Flux de données complet](#flux-de-données-complet)
10. [Personnalisation et extension](#personnalisation-et-extension)
11. [Bonnes pratiques](#bonnes-pratiques)
12. [Troubleshooting](#troubleshooting)

## Introduction

Cette documentation explique en détail l'implémentation de Flask-Login dans l'application LDAP Manager. Flask-Login est une bibliothèque qui facilite la gestion des sessions utilisateur dans Flask, permettant l'authentification, la connexion persistante et le contrôle d'accès basé sur les rôles.

Dans le contexte de LDAP Manager, Flask-Login est utilisé en conjonction avec l'authentification LDAP pour fournir un système d'authentification robuste qui s'intègre avec les groupes et rôles LDAP, tout en offrant une gestion de session côté serveur.

## Vue d'ensemble de l'architecture

L'architecture d'authentification de LDAP Manager utilise les composants suivants :

1. **Flask-Login** : Gère les sessions utilisateur et l'état d'authentification
2. **LDAPConfigManager** : Gère les connexions aux différentes sources LDAP configurées
3. **EDIRModel** : Interagit directement avec les serveurs LDAP via ldap3
4. **User Model** : Implémente UserMixin de Flask-Login et ajoute des fonctionnalités RBAC
5. **Menu Configuration** : Système de menus dynamiques basé sur les rôles utilisateur

Le flux d'authentification suit ces étapes :
1. L'utilisateur soumet ses identifiants via le formulaire de connexion
2. Le service d'authentification vérifie les identifiants contre LDAP
3. Les données utilisateur sont récupérées, y compris l'appartenance aux groupes
4. Un objet User est créé et chargé dans la session Flask-Login
5. L'objet User est ensuite disponible dans `g.user` et `current_user` pour toutes les requêtes

## Configuration initiale

### Initialisation de Flask-Login

Flask-Login est initialisé dans `flask_app/__init__.py` par l'appel à `init_login_manager()` :

```python
def create_app():
    app = Flask(__name__, static_folder='static')
    app.secret_key = 'eyqscmnc'  # À remplacer par une clé secrète sécurisée en production
    
    # Initialize LDAP config manager
    ldap_config_manager.init_app(app)
    app.ldap_config_manager = ldap_config_manager
    
    # Initialize login manager
    init_login_manager(app)
    
    # ...
```

### Configuration du LoginManager

Le `LoginManager` est configuré dans `flask_app/services/login_manager.py` :

```python
def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # La vue à rediriger si l'utilisateur n'est pas connecté
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Set up the user loader
    @login_manager.user_loader
    def load_user(username):
        # ...
```

C'est ici que sont définis les paramètres clés :
- `login_view` : La route vers laquelle rediriger si l'authentification est requise
- `login_message` : Le message à afficher à l'utilisateur non authentifié
- `login_message_category` : La catégorie du message flash (pour le style)

## Modèle d'utilisateur

Le modèle d'utilisateur est défini dans `flask_app/models/user_model.py` et étend `UserMixin` de Flask-Login pour fournir les méthodes requises (`is_authenticated`, `is_active`, `is_anonymous`, et `get_id`).

### Classe User

```python
class User(UserMixin):
    def __init__(self, username, dn, display_name=None, email=None, ldap_source=None, 
                 roles=None, permissions=None, groups=None):
        self.id = username  # requis par Flask-Login
        self.username = username
        self.dn = dn
        self.display_name = display_name or username
        self.email = email
        self.ldap_source = ldap_source or 'meta'
        self.roles = roles or []
        self.permissions = permissions or set()
        self.groups = groups or []
        self._profile_data = {}
    
    # Méthodes pour vérifier les rôles et permissions
    def has_role(self, role):
        """Vérifie si l'utilisateur a un rôle spécifique"""
        return role in self.roles
    
    def has_permission(self, permission):
        """Vérifie si l'utilisateur a une permission spécifique"""
        return permission in self.permissions
    
    # ...
```

### Méthode from_ldap_data

La méthode de classe `from_ldap_data` est cruciale pour créer des objets User à partir des données LDAP :

```python
@classmethod
def from_ldap_data(cls, username, user_data, ldap_source='meta'):
    """
    Crée une instance User à partir des données LDAP
    """
    # Extraction des groupes
    groups = []
    if 'groupMembership' in user_data and user_data['groupMembership']:
        groups = [group['cn'] for group in user_data['groupMembership']]
    
    # Extraction des rôles basés sur l'appartenance aux groupes
    roles = []
    if 'admin_group_dn' in user_data and user_data.get('is_admin_member', False):
        roles.append('admin')
    if 'reader_group_dn' in user_data and user_data.get('is_reader_member', False):
        roles.append('reader')
    
    # Définition des permissions basées sur les rôles
    permissions = set()
    if 'admin' in roles:
        permissions.update([
            'view_users', 'create_users', 'edit_users', 'delete_users',
            'view_groups', 'edit_groups', 'create_groups', 'delete_groups',
            'view_roles', 'edit_roles', 'create_roles', 'delete_roles',
            'view_services', 'edit_services', 'upload_files', 'manage_system'
        ])
    elif 'reader' in roles:
        permissions.update([
            'view_users', 'view_groups', 'view_roles', 'view_services'
        ])
    
    # Création de l'instance User
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

Cette méthode traduit les données LDAP brutes en un modèle d'utilisateur structuré avec des rôles et des permissions.

## Processus d'authentification

### Route de login

La route de login est définie dans `flask_app/routes/auth.py` :

```python
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user_password = request.form['password']
        
        # Utilisation de la fonction d'authentification
        user = authenticate_user(username, user_password, ldap_source='meta')
        
        if user:
            # Utiliser login_user de Flask-Login
            from flask_login import login_user
            login_user(user)
            
            # Conservation de la méthode session pour compatibilité
            session['logged_in'] = True
            session['username'] = username
            session['role'] = 'admin' if user.is_admin else 'reader'
            
            # Définir la source LDAP active par défaut
            session['ldap_source'] = 'meta'
            session['ldap_name'] = meta_login_config.get('LDAP_name', 'META')
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')
```

### Fonction d'authentification

La fonction `authenticate_user` dans `flask_app/services/login_manager.py` gère l'authentification contre LDAP :

```python
def authenticate_user(username, password, ldap_source='meta'):
    """
    Authentifie un utilisateur contre LDAP et crée un objet User
    """
    try:
        # Création du modèle EDIR pour la source spécifiée
        ldap_model = EDIRModel(source=ldap_source)
        
        # Authentification contre LDAP
        conn = ldap_model.authenticate(username, password)
        if not conn:
            return None
        
        # Vérification de l'appartenance aux groupes admin ou reader
        is_admin_member = False
        is_reader_member = False
        
        admin_group_dn = ldap_model.admin_group_dn
        reader_group_dn = ldap_model.reader_group_dn
        
        # Vérification de l'appartenance au groupe admin
        conn.search(admin_group_dn, f'(member={conn.user})', search_scope='BASE')
        if conn.entries:
            is_admin_member = True
        
        # Vérification de l'appartenance au groupe reader
        conn.search(reader_group_dn, f'(member={conn.user})', search_scope='BASE')
        if conn.entries:
            is_reader_member = True
        
        # Récupération des détails utilisateur
        user_data = ldap_model.search_user_final(username, 'cn')
        if not user_data:
            return None
            
        # Ajout des informations d'appartenance aux groupes
        user_data['is_admin_member'] = is_admin_member
        user_data['is_reader_member'] = is_reader_member
        user_data['admin_group_dn'] = admin_group_dn
        user_data['reader_group_dn'] = reader_group_dn
        
        # Stockage des données utilisateur en session pour récupération ultérieure
        session['user_data'] = user_data
        session['ldap_source'] = ldap_source
        
        # Création et retour de l'utilisateur
        user = User.from_ldap_data(username, user_data, ldap_source)
        return user
    
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None
```

## Sessions et gestion des utilisateurs

### User Loader

Le user loader est enregistré auprès de Flask-Login pour charger l'utilisateur à partir de la session :

```python
@login_manager.user_loader
def load_user(username):
    """Charge l'utilisateur depuis la session"""
    if not username:
        return None
    
    # Stockage de l'utilisateur dans g pour un accès facile
    if 'user_data' in session:
        user_data = session['user_data']
        ldap_source = session.get('ldap_source', 'meta')
        user = User.from_ldap_data(username, user_data, ldap_source)
        return user
    
    return None
```

### Before Request Handler

Un handler `before_request` est configuré pour rendre l'utilisateur disponible dans `g.user` :

```python
@app.before_request
def before_request():
    g.user = current_user
    # Ajout de la source LDAP à g
    g.ldap_source = session.get('ldap_source', 'meta')
    
    # Si l'utilisateur est connecté, s'assurer que la config LDAP est définie pour l'utilisateur actuel
    if current_user.is_authenticated:
        g.user_roles = current_user.roles
        
        # Définir le nom LDAP pour l'affichage
        ldap_source = current_user.ldap_source
        g.ldap_name = app.ldap_config_manager.get_config(ldap_source).get('LDAP_name', 'LDAP')
```

### Déconnexion

La route de déconnexion utilise la fonction `logout_user()` de Flask-Login :

```python
@auth_bp.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()  # Déconnecte l'utilisateur avec Flask-Login
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
```

## Contrôle d'accès basé sur les rôles

L'application utilise trois types de décorateurs de contrôle d'accès :

### 1. Décorateur basé sur les rôles

```python
def role_required(role):
    """Décorateur pour exiger un rôle spécifique pour l'accès"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Vérification que l'utilisateur est authentifié et a le rôle requis
            if not g.user or not g.user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not g.user.has_role(role):
                flash(f'You need the "{role}" role to access this page.', 'danger')
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### 2. Décorateur basé sur les permissions

```python
def permission_required(permission):
    """Décorateur pour exiger une permission spécifique pour l'accès"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Vérification que l'utilisateur est authentifié et a la permission requise
            if not g.user or not g.user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not g.user.has_permission(permission):
                flash(f'You don\'t have permission to access this resource.', 'danger')
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### 3. Décorateur pour les administrateurs

```python
def admin_required(f):
    """Décorateur pour les routes réservées aux administrateurs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not g.user.is_admin:
            flash('Administrator access is required.', 'danger')
            abort(403)  # Forbidden
        
        return f(*args, **kwargs)
    return decorated_function
```

Ces décorateurs peuvent être utilisés pour protéger des routes :

```python
@app.route('/admin_only')
@role_required('admin')
def admin_only_route():
    # Seuls les utilisateurs avec le rôle 'admin' peuvent accéder
    return render_template('admin_page.html')
```

## Intégration avec le système de menus dynamiques

Le système d'authentification est intégré avec le système de menus dynamiques, qui charge des configurations de menu différentes selon les rôles de l'utilisateur.

### MenuConfig

La classe `MenuConfig` dans `flask_app/services/menu_config.py` gère les configurations de menu pour différents rôles :

```python
def get_menu_for_user(self, user=None):
    """
    Obtient les éléments de menu pour l'utilisateur actuel en fonction de ses rôles
    """
    if user is None:
        user = g.user if hasattr(g, 'user') else None
    
    # Si aucun utilisateur ou non authentifié, retourne un menu vide
    if not user or not user.is_authenticated:
        return []
    
    # Vérifie les rôles de l'utilisateur et retourne le menu approprié
    if user.is_admin and 'admin' in self.role_menus:
        return self.role_menus['admin']
    elif user.is_reader and 'reader' in self.role_menus:
        return self.role_menus['reader']
    
    # Si l'utilisateur a d'autres rôles, combine leurs menus
    combined_menu = []
    for role in user.roles:
        if role in self.role_menus:
            # Ajoute les éléments qui ne sont pas déjà dans le menu combiné
            for item in self.role_menus[role]:
                if item not in combined_menu:
                    combined_menu.append(item)
    
    # Si aucun menu de rôle spécifique n'est trouvé, repli sur le menu par défaut
    if not combined_menu:
        # Filtre les éléments qui ne nécessitent pas de permissions spécifiques
        combined_menu = [
            item for item in self.default_menu 
            if not item.get('required_permission') or 
            (user.has_permission(item.get('required_permission')))
        ]
    
    return combined_menu
```

## Flux de données complet

Voici le flux de données complet pour l'authentification et l'autorisation :

1. **Soumission du formulaire de connexion**:
   - L'utilisateur soumet le formulaire avec nom d'utilisateur et mot de passe
   - La route `/login` est appelée

2. **Authentification LDAP**:
   - `authenticate_user()` est appelée
   - EDIRModel tente de se connecter au serveur LDAP
   - Si l'authentification réussit, les détails de l'utilisateur sont récupérés

3. **Création de l'utilisateur**:
   - Les données LDAP sont transformées en objet User
   - L'appartenance aux groupes est vérifiée pour déterminer les rôles
   - Les rôles sont traduits en permissions

4. **Établissement de la session**:
   - `login_user()` est appelé pour démarrer la session Flask-Login
   - Les données utilisateur sont stockées en session
   - L'utilisateur est redirigé vers le tableau de bord

5. **Requêtes subséquentes**:
   - `before_request` charge l'utilisateur dans `g.user`
   - `current_user` est disponible dans toutes les routes et templates
   - Les décorateurs de contrôle d'accès vérifient les rôles et permissions

6. **Système de menus dynamiques**:
   - `MenuConfig` charge les menus en fonction des rôles de l'utilisateur
   - Les éléments de menu nécessitant des permissions spécifiques sont filtrés

7. **Déconnexion**:
   - `logout_user()` termine la session Flask-Login
   - `session.clear()` supprime toutes les données de session

## Personnalisation et extension

### Ajout de nouveaux rôles

Pour ajouter un nouveau rôle :

1. Mettre à jour la logique dans `User.from_ldap_data()` pour attribuer le nouveau rôle
2. Définir les permissions pour le nouveau rôle
3. Créer un fichier de configuration de menu `flask_app/config/menu_role_newrole.json`

```python
# Exemple d'ajout d'un rôle "manager"
if 'manager_group_dn' in user_data and user_data.get('is_manager_member', False):
    roles.append('manager')

# Définir les permissions pour le nouveau rôle
if 'manager' in roles:
    permissions.update([
        'view_users', 'edit_users',
        'view_groups', 'edit_groups',
        'view_reports', 'generate_reports'
    ])
```

### Personnalisation des permissions

Les permissions sont définies dans `User.from_ldap_data()` et peuvent être facilement étendues :

```python
# Exemple d'ajout de nouvelles permissions pour le rôle admin
if 'admin' in roles:
    permissions.update([
        # Permissions existantes
        'view_users', 'create_users', 'edit_users', 'delete_users',
        # Nouvelles permissions
        'export_data', 'import_data', 'run_background_jobs',
        'view_audit_logs', 'purge_old_data'
    ])
```

## Bonnes pratiques

1. **Sécurité de la clé secrète** : Remplacer la clé secrète par défaut dans `create_app()` par une clé sécurisée stockée dans une variable d'environnement.

2. **HTTPS** : Toujours utiliser HTTPS en production pour protéger les sessions et les identifiants.

3. **Protection CSRF** : Activer la protection CSRF pour tous les formulaires POST :

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    # ...
    csrf.init_app(app)
    # ...
```

4. **Échéance de session** : Configurer une échéance de session appropriée :

```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
```

5. **Logging** : Implémenter un logging approprié pour les événements d'authentification :

```python
import logging
logger = logging.getLogger(__name__)

def authenticate_user(username, password, ldap_source='meta'):
    try:
        # ...
        logger.info(f"User {username} authenticated successfully from source {ldap_source}")
        # ...
    except Exception as e:
        logger.error(f"Authentication error for user {username}: {str(e)}")
        return None
```

## Troubleshooting

### Problèmes de Session

Si les sessions expirent prématurément ou ne persistent pas :

1. Vérifier la configuration `PERMANENT_SESSION_LIFETIME`
2. S'assurer que `app.secret_key` est correctement définie
3. Vérifier que les cookies sont correctement configurés pour HTTPS

### Problèmes d'authentification LDAP

Si l'authentification LDAP échoue :

1. Vérifier les paramètres de connexion au serveur LDAP
2. S'assurer que le DN et le mot de passe de liaison sont corrects
3. Vérifier que le DN de l'utilisateur est correctement formaté
4. Activer le débogage LDAP pour des messages d'erreur plus détaillés

### Problèmes de permissions

Si les utilisateurs n'obtiennent pas les bonnes permissions :

1. Vérifier l'appartenance aux groupes dans l'annuaire LDAP
2. Vérifier les `admin_group_dn` et `reader_group_dn` dans votre configuration LDAP
3. Déboguer en affichant les résultats de recherche LDAP dans `authenticate_user()`

### Débogage de Flask-Login

Pour déboguer des problèmes avec Flask-Login :

1. Activer le mode débogage de Flask : `app.debug = True`
2. Vérifier que `login_user()` est bien appelé et retourne `True`
3. Vérifier que `user_loader` charge correctement l'utilisateur
4. Inspecter le contenu de `session` et `g.user`