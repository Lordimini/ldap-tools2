# Documentation des Composants JavaScript - LDAP Manager

## Table des matières

1. [Architecture générale](#architecture-générale)
2. [Modules principaux](#modules-principaux)
   - [LDAPManager](#ldapmanager)
   - [LDAPUtils](#ldaputils)
   - [AutocompleteUtils](#autocompleteutils)
   - [DataTableUtils](#datatableutils)
   - [GroupManagementUtils](#groupmanagementutils)
   - [ValidationUtils](#validationutils)
3. [Flux d'initialisation](#flux-dinitialisation)
4. [Fonctionnalités par page](#fonctionnalités-par-page)
5. [Compatibilité et transition](#compatibilité-et-transition)
6. [Bonnes pratiques](#bonnes-pratiques)

## Architecture générale

L'architecture JavaScript de LDAP Manager est organisée selon un modèle modulaire où chaque composant est responsable d'une fonctionnalité spécifique. Cette approche facilite la maintenance, le test et l'extension du code.

### Structure des fichiers

```
flask_app/static/js/
├── app.js                      # Point d'entrée principal
├── main-init.js                # Initialisation détaillée des composants
├── compatibility.js            # Couche de compatibilité pour code existant
├── main.js                     # Fonctions générales (UI, navigation)
├── components/                 # Modules fonctionnels
│   ├── autocomplete-init.js    # Gestion des autocompletions
│   ├── datatables-init.js      # Configuration des tables
│   └── group-management.js     # Gestion des groupes
├── utils/                      # Utilitaires génériques
│   ├── ldap-utils.js           # Fonctions liées à LDAP
│   └── validation-utils.js     # Validation des formulaires
└── pages/                      # Scripts spécifiques aux pages
    ├── add_user_list_group.js  # Ajout d'utilisateurs à un groupe
    ├── group_users.js          # Gestion des utilisateurs d'un groupe
    ├── post_creation.js        # Post-création d'utilisateur
    ├── search.js               # Recherche
    ├── update_user.js          # Mise à jour d'utilisateur
    └── user_creation.js        # Création d'utilisateur
```

## Modules principaux

### LDAPManager

`LDAPManager` est le point d'entrée principal de la bibliothèque. Il coordonne l'initialisation de tous les autres modules.

```javascript
window.LDAPManager = {
  init: function(options = {}) {
    // Options par défaut
    const defaultOptions = {
      debug: false,
      enhanceLinks: true,
      enhanceForms: true,
      initDataTables: true,
      initAutocomplete: true,
      initGroupManagement: true
    };
    
    // Fusionner avec options personnalisées
    const config = { ...defaultOptions, ...options };
    
    // Initialiser les composants selon la configuration
    // ...
  },
  
  reinitialize: function(feature, options = {}) {
    // Réinitialiser un composant spécifique
    // ...
  },
  
  utils: {
    ldap: LDAPUtils,
    dataTables: DataTableUtils,
    autocomplete: AutocompleteUtils,
    groupManagement: GroupManagementUtils,
    validation: ValidationUtils
  }
};
```

#### Options d'initialisation

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| `debug` | Boolean | `false` | Active le mode debug avec logs détaillés |
| `enhanceLinks` | Boolean | `true` | Ajoute automatiquement le paramètre source LDAP aux liens |
| `enhanceForms` | Boolean | `true` | Ajoute automatiquement le champ LDAP source aux formulaires |
| `initDataTables` | Boolean | `true` | Initialise les DataTables sur la page |
| `initAutocomplete` | Boolean | `true` | Initialise les fonctionnalités d'autocomplétion |
| `initGroupManagement` | Boolean | `true` | Initialise la gestion des groupes |

#### Utilisation

```javascript
// Initialisation par défaut
LDAPManager.init();

// Initialisation personnalisée
LDAPManager.init({
  debug: true,
  initDataTables: false
});

// Réinitialisation d'un composant
LDAPManager.reinitialize('tables');
```

### LDAPUtils

Module utilitaire pour la gestion des sources LDAP et des URLs.

```javascript
const LDAPUtils = {
  getCurrentSource: function() {
    // Récupère la source LDAP actuelle
    return $('#current_ldap_source').val() || 'meta';
  },
  
  enhanceLinks: function(source) {
    // Ajoute le paramètre source à tous les liens internes
  },
  
  enhanceForms: function(source) {
    // Ajoute le champ LDAP source à tous les formulaires
  },
  
  setupRefreshButton: function() {
    // Configure le bouton de rafraîchissement
  },
  
  init: function() {
    // Initialise toutes les fonctionnalités
  }
};
```

#### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `getCurrentSource()` | Récupère la source LDAP actuelle depuis un élément caché du DOM |
| `enhanceLinks(source)` | Ajoute le paramètre `source` à tous les liens internes |
| `enhanceForms(source)` | Ajoute un champ caché `ldap_source` à tous les formulaires |
| `setupRefreshButton()` | Configure le bouton de changement de source LDAP |
| `init()` | Initialise toutes les fonctionnalités du module |

#### Utilisation

```javascript
// Récupérer la source LDAP actuelle
const source = LDAPUtils.getCurrentSource();

// Améliorer manuellement les liens et formulaires
LDAPUtils.enhanceLinks(source);
LDAPUtils.enhanceForms(source);

// Initialiser tout
LDAPUtils.init();
```

### AutocompleteUtils

Module pour gérer les fonctionnalités d'autocomplétion des champs de recherche.

```javascript
const AutocompleteUtils = {
  initFullNameAutocomplete: function(inputSelector, sourceUrl, ldapSource) {
    // Initialise l'autocomplétion pour la recherche par nom complet
  },
  
  initGroupAutocomplete: function(inputSelector, sourceUrl, ldapSource, onSelect) {
    // Initialise l'autocomplétion pour la recherche de groupes
  },
  
  initManagerAutocomplete: function(inputSelector, sourceUrl, ldapSource, dnFieldSelector) {
    // Initialise l'autocomplétion pour la recherche de managers
  },
  
  initServiceAutocomplete: function(inputSelector, sourceUrl, ldapSource) {
    // Initialise l'autocomplétion pour la recherche de services
  },
  
  initRoleAutocomplete: function(inputSelector, sourceUrl, ldapSource) {
    // Initialise l'autocomplétion pour la recherche de rôles
  },
  
  initSearchTypeAutocomplete: function(searchTypeSelector, searchTermSelector, fullNameUrl, ldapSource) {
    // Initialise l'autocomplétion en fonction du type de recherche
  }
};
```

#### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `initFullNameAutocomplete(inputSelector, sourceUrl, ldapSource)` | Initialise l'autocomplétion pour la recherche par nom |
| `initGroupAutocomplete(inputSelector, sourceUrl, ldapSource, onSelect)` | Initialise l'autocomplétion pour les groupes |
| `initManagerAutocomplete(inputSelector, sourceUrl, ldapSource, dnFieldSelector)` | Initialise l'autocomplétion pour les managers |
| `initServiceAutocomplete(inputSelector, sourceUrl, ldapSource)` | Initialise l'autocomplétion pour les services |
| `initRoleAutocomplete(inputSelector, sourceUrl, ldapSource)` | Initialise l'autocomplétion pour les rôles |
| `initSearchTypeAutocomplete(searchTypeSelector, searchTermSelector, fullNameUrl, ldapSource)` | Initialise l'autocomplétion basée sur le type de recherche |

#### Utilisation

```javascript
// Initialiser l'autocomplétion pour un champ de recherche de noms
AutocompleteUtils.initFullNameAutocomplete(
  '#search_term', 
  '/api/autocomplete/fullname', 
  'meta'
);

// Initialiser l'autocomplétion pour un champ de recherche de groupes
AutocompleteUtils.initGroupAutocomplete(
  '#group_name',
  '/api/autocomplete/groups',
  'meta',
  function(selectedItem) {
    console.log('Groupe sélectionné:', selectedItem);
  }
);
```

### DataTableUtils

Module pour initialiser et configurer les tables de données avec DataTables.

```javascript
const DataTableUtils = {
  enableClickableRows: function(tableSelector, urlBase, dataAttribute, ldapSource) {
    // Active les lignes cliquables dans une table
  },
  
  defaultUserTableOptions: {
    // Options par défaut pour les tables d'utilisateurs
  },
  
  defaultGroupTableOptions: {
    // Options par défaut pour les tables de groupes
  },
  
  initUserTable: function(tableSelector, customOptions, clickableOptions) {
    // Initialise une table d'utilisateurs
  },
  
  initGroupTable: function(tableSelector, customOptions) {
    // Initialise une table de groupes
  },
  
  initGenericTable: function(tableSelector, options, clickableOptions) {
    // Initialise une table générique
  },
  
  enhanceDataTableStyle: function() {
    // Améliore le style des éléments DataTables
  },
  
  setupColumnFilter: function(table, inputSelector, columnIndex) {
    // Configure le filtrage sur une colonne spécifique
  }
};
```

#### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `enableClickableRows(tableSelector, urlBase, dataAttribute, ldapSource)` | Rend les lignes de table cliquables |
| `initUserTable(tableSelector, customOptions, clickableOptions)` | Initialise une table d'utilisateurs |
| `initGroupTable(tableSelector, customOptions)` | Initialise une table de groupes |
| `initGenericTable(tableSelector, options, clickableOptions)` | Initialise une table générique |
| `enhanceDataTableStyle()` | Améliore les styles des éléments DataTables |
| `setupColumnFilter(table, inputSelector, columnIndex)` | Configure un filtre pour une colonne spécifique |

#### Options par défaut pour les tables d'utilisateurs

```javascript
defaultUserTableOptions: {
  responsive: true,
  paging: true,
  pageLength: 10,
  lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
  searching: true,
  info: true,
  order: [[1, 'asc']], // Tri par défaut sur la colonne "Full Name"
  columnDefs: [
    { orderable: true, targets: [0, 1, 2, 3] }
  ],
  language: {
    search: "",
    searchPlaceholder: "Search in all columns...",
    zeroRecords: "No matching records found",
    info: "Showing _START_ to _END_ of _TOTAL_ users",
    infoEmpty: "No users found",
    infoFiltered: "(filtered from _MAX_ total users)"
  }
}
```

#### Utilisation

```javascript
// Initialiser une table d'utilisateurs avec options par défaut
const usersTable = DataTableUtils.initUserTable('#usersTable');

// Initialiser une table d'utilisateurs avec lignes cliquables
const clickableTable = DataTableUtils.initUserTable('#usersTable', {}, {
  urlBase: '/user',
  dataAttribute: 'cn',
  ldapSource: 'meta'
});

// Initialiser une table avec options personnalisées
const customTable = DataTableUtils.initGenericTable('#customTable', {
  paging: false,
  ordering: false,
  info: false
});

// Ajouter un filtre sur une colonne
DataTableUtils.setupColumnFilter(usersTable, '#serviceFilter', 3);
```

### GroupManagementUtils

Module pour gérer les sélections de groupes et d'utilisateurs.

```javascript
const GroupManagementUtils = {
  selectedUsers: [], // Utilisateurs sélectionnés pour l'ajout à un groupe
  groupsToAdd: [],   // Groupes sélectionnés pour l'ajout
  groupsToRemove: [], // Groupes sélectionnés pour la suppression
  
  initUserSelection: function(initialUsers) {
    // Initialise la gestion des utilisateurs
  },
  
  updateSelectedUsersUI: function() {
    // Met à jour l'interface utilisateur
  },
  
  initGroupsToAdd: function() {
    // Initialise la gestion des groupes à ajouter
  },
  
  updateGroupsToAddDisplay: function() {
    // Met à jour l'affichage des groupes à ajouter
  },
  
  removeAddGroup: function(index) {
    // Supprime un groupe de la liste des groupes à ajouter
  },
  
  initGroupsToRemove: function(userGroups) {
    // Initialise la gestion des groupes à supprimer
  },
  
  updateGroupsToRemoveDisplay: function() {
    // Met à jour l'affichage des groupes à supprimer
  },
  
  removeRemoveGroup: function(index) {
    // Supprime un groupe de la liste des groupes à supprimer
  },
  
  initSortAndFilter: function() {
    // Initialise les filtres et tris pour les groupes et rôles
  }
};
```

#### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `initUserSelection(initialUsers)` | Initialise la sélection d'utilisateurs |
| `updateSelectedUsersUI()` | Met à jour l'UI des utilisateurs sélectionnés |
| `initGroupsToAdd()` | Initialise les groupes à ajouter |
| `updateGroupsToAddDisplay()` | Met à jour l'UI des groupes à ajouter |
| `removeAddGroup(index)` | Supprime un groupe à ajouter |
| `initGroupsToRemove(userGroups)` | Initialise les groupes à supprimer |
| `updateGroupsToRemoveDisplay()` | Met à jour l'UI des groupes à supprimer |
| `removeRemoveGroup(index)` | Supprime un groupe à supprimer |
| `initSortAndFilter()` | Initialise les filtres et tris pour groupes et rôles |

#### Format des données

```javascript
// Format des utilisateurs sélectionnés
selectedUsers = [
  { dn: "CN=user1,OU=Users,DC=example,DC=com", cn: "user1", fullName: "User One" },
  { dn: "CN=user2,OU=Users,DC=example,DC=com", cn: "user2", fullName: "User Two" }
];

// Format des groupes à ajouter/supprimer
groupsToAdd = [
  { name: "Groupe A", dn: "CN=GroupA,OU=Groups,DC=example,DC=com" },
  { name: "Groupe B", dn: "CN=GroupB,OU=Groups,DC=example,DC=com" }
];
```

#### Utilisation

```javascript
// Initialiser la sélection d'utilisateurs
GroupManagementUtils.initUserSelection([]);

// Initialiser la gestion des groupes à ajouter
GroupManagementUtils.initGroupsToAdd();

// Initialiser la gestion des groupes à supprimer
GroupManagementUtils.initGroupsToRemove(userGroups);

// Mettre à jour manuellement l'UI
GroupManagementUtils.updateSelectedUsersUI();
GroupManagementUtils.updateGroupsToAddDisplay();
GroupManagementUtils.updateGroupsToRemoveDisplay();

// Supprimer un groupe
GroupManagementUtils.removeAddGroup(0);
GroupManagementUtils.removeRemoveGroup(1);
```

### ValidationUtils

Module pour valider les formulaires et gérer les champs requis optionnels.

```javascript
const ValidationUtils = {
  initRequiredFieldOverrides: function(fieldIds) {
    // Initialise les overrides de champs requis
  },
  
  checkNameExists: function(url, data, resultDivId) {
    // Vérifie si un nom existe
  },
  
  normalizeFavvNatNr: function(input) {
    // Normalise un numéro de registre national
  },
  
  checkFavvNatNrExists: function(url, favvNatNr, ldapSource, resultDivId) {
    // Vérifie si un numéro de registre national existe
  },
  
  initClearResults: function(inputIds, resultDivId) {
    // Initialise les gestionnaires pour effacer les résultats
  }
};
```

#### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `initRequiredFieldOverrides(fieldIds)` | Initialise les overrides pour champs requis |
| `checkNameExists(url, data, resultDivId)` | Vérifie si un nom existe déjà |
| `normalizeFavvNatNr(input)` | Normalise un numéro de registre national |
| `checkFavvNatNrExists(url, favvNatNr, ldapSource, resultDivId)` | Vérifie si un numéro existe déjà |
| `initClearResults(inputIds, resultDivId)` | Efface les messages de validation |

#### Utilisation

```javascript
// Initialiser les overrides de champs requis
ValidationUtils.initRequiredFieldOverrides(['email', 'favvNatNr', 'manager']);

// Normaliser un champ de numéro de registre national
const input = document.getElementById('favvNatNr');
ValidationUtils.normalizeFavvNatNr(input);

// Vérifier si un nom existe déjà
ValidationUtils.checkNameExists(
  '/api/check_name_exists',
  { givenName: "John", sn: "Doe", ldap_source: "meta" },
  'nameCheckResult'
);

// Vérifier si un numéro de registre existe déjà
ValidationUtils.checkFavvNatNrExists(
  '/api/check_favvnatnr_exists',
  '12345678901',
  'meta',
  'favvNatNrCheckResult'
);

// Effacer les résultats de validation quand les champs changent
ValidationUtils.initClearResults(['givenName', 'sn'], 'nameCheckResult');
```

## Flux d'initialisation

Le flux d'initialisation de l'application suit les étapes suivantes :

1. Chargement de la bibliothèque via `app.js`
2. Vérification de l'option `LDAPManagerNoAutoInit`
3. Initialisation automatique si non désactivée via `LDAPManager.init()`
4. Détection des éléments de la page via `main-init.js`
5. Initialisation des composants spécifiques
6. Exécution des gestionnaires de compatibilité

```javascript
// Flux simplifié dans app.js
window.LDAPManager = {
  init: function(options = {}) {
    // Fusion des options
    const config = { ...defaultOptions, ...options };
    
    // Exécuter l'initialisation au chargement de la page
    $(document).ready(function() {
      // Récupérer la source LDAP
      const ldapSource = LDAPUtils.getCurrentSource();
      
      // Initialiser les fonctionnalités de base
      if (config.enhanceLinks) {
        LDAPUtils.enhanceLinks(ldapSource);
      }
      
      // Initialiser les autres fonctionnalités selon la configuration
      if (config.initDataTables) {
        initializeTables();
      }
      
      // Émettre un événement pour signaler l'initialisation terminée
      $(document).trigger('ldapmanager:initialized');
    });
  }
};

// Initialisation automatique sauf si désactivée
if (!window.LDAPManagerNoAutoInit) {
  window.LDAPManager.init({ debug: false });
}
```

## Fonctionnalités par page

### 1. Recherche d'utilisateurs (search.js)

- Autocomplétion du champ de recherche par nom complet
- Gestion des erreurs d'authentification
- Amélioration des liens avec source LDAP
- Filtrage et tri des groupes et rôles

### 2. Création d'utilisateur (user_creation.js)

- Affichage conditionnel des champs selon le type d'utilisateur
- Validation des champs obligatoires avec overrides
- Vérification de l'existence du nom et du numéro national
- Prévisualisation des détails utilisateur avant création
- Normalisation du numéro de registre national

### 3. Mise à jour d'utilisateur (update_user.js)

- Gestion des groupes à ajouter et supprimer
- Autocomplétion des champs (manager, service, groupes)
- Filtrage et tri des groupes existants

### 4. Ajout d'utilisateurs à un groupe (add_user_list_group.js)

- Sélection multiple d'utilisateurs
- Autocomplétion des noms d'utilisateurs
- Ajout en masse par numéros CN
- Gestion des tables de membres actuels

### 5. Gestion des utilisateurs d'un groupe (group_users.js)

- Tables DataTables pour afficher les membres
- Filtrage par service
- Navigation entre sources LDAP

### 6. Post-création d'utilisateur (post_creation.js)

- Ajout de groupes à l'utilisateur nouvellement créé
- Autocomplétion pour manager, groupe, service

## Compatibilité et transition

Le module `compatibility.js` fournit une couche de compatibilité pour faciliter la transition vers la nouvelle architecture.

### Fonctions de compatibilité

```javascript
// Exposition globale des fonctions de suppression de groupe
window.removeGroup = function(index) {
  if (typeof GroupManagementUtils !== 'undefined') {
    GroupManagementUtils.removeAddGroup(index);
  } else {
    console.error('GroupManagementUtils not available for removeGroup');
  }
};

// Définit une fonction qui s'exécute après l'initialisation
function addCompatibilityHandler(handler) {
  if (typeof handler === 'function') {
    compatibilityHandlers.push(handler);
  }
}

// Intégration avec les fonctions d'initialisation existantes
function initializeAutocomplete() {
  // Implémentation compatible
}
```

### Utilisation des handlers de compatibilité

```javascript
// Remplacer une fonction existante par celle de la bibliothèque
addCompatibilityHandler(function() {
  window.updateGroupsToAddDisplay = function() {
    GroupManagementUtils.updateGroupsToAddDisplay();
  };
});

// Compatibilité pour la gestion des sources LDAP
addCompatibilityHandler(function() {
  if (typeof window.currentLdapSource === 'undefined') {
    window.currentLdapSource = LDAPUtils.getCurrentSource();
  }
});
```

## Bonnes pratiques

### 1. Gestion de la source LDAP

Toujours utiliser `LDAPUtils.getCurrentSource()` pour obtenir la source LDAP actuelle :

```javascript
const ldapSource = LDAPUtils.getCurrentSource();
```

### 2. Initialisation d'éléments UI

Vérifier l'existence des éléments avant d'initialiser :

```javascript
if ($('#element_id').length > 0) {
  // Initialiser l'élément
}
```

### 3. Nettoyage avant réinitialisation

Détruire les instances existantes avant de les réinitialiser :

```javascript
// DataTables
if ($.fn.DataTable.isDataTable('#tableId')) {
  $('#tableId').DataTable().destroy();
}

// Autocomplete
if ($('#input_id').autocomplete('instance')) {
  $('#input_id').autocomplete('destroy');
}
```

### 4. Délégation d'événements

Utiliser la délégation pour les éléments dynamiques :

```javascript
$(document).on('click', '.add-user-btn', function() {
  // Traitement
});
```

### 5. Paramètres AJAX

Toujours inclure la source LDAP dans les requêtes AJAX :

```javascript
$.ajax({
  url: '/api/endpoint',
  method: 'POST',
  data: JSON.stringify({
    // Autres données
    ldap_source: LDAPUtils.getCurrentSource()
  }),
  // Autres options
});
```

### 6. Gestion des erreurs

Implémenter des gestionnaires d'erreurs pour les requêtes AJAX :

```javascript
$.ajax({
  // Options
  success: function(response) {
    // Traitement réussi
  },
  error: function(xhr, status, error) {
    console.error("Error:", error);
    // Afficher un message à l'utilisateur
  },
  complete: function() {
    // Nettoyage
  }
});
```

### 7. Performance des tables

Optimiser les options DataTables selon les besoins :

```javascript
const tableOptions = {
  responsive: true,
  paging: true,
  pageLength: window.innerHeight < 800 ? 5 : 10, // Adapter au viewport
  deferRender: true, // Pour les grandes tables
  // Autres options
};
```