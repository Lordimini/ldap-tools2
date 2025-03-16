# Résumé de l'architecture Flask-Login dans LDAP Manager

Ce document sert de résumé concis de l'implémentation Flask-Login dans l'application LDAP Manager, fournissant suffisamment de contexte pour comprendre l'architecture complète sans accès aux fichiers source.

## Structure des fichiers clés

```
flask_app/
├── __init__.py                      # Initialisation de l'app et LoginManager
├── config/
│   ├── menu_base.json               # Menu de base pour tous les utilisateurs
│   ├── menu_role_admin.json         # Menu spécifique aux admins
│   └── menu_role_reader.json        # Menu spécifique aux lecteurs
├── models/
│   ├── ldap_config_manager.py       # Gestion des connexions LDAP
│   └── user_model.py                # Modèle User avec UserMixin + RBAC
├── services/
│   ├── login_manager.py             # Configuration de Flask-Login
│   ├── menu_config.py               # Menus dynamiques basés sur rôles
│   └── menu_service.py              # Service alternatif pour menus
├── routes/
│   └── auth.py                      # Routes d'authentification
└── templates/
    ├── base.html                    # Template avec menu et user dropdown
    └── login.html                   # Page de connexion
```

## Modèle d'authentification

LDAP Manager utilise une architecture d'authentification hybride:

1. **Flask-Login** gère les sessions utilisateur côté serveur
2. **LDAP** (via `EDIRModel`) pour l'authentification et les données utilisateur
3. **RBAC** (Role-Based Access Control) basé sur les groupes LDAP

## Flux d'authentification

```
+-------------+    +-------------+    +---------------+    +-------------+
| Formulaire  | -> | Route login | -> | authenticate_ | -> | EDIRModel   |
| de login    |    | auth.py     |    | user()        |    | (LDAP Auth) |
+-------------+    +-------------+    +---------------+    +-------------+
                                             |
                                             v
+-------------+    +-------------+    +---------------+
| Menu        | <- | Données     | <- | User.from_    |
| dynamique   |    | utilisateur |    | ldap_data()   |
+-------------+    | en session  |    +---------------+
                   +-------------+
```

## Modèle utilisateur et RBAC

La classe `User` dans `user_model.py`:
- Hérite de `UserMixin` de Flask-Login
- Stocke l'username, DN, display_name, email, ldap_source
- Maintient les listes de rôles, permissions et groupes
- Méthodes: `has_role()`, `has_permission()`, `is_in_group()`
- Propriétés: `is_admin`, `is_reader`, `name`

Les rôles sont dérivés de l'appartenance aux groupes LDAP:
- Groupe admin → rôle "admin" → toutes les permissions
- Groupe reader → rôle "reader" → permissions limitées de lecture

## Configuration de Flask-Login

Dans `services/login_manager.py`:
- Instance unique de `LoginManager`
- Configuration: login_view, login_message, login_message_category
- User loader qui récupère l'utilisateur depuis la session
- Before request handler qui positionne `g.user` à `current_user`
- Fonction `authenticate_user()` pour l'authentification LDAP

## Gestion des sessions

Stockage en session:
- Données utilisateur brutes: `session['user_data']`
- Indicateurs d'état: `session['logged_in']`, `session['username']`
- Informations de rôle: `session['role']`
- Configuration LDAP: `session['ldap_source']`, `session['ldap_name']`

Le chargement utilisateur utilise:
1. L'identifiant fourni par Flask-Login
2. Les données brutes stockées dans `session['user_data']`
3. La méthode `User.from_ldap_data()` pour reconstruire l'objet

## Contrôle d'accès

Trois décorateurs de contrôle d'accès:
1. `@role_required(role)` - Vérifie un rôle spécifique
2. `@permission_required(permission)` - Vérifie une permission spécifique
3. `@admin_required` - Shorthand pour le rôle admin

Exemple:
```python
@app.route('/manage_users')
@permission_required('edit_users')
def manage_users():
    # Accès uniquement avec permission 'edit_users'
    return render_template('manage_users.html')
```

## Intégration des menus dynamiques

Le système utilise deux services de menu:
1. `MenuConfig` (principal): Gère les menus basés sur les rôles utilisateur
2. `MenuService` (secondaire): Gère les menus basés sur la source LDAP

Configuration par fichiers JSON:
- `menu_base.json`: Menu par défaut
- `menu_role_admin.json`: Menu administrateur
- `menu_role_reader.json`: Menu lecteur

Structure du menu:
```json
{
  "menu_items": [
    {
      "label": "Dashboard",
      "url": "/dashboard",
      "icon": "bi bi-speedometer2",
      "active_pattern": "^/dashboard"
    },
    {
      "is_section": true,
      "label": "SECTION",
      "items": [
        {
          "label": "Menu Item",
          "url": "/path",
          "icon": "bi bi-icon",
          "required_permission": "permission_name"
        }
      ]
    }
  ]
}
```

## Configuration LDAP

Gérée par `LDAPConfigManager` qui:
- Maintient les configurations pour différentes sources LDAP (meta, idme)
- Gère le basculement entre sources LDAP
- Stocke la source active dans `session['ldap_source']`

Sources LDAP disponibles:
- `meta`: Source LDAP par défaut
- `idme`: Source LDAP secondaire

## Points d'extension

Pour ajouter un nouveau rôle:
1. Mettre à jour la détection dans `User.from_ldap_data()`
2. Définir les permissions pour ce rôle
3. Créer `menu_role_newrole.json`

Pour personnaliser les permissions:
- Modifier les ensembles de permissions dans `User.from_ldap_data()`

Pour ajouter une source LDAP:
- Ajouter la configuration à `LDAPConfigManager.configs`
- Créer les fichiers de menu correspondants

## Éléments de sécurité

Pratiques à implémenter/vérifier:
- Remplacer la clé secrète par défaut `eyqscmnc`
- Utiliser HTTPS en production
- Configurer `PERMANENT_SESSION_LIFETIME`
- Ajouter protection CSRF
- Implémenter un système de logging pour les événements d'authentification

## Problèmes courants

Authentification LDAP:
- Vérifier les paramètres de connexion au serveur LDAP
- S'assurer que les DNs des groupes admin/reader sont corrects

Sessions Flask-Login:
- Vérifier que `login_user()` retourne True
- Inspecter le contenu de `session` et `g.user`

Permissions incorrectes:
- Vérifier l'appartenance aux groupes LDAP
- Déboguer la méthode `User.from_ldap_data()`

## Intégration dans l'UI

L'interface utilisateur affiche:
- Le nom/username de l'utilisateur dans la barre de navigation
- Des badges pour les rôles (Admin, Reader)
- Un menu dynamique basé sur les rôles/permissions
- Un sélecteur de source LDAP pour les utilisateurs authentifiés

## Notes techniques

- Les configurations sont redondantes entre `MenuConfig` et `MenuService`
- Le code conserve la session Flask native pour compatibilité avec du code existant
- Les routes stockent `is_admin` comme raccourci dans `session['role']`