/**
 * Module de compatibilité pour assurer la transition en douceur vers la nouvelle bibliothèque
 * Ce fichier fournit des fonctions de compatibilité pour le code existant qui n'a pas
 * encore été migré vers la nouvelle structure. Ces fonctions seront progressivement
 * supprimées au fur et à mesure que le code est migré.
 */

/**
 * Exposition globale des fonctions de suppression de groupe pour la compatibilité
 * avec les gestionnaires d'événements onclick définis dans le HTML
 */
window.removeGroup = function(index) {
    if (typeof GroupManagementUtils !== 'undefined') {
      GroupManagementUtils.removeAddGroup(index);
    } else {
      console.error('GroupManagementUtils not available for removeGroup');
    }
  };
  
  window.removeAddGroup = function(index) {
    if (typeof GroupManagementUtils !== 'undefined') {
      GroupManagementUtils.removeAddGroup(index);
    } else {
      console.error('GroupManagementUtils not available for removeAddGroup');
    }
  };
  
  window.removeRemoveGroup = function(index) {
    if (typeof GroupManagementUtils !== 'undefined') {
      GroupManagementUtils.removeRemoveGroup(index);
    } else {
      console.error('GroupManagementUtils not available for removeRemoveGroup');
    }
  };
  
  /**
   * Définit une fonction de compatibilité qui s'exécute après l'initialisation de la bibliothèque
   * Utilisation: addCompatibilityHandler(function() { ... votre code ... });
   */
  let compatibilityHandlers = [];
  
  function addCompatibilityHandler(handler) {
    if (typeof handler === 'function') {
      compatibilityHandlers.push(handler);
    }
  }
  
  // Exécuter les gestionnaires de compatibilité après l'initialisation de la page
  $(document).ready(function() {
    // Attendre un bref délai pour s'assurer que tous les autres scripts sont chargés
    setTimeout(function() {
      compatibilityHandlers.forEach(function(handler) {
        try {
          handler();
        } catch (error) {
          console.error('Error in compatibility handler:', error);
        }
      });
      console.log('LDAP Manager: Compatibility handlers executed');
    }, 100);
  });
  
  /**
   * Intégration avec les fonctions d'initialisation d'autocomplétion existantes
   * Cela permet au code existant appelant ces fonctions de continuer à fonctionner
   */
  function initializeAutocomplete() {
    const searchTypeInput = $('#search_type');
    const searchTermInput = $('#search_term');
    const ldapSource = LDAPUtils.getCurrentSource();
    
    if (searchTypeInput.length > 0 && searchTermInput.length > 0 && searchTermInput.autocomplete) {
      if (searchTypeInput.val() === 'fullName' && window.autocompleteFullNameUrl) {
        AutocompleteUtils.initFullNameAutocomplete('#search_term', window.autocompleteFullNameUrl, ldapSource);
      } else if (searchTermInput.autocomplete('instance')) {
        // Détruire l'instance existante si le type n'est pas fullName
        searchTermInput.autocomplete('destroy');
      }
    }
  }
  
  // Compatibilité pour les fonctions d'initialisation des tables
  if (typeof $.fn.DataTable !== 'undefined') {
    addCompatibilityHandler(function() {
      // Si une table a déjà été initialisée par le code existant, s'assurer qu'elle
      // bénéficie des améliorations de style de DataTableUtils
      DataTableUtils.enhanceDataTableStyle();
    });
  }
  
  /**
   * Fonctions de compatibilité pour gérer la transition des fonctionnalités
   * spécifiques à la page
   */
  
  // Compatibilité pour add_user_list_group.js
  if ($('#selected_users_list').length > 0 && !window.initialSelectedUsers) {
    window.initialSelectedUsers = [];
  }
  
  // Compatibilité pour update_user.js
  if ($('#groups_to_add').length > 0 && typeof window.updateGroupsToAddDisplay === 'function') {
    addCompatibilityHandler(function() {
      // Remplacer la fonction existante par celle de la bibliothèque
      window.updateGroupsToAddDisplay = function() {
        GroupManagementUtils.updateGroupsToAddDisplay();
      };
    });
  }
  
  // Compatibilité pour la gestion des sources LDAP
  addCompatibilityHandler(function() {
    // Vérifier si un code spécifique à une page a besoin d'accéder à la source LDAP
    if (typeof window.currentLdapSource === 'undefined') {
      window.currentLdapSource = LDAPUtils.getCurrentSource();
    }
  });