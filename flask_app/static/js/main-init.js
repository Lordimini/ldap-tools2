/**
 * Script d'initialisation principal pour l'application LDAP Manager
 * Ce script détecte les éléments présents sur la page et initialise les fonctionnalités appropriées
 */
$(document).ready(function() {
    console.log('LDAP Manager: Initializing application...');
    
    // Récupérer la source LDAP courante
    const ldapSource = LDAPUtils.getCurrentSource();
    console.log(`LDAP Manager: Current LDAP source: ${ldapSource}`);
    
    // Initialiser les utilitaires LDAP
    LDAPUtils.init();
    
    // Détecter et initialiser les composants de page spécifiques
    initializePageComponents(ldapSource);
  });
  
  /**
   * Détecte et initialise les composants spécifiques à la page actuelle
   * @param {string} ldapSource - Source LDAP actuelle
   */
  function initializePageComponents(ldapSource) {
    // Initialiser les tables DataTables si présentes
    initializeTables();
    
    // Initialiser les fonctionnalités d'autocomplétion
    initializeAutocomplete(ldapSource);
    
    // Initialiser la gestion des groupes si nécessaire
    initializeGroupManagement(ldapSource);
    
    // Ajouter d'autres initialisations de composants au besoin
    initializeSortAndFilter();
    
    // Initialiser les validations de formulaire si nécessaire
    initializeValidations(ldapSource);
  }
  
  /**
   * Initialise toutes les tables DataTables présentes sur la page
   */
  /**
 * Initialise toutes les tables DataTables présentes sur la page
 */
function initializeTables() {
  // Table des utilisateurs
  if ($('#usersTable').length > 0) {
    // Déterminer si nous sommes dans la page view_role
    // en vérifiant si window.searchUserUrl est défini
    const isViewRolePage = typeof window.searchUserUrl !== 'undefined';
    
    // Récupérer la source LDAP
    const ldapSource = LDAPUtils.getCurrentSource();
    
    let userTable;
    
    if (isViewRolePage) {
      // Si nous sommes dans la page view_role, activer les lignes cliquables
      userTable = DataTableUtils.initUserTable('#usersTable', {}, {
        urlBase: window.searchUserUrl,
        dataAttribute: 'cn',
        ldapSource: ldapSource
      });
      console.log('LDAP Manager: Users table initialized with clickable rows');
    } else {
      // Initialisation standard pour les autres pages
      userTable = DataTableUtils.initUserTable('#usersTable');
    }
    
    // Ajouter un filtre par service si présent
    if ($('#serviceFilter').length > 0) {
      DataTableUtils.setupColumnFilter(userTable, '#serviceFilter', 3);
    }
    
    console.log('LDAP Manager: Users table initialized');
  }
  
  // Table des groupes
  if ($('#groupsTable').length > 0) {
    DataTableUtils.initGroupTable('#groupsTable');
    console.log('LDAP Manager: Groups table initialized');
  }
  
  // Table des utilisateurs actuels d'un groupe
  if ($('#currentMembersTable').length > 0) {
    DataTableUtils.initGenericTable('#currentMembersTable', {
      responsive: true,
      paging: true,
      pageLength: 5,
      lengthMenu: [[5, 10, 25, -1], [5, 10, 25, "All"]],
      searching: true,
      info: true,
      order: [[1, 'asc']], // Tri par défaut par nom complet
      language: {
        search: "",
        searchPlaceholder: "Search members...",
        zeroRecords: "No matching records found",
        info: "Showing _START_ to _END_ of _TOTAL_ members",
        infoEmpty: "No members found",
        infoFiltered: "(filtered from _MAX_ total members)"
      }
    });
    console.log('LDAP Manager: Current members table initialized');
  }
  
  // Table des rôles
  if ($('#rolesTable').length > 0) {
    DataTableUtils.initGenericTable('#rolesTable', {
      paging: false,
      searching: true,
      info: false,
      order: [[0, 'asc']]
    });
    console.log('LDAP Manager: Roles table initialized');
  }
  
  // Table des conteneurs
  if ($('#containersTable').length > 0) {
    DataTableUtils.initGenericTable('#containersTable', {
      paging: false,
      searching: true,
      info: false,
      order: [[0, 'asc']]
    });
    console.log('LDAP Manager: Containers table initialized');
  }
}
  
  /**
   * Initialise les fonctionnalités d'autocomplétion sur la page
   * @param {string} ldapSource - Source LDAP actuelle
   */
  function initializeAutocomplete(ldapSource) {
    // Autocomplétion du champ de recherche par type
    if ($('#search_type').length > 0 && $('#search_term').length > 0 && window.autocompleteFullNameUrl) {
      AutocompleteUtils.initSearchTypeAutocomplete('#search_type', '#search_term', window.autocompleteFullNameUrl, ldapSource);
      console.log('LDAP Manager: Search type autocomplete initialized');
    }
    
    // Autocomplétion des groupes
    if ($('#group_name').length > 0 && window.autocompleteGroupsUrl) {
      AutocompleteUtils.initGroupAutocomplete('#group_name', window.autocompleteGroupsUrl, ldapSource);
      console.log('LDAP Manager: Group name autocomplete initialized');
    }
    
    // Autocomplétion des managers
    if ($('#hierarchical_manager').length > 0 && window.autocompleteManagersUrl) {
      AutocompleteUtils.initManagerAutocomplete('#hierarchical_manager', window.autocompleteManagersUrl, ldapSource);
      console.log('LDAP Manager: Manager autocomplete initialized');
    }
    
    // Autocomplétion des services
    if ($('#ou').length > 0 && window.autocompleteServicesUrl) {
      AutocompleteUtils.initServiceAutocomplete('#ou', window.autocompleteServicesUrl, ldapSource);
      console.log('LDAP Manager: Service (OU) autocomplete initialized');
    }
    
    // Autocomplétion des rôles
    if ($('#role_cn').length > 0 && window.autocompleteRolesUrl) {
      AutocompleteUtils.initRoleAutocomplete('#role_cn', window.autocompleteRolesUrl, ldapSource);
      console.log('LDAP Manager: Role autocomplete initialized');
    }
    
    // Autocomplétion des noms de service
    if ($('#service_name').length > 0 && window.autocompleteServicesUrl) {
      AutocompleteUtils.initServiceAutocomplete('#service_name', window.autocompleteServicesUrl, ldapSource);
      console.log('LDAP Manager: Service name autocomplete initialized');
    }
  }
  
  /**
   * Initialise la gestion des groupes si les éléments nécessaires sont présents
   * @param {string} ldapSource - Source LDAP actuelle
   */
  function initializeGroupManagement(ldapSource) {
    // Initialisation de la sélection des utilisateurs pour l'ajout à un groupe
    if ($('#selected_users_list').length > 0) {
      const initialUsers = window.initialSelectedUsers || [];
      GroupManagementUtils.initUserSelection(initialUsers);
      console.log('LDAP Manager: User selection for group initialized');
    }
    
    // Initialisation des groupes à ajouter
    if ($('#selected_groups').length > 0) {
      GroupManagementUtils.initGroupsToAdd();
      console.log('LDAP Manager: Groups to add initialized');
    }
    
    // Initialisation des groupes à supprimer
    if ($('#groups_to_remove').length > 0) {
      GroupManagementUtils.initGroupsToRemove(window.userGroups || []);
      console.log('LDAP Manager: Groups to remove initialized');
    }
  }
  
  /**
   * Initialise les fonctionnalités de tri et de filtrage
   */
  function initializeSortAndFilter() {
    // Vérifier si les éléments de filtrage et de tri sont présents
    if (($('#group-filter').length > 0 || $('#role-filter').length > 0) &&
        ($('#sort-groups').length > 0 || $('#sort-roles').length > 0)) {
      GroupManagementUtils.initSortAndFilter();
      console.log('LDAP Manager: Sort and filter initialized');
    }
  }
  
  /**
   * Initialise les validations de formulaire
   * @param {string} ldapSource - Source LDAP actuelle
   */
  function initializeValidations(ldapSource) {
    // Initialiser les overrides de champs requis si présents
    const overrideFields = [];
    
    if ($('#email').length > 0 && $('#emailOverrideBtn').length > 0) {
      overrideFields.push('email');
    }
    
    if ($('#favvNatNr').length > 0 && $('#favvNatNrOverrideBtn').length > 0) {
      overrideFields.push('favvNatNr');
      
      // Initialiser la normalisation du numéro de registre national
      ValidationUtils.normalizeFavvNatNr(document.getElementById('favvNatNr'));
      
      // Initialiser la vérification du numéro de registre national
      if ($('#checkFavvNatNrBtn').length > 0 && window.checkFavvNatNrExistsUrl) {
        $('#checkFavvNatNrBtn').click(function() {
          const favvNatNr = $('#favvNatNr').val()?.trim() || '';
          ValidationUtils.checkFavvNatNrExists(
            window.checkFavvNatNrExistsUrl,
            favvNatNr,
            ldapSource,
            'favvNatNrCheckResult'
          );
        });
      }
    }
    
    if ($('#manager').length > 0 && $('#managerOverrideBtn').length > 0) {
      overrideFields.push('manager');
    }
    
    if (overrideFields.length > 0) {
      ValidationUtils.initRequiredFieldOverrides(overrideFields);
      console.log('LDAP Manager: Required field overrides initialized');
    }
    
    // Initialiser la vérification du nom si présente
    if ($('#checkNameBtn').length > 0 && window.checkNameExistsUrl) {
      $('#checkNameBtn').click(function() {
        const givenName = $('#givenName').val()?.trim() || '';
        const sn = $('#sn').val()?.trim() || '';
        
        ValidationUtils.checkNameExists(
          window.checkNameExistsUrl,
          {
            givenName: givenName,
            sn: sn,
            ldap_source: ldapSource
          },
          'nameCheckResult'
        );
      });
      
      // Initialiser l'effacement des résultats de vérification
      ValidationUtils.initClearResults(['givenName', 'sn'], 'nameCheckResult');
      
      console.log('LDAP Manager: Name check initialized');
    }
    
    // Attacher validateur au formulaire de création d'utilisateur
    if ($('#userCreationForm').length > 0) {
      // Cette fonction est définie dans user_creation.js
      if (typeof validateForm === 'function') {
        $('#userCreationForm').on('submit', validateForm);
        console.log('LDAP Manager: User creation form validation initialized');
      }
    }
  }

  /**
 * Fonction d'initialisation pour les pages de création d'utilisateur
 * Cette fonction doit être ajoutée au fichier main-init.js
 */
function initializeUserCreation() {
  // Vérifier si nous sommes sur la page de création d'utilisateur
  if (document.getElementById('userCreationForm')) {
    console.log('LDAP Manager: Initializing user creation functionality');
    
    // Initialiser les validations avec les champs qui peuvent avoir des overrides
    ValidationUtils.initRequiredFieldOverrides(['email', 'favvNatNr', 'manager']);
    
    // Initialiser les fonctionnalités spécifiques à la création d'utilisateur
    if (typeof UserCreationUtils !== 'undefined') {
      UserCreationUtils.init();
    } else {
      console.error('LDAP Manager: UserCreationUtils module not available');
    }
  }
}

/**
 * Ajout à la fonction initializePageComponents dans main-init.js
 * Ajouter cette ligne après les autres initialisations :
 * 
 * // Initialiser la création d'utilisateur si nécessaire
 * initializeUserCreation();
 */