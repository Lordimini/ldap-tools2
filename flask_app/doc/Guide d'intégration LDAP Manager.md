# Guide d'intégration de la bibliothèque LDAP Manager JS

Ce guide explique comment intégrer la nouvelle bibliothèque JavaScript à votre application LDAP Manager existante.

## Structure des fichiers

La bibliothèque est composée des fichiers suivants :

```
static/js/
├── utils/
│   ├── ldap-utils.js        - Utilitaires pour la gestion des sources LDAP
│   ├── validation-utils.js  - Validation des formulaires
├── components/
│   ├── datatables-init.js   - Initialisation des tables DataTables
│   ├── autocomplete-init.js - Initialisation des fonctionnalités d'autocomplétion
│   ├── group-management.js  - Gestion des groupes (ajout/suppression)
├── compatibility.js         - Fonctions de compatibilité avec le code existant
├── main-init.js             - Logique d'initialisation commune
└── app.js                   - Point d'entrée principal
```

## Méthode d'intégration recommandée

### Étape 1: Inclusion des fichiers

Modifiez votre fichier `base.html` pour inclure la bibliothèque. Ajoutez le code suivant avant la fin du bloc `scripts` :

```html
<!-- LDAP Manager Library -->
<script src="{{ url_for('static', filename='js/utils/ldap-utils.js') }}"></script>
<script src="{{ url_for('static', filename='js/utils/validation-utils.js') }}"></script>
<script src="{{ url_for('static', filename='js/components/datatables-init.js') }}"></script>
<script src="{{ url_for('static', filename='js/components/autocomplete-init.js') }}"></script>
<script src="{{ url_for('static', filename='js/components/group-management.js') }}"></script>
<script src="{{ url_for('static', filename='js/compatibility.js') }}"></script>
<script src="{{ url_for('static', filename='js/main-init.js') }}"></script>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
```

### Étape 2: Migration progressive des pages

Pour chaque page, vous avez deux options :

#### Option A: Migration complète
1. Supprimer l'inclusion du fichier JS spécifique à la page
2. Utiliser uniquement la bibliothèque commune

#### Option B: Coexistence temporaire
1. Conserver le fichier JS spécifique à la page
2. Modifier ce fichier pour utiliser les fonctions de la bibliothèque commune

### Exemple de migration complète (pour `search.html`)

Avant :
```html
{% block scripts %}
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://code.jquery.com/ui/1.13.1/jquery-ui.min.js"></script>
<script>
    window.autocompleteFullNameUrl = "{{ url_for('autocomplete.autocomplete_fullName') }}";
</script>
<script src="{{ url_for('static', filename='js/search.js') }}"></script>
{% endblock %}
```

Après :
```html
{% block scripts %}
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://code.jquery.com/ui/1.13.1/jquery-ui.min.js"></script>
<script>
    window.autocompleteFullNameUrl = "{{ url_for('autocomplete.autocomplete_fullName') }}";
</script>
{% endblock %}
```

### Exemple de coexistence temporaire (pour `update_user.js`)

Modifiez votre fichier JS existant :

```javascript
// Fichier: static/js/update_user.js
$(document).ready(function() {
    // Utiliser les fonctions de la bibliothèque pour les opérations communes
    const ldapSource = LDAPUtils.getCurrentSource();
    
    // Code spécifique à la page qui n'est pas encore migré
    // ...
    
    // Utiliser les fonctions de la bibliothèque pour la gestion des groupes
    GroupManagementUtils.initGroupsToAdd();
    GroupManagementUtils.initGroupsToRemove(window.userGroups || []);
    GroupManagementUtils.initSortAndFilter();
});
```

## Configuration avancée

Vous pouvez configurer le comportement de la bibliothèque en utilisant l'API `LDAPManager` :

```javascript
// Désactiver l'initialisation automatique
window.LDAPManagerNoAutoInit = true;

// Initialiser manuellement avec des options personnalisées
$(document).ready(function() {
    window.LDAPManager.init({
        debug: true,               // Activer les logs de debug
        enhanceLinks: true,        // Améliorer les liens avec le paramètre source
        enhanceForms: true,        // Améliorer les formulaires avec le champ source
        initDataTables: true,      // Initialiser les tables DataTables
        initAutocomplete: true,    // Initialiser les fonctionnalités d'autocomplétion
        initGroupManagement: true  // Initialiser la gestion des groupes
    });
});
```

## Réinitialisation des fonctionnalités

Si vous avez besoin de réinitialiser certaines fonctionnalités après un changement dynamique dans le DOM :

```javascript
// Réinitialiser les tables DataTables
LDAPManager.reinitialize('tables');

// Réinitialiser les fonctionnalités d'autocomplétion
LDAPManager.reinitialize('autocomplete');

// Réinitialiser toutes les fonctionnalités
LDAPManager.reinitialize('all');
```

## Accès aux utilitaires

Pour un accès direct aux utilitaires :

```javascript
// Utiliser les utilitaires LDAP
const source = LDAPManager.utils.ldap.getCurrentSource();

// Initialiser une table DataTables personnalisée
const table = LDAPManager.utils.dataTables.initGenericTable('#myTable', {
    pageLength: 25,
    order: [[0, 'desc']]
});
```

## Support des événements

La bibliothèque émet des événements que vous pouvez utiliser pour synchroniser votre code :

```javascript
$(document).on('ldapmanager:initialized', function() {
    // Code à exécuter après l'initialisation de la bibliothèque
    console.log('LDAP Manager a été initialisé');
});
```

## Migration complète

Une fois que toutes les pages ont été migrées, vous pouvez :

1. Supprimer tous les anciens fichiers JS spécifiques aux pages
2. Supprimer le fichier `compatibility.js` qui n'est plus nécessaire
3. Mettre à jour la documentation en conséquence

## Dépannage

Si vous rencontrez des problèmes lors de l'intégration :

1. Activez le mode debug : `LDAPManager.init({ debug: true })`
2. Vérifiez la console pour les messages d'erreur
3. Assurez-vous que jQuery est chargé avant la bibliothèque
4. Vérifiez que les URL d'autocomplétion sont correctement définies (`window.autocompleteFullNameUrl`, etc.)