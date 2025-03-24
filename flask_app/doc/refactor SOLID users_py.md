## Schéma révisé de refactorisation

### Structure des classes:

#### 1. `LDAPUserCRUD` (dans `user_crud.py`):
- Hérite de `LDAPBase`
- Méthodes principales:
  - `get_user()` - Version améliorée et unifiée de `search_user_final` et `get_pending_users`
    - Avec options pour filtrer par container, par attributs spécifiques, etc.
    - Paramètres pour contrôler le format de retour (simplifié ou complet)
  - `create_user()` - Pour la création initiale d'utilisateurs
  - `update_user()` - Version étendue qui englobe aussi `complete_user_creation`
    - Avec paramètres optionnels pour gérer différents scénarios de mise à jour
  - `delete_user()` - Pour supprimer un utilisateur

#### 2. `LDAPUserUtils` (dans `user_utils.py`):
- Hérite de `LDAPBase`
- Méthodes:
  - `generate_unique_cn()` - Génération de CN uniques
  - `generate_password_from_cn()` - Génération de mots de passe
  - `check_name_combination_exists()` - Vérification des combinaisons de noms
  - `check_favvnatnr_exists()` - Vérification de l'existence d'un FavvNatNr
  - Autres méthodes utilitaires sans opérations CRUD directes

## Documentation sur l'implémentation révisée

### 1. Unification de `get_user`

```markdown
### `get_user(search_param, options=None)`

**Description:**  
Méthode unifiée pour rechercher des utilisateurs dans le LDAP, remplaçant `search_user_final` et `get_pending_users`.

**Paramètres:**
- `search_param`: Chaîne de recherche (CN, mail, etc.) ou DN complet
- `options`: Dictionnaire d'options pour la recherche:
  - `search_type`: Type de recherche ('cn', 'fullName', 'mail', etc.)
  - `container`: Container spécifique à rechercher ('active', 'inactive', 'toprocess', 'all')
  - `simplified`: Retourner un format simplifié (True/False)
  - `return_list`: Retourner une liste d'utilisateurs au lieu d'un seul
  - `filter_attributes`: Dictionnaire d'attributs pour filtrer les résultats
  - `attributes`: Liste d'attributs à retourner (None = tous les attributs)

**Retourne:**
- Un dictionnaire d'utilisateur ou une liste de dictionnaires selon les options
```

### 2. Extension de `update_user`

```markdown
### `update_user(user_dn, attributes=None, options=None)`

**Description:**  
Méthode étendue pour mettre à jour les utilisateurs, englobant aussi la fonctionnalité de `complete_user_creation`.

**Paramètres:**
- `user_dn`: DN de l'utilisateur à mettre à jour
- `attributes`: Dictionnaire d'attributs à modifier
- `options`: Dictionnaire d'options pour la mise à jour:
  - `groups_to_add`: Liste des groupes à ajouter
  - `groups_to_remove`: Liste des groupes à supprimer
  - `reset_password`: Réinitialiser le mot de passe (True/False)
  - `expire_password`: Forcer l'expiration du mot de passe (True/False)
  - `target_container`: Container cible pour déplacer l'utilisateur
  - `change_reason`: Raison du changement (pour la journalisation)
  - `is_completion`: Indique si c'est une opération de complétion (True/False)

**Retourne:**
- Tuple (bool, str): Succès de l'opération et message de statut
```

## Diagramme de la nouvelle structure

```
                                   ┌───────────┐
                                   │  LDAPBase │
                                   └─────┬─────┘
                                         │
                                         │
                 ┌─────────────────────────────────────────┐
                 │                                         │
                 ▼                                         ▼
        ┌─────────────────┐                     ┌─────────────────┐
        │   LDAPUserCRUD  │                     │  LDAPUserUtils  │
        │                 │                     │                 │
        │ - get_user()    │                     │ - generate_     │
        │ - create_user() │                     │   unique_cn()   │
        │ - update_user() │                     │ - generate_     │
        │ - delete_user() │                     │   password_     │
        │                 │                     │   from_cn()     │
        │                 │                     │ - check_name_   │
        │                 │                     │   combination_  │
        │                 │                     │   exists()      │
        │                 │                     │ - check_        │
        │                 │                     │   favvnatnr_    │
        │                 │                     │   exists()      │
        └────────┬────────┘                     └────────┬────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
                           ┌─────────────────┐
                           │  LDAPUserMixin  │
                           └─────────────────┘
```

Cette approche non seulement simplifie l'interface en réduisant le nombre de méthodes, mais elle rend aussi les fonctions individuelles plus puissantes et flexibles. Les options par défaut permettront de maintenir la compatibilité avec le code existant tout en permettant des utilisations plus avancées.