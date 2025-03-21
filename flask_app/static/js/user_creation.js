/**
 * Script de création d'utilisateur pour LDAP Manager
 * Ce script utilise les modules de l'architecture modulaire pour initialiser les fonctionnalités
 */

// Désactiver l'initialisation automatique pour contrôler l'ordre d'initialisation
window.LDAPManagerNoAutoInit = true;

document.addEventListener('DOMContentLoaded', function() {
  console.log('Initializing user creation page...');
  
  // Initialiser LDAPManager avec des options spécifiques
  if (typeof LDAPManager !== 'undefined') {
    LDAPManager.init({
      debug: false,           // Activer si nécessaire pendant le développement
      enhanceLinks: true,
      enhanceForms: true,
      initDataTables: false,  // Pas de tables dans la page de création d'utilisateur
      initAutocomplete: true, // Nécessaire pour l'autocomplétion du manager
      initGroupManagement: false // Pas de gestion de groupe à ce stade
    });
    
    // Enregistrer UserCreationUtils dans LDAPManager si disponible
    if (typeof LDAPManager.registerUtil === 'function' && typeof UserCreationUtils !== 'undefined') {
      LDAPManager.registerUtil('userCreation', UserCreationUtils);
    }
  } else {
    console.error('LDAPManager not defined! Check script loading order.');
  }
  
  // Initialiser le module de validation avec les champs qui peuvent avoir des overrides
  if (typeof ValidationUtils !== 'undefined') {
    ValidationUtils.initRequiredFieldOverrides(['email', 'favvNatNr', 'manager']);
    
    // Initialisation pour les vérifications de nom et de registre national
    if (document.getElementById('checkNameBtn') && window.checkNameExistsUrl) {
      document.getElementById('checkNameBtn').addEventListener('click', function() {
        const givenName = document.getElementById('givenName').value.trim();
        const sn = document.getElementById('sn').value.trim();
        
        ValidationUtils.checkNameExists(
          window.checkNameExistsUrl,
          {
            givenName: givenName,
            sn: sn,
            ldap_source: LDAPUtils.getCurrentSource()
          },
          'nameCheckResult'
        );
      });
      
      // Initialiser l'effacement des résultats de vérification
      ValidationUtils.initClearResults(['givenName', 'sn'], 'nameCheckResult');
    }
    
    if (document.getElementById('checkFavvNatNrBtn') && window.checkFavvNatNrExistsUrl) {
      document.getElementById('checkFavvNatNrBtn').addEventListener('click', function() {
        const favvNatNr = document.getElementById('favvNatNr').value.trim();
        ValidationUtils.checkFavvNatNrExists(
          window.checkFavvNatNrExistsUrl,
          favvNatNr,
          LDAPUtils.getCurrentSource(),
          'favvNatNrCheckResult'
        );
      });
    }
  } else {
    console.error('ValidationUtils not defined! Check script loading order.');
  }
  
  // Initialiser les fonctionnalités spécifiques à la création d'utilisateur
  if (typeof UserCreationUtils !== 'undefined') {
    UserCreationUtils.init();
  } else {
    console.error('UserCreationUtils not defined! Check script loading order.');
  }
  
  // Gestionnaire global d'erreurs pour le débogage
  window.addEventListener('error', function(event) {
    console.error('Global error caught:', event.error);
  });
  
  console.log('User creation page initialization complete');
});