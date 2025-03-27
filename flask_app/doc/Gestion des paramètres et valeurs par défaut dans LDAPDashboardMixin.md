# Documentation: Gestion des paramètres et valeurs par défaut dans LDAPDashboardMixin

Cette documentation explique comment utiliser et configurer les statistiques du tableau de bord LDAP, avec un focus particulier sur les paramètres et valeurs par défaut.

## Comprendre les valeurs par défaut dans les dictionnaires Python

Lorsqu'on récupère une valeur depuis un dictionnaire, la méthode `get()` permet de spécifier une valeur par défaut si la clé n'existe pas:

```python
# Syntaxe: dictionnaire.get('clé', valeur_par_défaut)
disabled_accounts = stats.get('disabled_accounts', 0)
```

**Comportement:**
- Si `'disabled_accounts'` existe dans `stats`, la méthode retourne cette valeur
- Si `'disabled_accounts'` n'existe pas, la méthode retourne `0` (empêchant les erreurs `KeyError`)

## Paramètres dans les méthodes de statistiques

### Approche actuelle

Actuellement, les méthodes sont appelées individuellement:

```python
# Dans LDAPDashboardMixin
def get_inactive_users_count(self, months=3):
    # Logique pour trouver les utilisateurs inactifs depuis 'months' mois
    # ...

# Dans la route dashboard.py
inactive_users = ldap_model.get_inactive_users_count(months=3)
```

Cette approche:
- Est redondante (months=3 est déjà la valeur par défaut)
- Nécessite plusieurs appels LDAP séparés
- Rend le code de la route verbeux

### Approche recommandée

Une approche plus efficace est de regrouper les statistiques dans `get_dashboard_stats()` avec des paramètres personnalisables:

```python
# Dans LDAPDashboardMixin
def get_dashboard_stats(self, inactive_months=3):
    return {
        'total_users': self.get_total_users_count(),
        'recent_logins': self.get_recent_logins_count(),
        'disabled_accounts': self.get_disabled_accounts_count(),
        'inactive_users': self.get_inactive_users_count(months=inactive_months),
        'expired_password_users': self.get_expired_password_users_count(),
        'never_logged_in_users': self.get_never_logged_in_users_count()
    }

# Dans la route dashboard.py
stats = ldap_model.get_dashboard_stats()  # Utilise la valeur par défaut (3 mois)
# Ou avec paramètre personnalisé:
# stats = ldap_model.get_dashboard_stats(inactive_months=6)  # 6 mois d'inactivité

disabled_accounts = stats.get('disabled_accounts', 0)
inactive_users = stats.get('inactive_users', 0)
expired_password_users = stats.get('expired_password_users', 0)
never_logged_in_users = stats.get('never_logged_in_users', 0)
```

## Exemple détaillé: Changer la période d'inactivité

### Scénario 1: Utiliser la période par défaut (3 mois)

```python
# Dans LDAPDashboardMixin
def get_dashboard_stats(self, inactive_months=3):
    # ... le reste de la méthode ...
    'inactive_users': self.get_inactive_users_count(months=inactive_months),
    # ...

# Dans la route
stats = ldap_model.get_dashboard_stats()  # Utilise inactive_months=3 par défaut
inactive_users = stats.get('inactive_users', 0)  # Utilisateurs inactifs depuis 3+ mois
```

### Scénario 2: Personnaliser la période (6 mois)

```python
# Dans la route
stats = ldap_model.get_dashboard_stats(inactive_months=6)  # Remplace la valeur par défaut
inactive_users = stats.get('inactive_users', 0)  # Utilisateurs inactifs depuis 6+ mois
```

## Avantages de cette approche

1. **Simplicité**: Une seule méthode (`get_dashboard_stats()`) à appeler dans la route
2. **Flexibilité**: Possibilité de personnaliser les paramètres selon les besoins
3. **Performance**: Réduction potentielle du nombre de connexions LDAP
4. **Maintenance**: Centralisation de la logique de récupération des statistiques
5. **Clarté**: Valeurs par défaut définies une seule fois, à un endroit logique

## Recommandations pour l'implémentation

- Définissez des valeurs par défaut réalistes dans les méthodes
- N'utilisez des paramètres explicites que lorsque vous souhaitez remplacer ces valeurs par défaut
- Regroupez les statistiques liées dans une seule méthode
- Utilisez systématiquement `get()` avec une valeur par défaut pour extraire les résultats

Cette approche garantit un code plus robuste, plus lisible et plus facile à maintenir.