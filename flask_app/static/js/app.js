/**
 * Point d'entrée principal de l'application LDAP Manager
 * Ce fichier importe et initialise tous les modules nécessaires
 * 
 * Pour utiliser cette bibliothèque, il suffit d'inclure app.js dans votre page :
 * <script src="/static/js/app.js"></script>
 */

// Définir une fonction d'initialisation globale
window.LDAPManager = {
    /**
     * Initialise l'application LDAP Manager avec des options personnalisées
     * @param {Object} options - Options d'initialisation
     */
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
      
      // Fusionner les options personnalisées avec les options par défaut
      const config = { ...defaultOptions, ...options };
      
      // Activer le mode debug si nécessaire
      if (config.debug) {
        console.log('LDAP Manager: Debug mode enabled');
        console.log('LDAP Manager: Configuration', config);
      }
      
      // Exécuter l'initialisation au chargement de la page
      $(document).ready(function() {
        // Récupérer la source LDAP
        const ldapSource = LDAPUtils.getCurrentSource();
        
        if (config.debug) {
          console.log(`LDAP Manager: Current LDAP source: ${ldapSource}`);
        }
        
        // Initialiser les fonctionnalités de base
        if (config.enhanceLinks) {
          LDAPUtils.enhanceLinks(ldapSource);
        }
        
        if (config.enhanceForms) {
          LDAPUtils.enhanceForms(ldapSource);
        }
        
        // Initialiser les boutons de rafraîchissement
        LDAPUtils.setupRefreshButton();
        
        // Initialiser les autres fonctionnalités selon la configuration
        if (config.initDataTables) {
          initializeTables();
        }
        
        if (config.initAutocomplete) {
          initializeAutocomplete(ldapSource);
        }
        
        if (config.initGroupManagement) {
          initializeGroupManagement(ldapSource);
        }
        
        // Initialiser toujours les validations et les tris/filtres
        initializeValidations(ldapSource);
        initializeSortAndFilter();
        
        if (config.debug) {
          console.log('LDAP Manager: Initialization complete');
        }
        
        // Émettre un événement pour signaler que l'initialisation est terminée
        $(document).trigger('ldapmanager:initialized');
      });
    },
    
    /**
     * Réinitialise une fonctionnalité spécifique
     * @param {string} feature - Nom de la fonctionnalité à réinitialiser
     * @param {Object} options - Options supplémentaires
     */
    reinitialize: function(feature, options = {}) {
      const ldapSource = LDAPUtils.getCurrentSource();
      
      switch (feature) {
        case 'tables':
          initializeTables();
          break;
        case 'autocomplete':
          initializeAutocomplete(ldapSource);
          break;
        case 'groupManagement':
          initializeGroupManagement(ldapSource);
          break;
        case 'validation':
          initializeValidations(ldapSource);
          break;
        case 'sortAndFilter':
          initializeSortAndFilter();
          break;
        case 'all':
          initializeTables();
          initializeAutocomplete(ldapSource);
          initializeGroupManagement(ldapSource);
          initializeValidations(ldapSource);
          initializeSortAndFilter();
          break;
        default:
          console.error(`LDAP Manager: Unknown feature "${feature}"`);
      }
    },
    
    /**
     * Accès aux utilitaires pour une utilisation avancée
     */
    utils: {
      ldap: LDAPUtils,
      dataTables: DataTableUtils,
      autocomplete: AutocompleteUtils,
      groupManagement: GroupManagementUtils,
      validation: ValidationUtils
    }
  };
  
  // Initialiser automatiquement l'application avec les paramètres par défaut
  // Ce comportement peut être désactivé en définissant window.LDAPManagerNoAutoInit = true
  // avant le chargement de ce script
  if (!window.LDAPManagerNoAutoInit) {
    window.LDAPManager.init({
      debug: false
    });
  }