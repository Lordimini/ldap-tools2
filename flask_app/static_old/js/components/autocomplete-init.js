/**
 * Utilitaires pour l'initialisation des fonctionnalités d'autocomplétion
 */
const AutocompleteUtils = {
    /**
     * Initialise l'autocomplétion pour la recherche par nom complet
     * @param {string} inputSelector - Sélecteur jQuery pour l'input
     * @param {string} sourceUrl - URL pour récupérer les données d'autocomplétion
     * @param {string} ldapSource - Source LDAP actuelle
     */
    initFullNameAutocomplete: function(inputSelector, sourceUrl, ldapSource) {
      const inputElement = $(inputSelector);
      if (inputElement.length === 0 || !inputElement.autocomplete) return;
      
      inputElement.autocomplete({
        source: function(request, response) {
          // Ne déclencher la recherche que si au moins 3 caractères sont saisis
          if (request.term.length < 3) {
            response([]);
            return;
          }
          
          // Ajouter une variable pour stocker la requête AJAX en cours
          if (this.xhr) {
            this.xhr.abort();
          }
          
          // Effectuer la requête AJAX avec un délai
          this.xhr = $.getJSON(sourceUrl, {
            term: request.term,
            source: ldapSource
          }, function(data) {
            response(data);
          });
        },
        minLength: 3,  // Définir une longueur minimale avant de déclencher l'autocomplétion
        delay: 300,    // Ajouter un délai de 300ms entre les frappes et la recherche
        select: function(event, ui) {
          inputElement.val(ui.item.value);
          return false;
        }
      }).data('ui-autocomplete')._renderItem = function(ul, item) {
        return $('<li>')
          .append(`<div>${item.label}</div>`)
          .appendTo(ul);
      };
    },
    
    /**
     * Initialise l'autocomplétion pour la recherche de groupes
     * @param {string} inputSelector - Sélecteur jQuery pour l'input
     * @param {string} sourceUrl - URL pour récupérer les données d'autocomplétion
     * @param {string} ldapSource - Source LDAP actuelle
     * @param {function} onSelect - Fonction appelée à la sélection (facultatif)
     */
    initGroupAutocomplete: function(inputSelector, sourceUrl, ldapSource, onSelect) {
      const inputElement = $(inputSelector);
      if (inputElement.length === 0 || !inputElement.autocomplete) return;
      
      inputElement.autocomplete({
        source: function(request, response) {
          $.getJSON(sourceUrl, {
            term: request.term,
            source: ldapSource
          }, function(data) {
            response(data);
          });
        },
        select: function(event, ui) {
          // Set the visible value (CN)
          inputElement.val(ui.item.value);
          
          // Store the complete DN if available
          const dnMatch = ui.item.label.match(/\((.*?)\)$/);
          if (dnMatch && dnMatch[1]) {
            $('#group_dn').val(dnMatch[1]);
          }
          
          // Appeler la fonction de callback si fournie
          if (typeof onSelect === 'function') {
            onSelect(ui.item);
          }
          
          return false;
        },
        minLength: 2
      }).data('ui-autocomplete')._renderItem = function(ul, item) {
        return $('<li>')
          .append(`<div>${item.label}</div>`)
          .appendTo(ul);
      };
    },
    
    /**
     * Initialise l'autocomplétion pour la recherche de managers
     * @param {string} inputSelector - Sélecteur jQuery pour l'input
     * @param {string} sourceUrl - URL pour récupérer les données d'autocomplétion
     * @param {string} ldapSource - Source LDAP actuelle
     * @param {string} dnFieldSelector - Sélecteur pour le champ caché qui stocke le DN (facultatif)
     */
    initManagerAutocomplete: function(inputSelector, sourceUrl, ldapSource, dnFieldSelector = '#manager_dn') {
      const inputElement = $(inputSelector);
      if (inputElement.length === 0 || !inputElement.autocomplete) return;
      
      inputElement.autocomplete({
        source: function(request, response) {
          $.getJSON(sourceUrl, {
            term: request.term,
            source: ldapSource
          }, function(data) {
            response(data);
          });
        },
        select: function(event, ui) {
          inputElement.val(ui.item.value);
          
          // Extract DN from label (format is "fullName - email - title (DN)")
          const dnMatch = ui.item.label.match(/\((.*?)\)$/);
          if (dnMatch && dnMatch[1]) {
            $(dnFieldSelector).val(dnMatch[1]);
          }
          
          return false;
        },
        minLength: 2
      }).data('ui-autocomplete')._renderItem = function(ul, item) {
        return $('<li>')
          .append(`<div>${item.label}</div>`)
          .appendTo(ul);
      };
    },
    
    /**
     * Initialise l'autocomplétion pour la recherche de services (OU)
     * @param {string} inputSelector - Sélecteur jQuery pour l'input
     * @param {string} sourceUrl - URL pour récupérer les données d'autocomplétion
     * @param {string} ldapSource - Source LDAP actuelle
     */
    initServiceAutocomplete: function(inputSelector, sourceUrl, ldapSource) {
      const inputElement = $(inputSelector);
      if (inputElement.length === 0 || !inputElement.autocomplete) return;
      
      inputElement.autocomplete({
        source: function(request, response) {
          $.getJSON(sourceUrl, {
            term: request.term,
            source: ldapSource
          }, function(data) {
            response(data);
          });
        },
        select: function(event, ui) {
          inputElement.val(ui.item.value);
          return false;
        },
        minLength: 2
      }).data('ui-autocomplete')._renderItem = function(ul, item) {
        return $('<li>')
          .append(`<div>${item.label}</div>`)
          .appendTo(ul);
      };
    },
    
    /**
     * Initialise l'autocomplétion pour la recherche de rôles
     * @param {string} inputSelector - Sélecteur jQuery pour l'input
     * @param {string} sourceUrl - URL pour récupérer les données d'autocomplétion
     * @param {string} ldapSource - Source LDAP actuelle
     */
    initRoleAutocomplete: function(inputSelector, sourceUrl, ldapSource) {
      const inputElement = $(inputSelector);
      if (inputElement.length === 0 || !inputElement.autocomplete) return;
      
      inputElement.autocomplete({
        source: function(request, response) {
          $.getJSON(sourceUrl, {
            term: request.term,
            source: ldapSource
          }, function(data) {
            response(data);
          });
        },
        select: function(event, ui) {
          inputElement.val(ui.item.value);
          return false;
        },
        minLength: 2
      }).data('ui-autocomplete')._renderItem = function(ul, item) {
        return $('<li>')
          .append(`<div>${item.label}</div>`)
          .appendTo(ul);
      };
    },
    
    /**
     * Initialise l'autocomplétion en fonction du type de recherche sélectionné
     * @param {string} searchTypeSelector - Sélecteur pour le type de recherche
     * @param {string} searchTermSelector - Sélecteur pour le terme de recherche
     * @param {string} fullNameUrl - URL pour l'autocomplétion par nom complet
     * @param {string} ldapSource - Source LDAP actuelle
     */
    initSearchTypeAutocomplete: function(searchTypeSelector, searchTermSelector, fullNameUrl, ldapSource) {
      const searchTypeInput = $(searchTypeSelector);
      const searchTermInput = $(searchTermSelector);
      
      if (searchTypeInput.length === 0 || searchTermInput.length === 0) return;
      
      const initializeAutocomplete = () => {
        // Détruire l'autocomplétion existante si présente
        if (searchTermInput.autocomplete) {
          searchTermInput.autocomplete('destroy');
        }
        
        // Initialiser l'autocomplétion seulement pour le type fullName
        if (searchTypeInput.val() === 'fullName') {
          this.initFullNameAutocomplete(searchTermSelector, fullNameUrl, ldapSource);
        }
      };
      
      // Initialiser au chargement
      initializeAutocomplete();
      
      // Réinitialiser lorsque le type de recherche change
      searchTypeInput.on('change', initializeAutocomplete);
    }
  };