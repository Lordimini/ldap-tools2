/**
 * Script de création d'utilisateur pour LDAP Manager
 * Ce script utilise les modules de l'architecture modulaire pour initialiser les fonctionnalités
 * 
 * Ce fichier est conçu pour remplacer l'ancien user_creation.js dans un souci de maintenabilité
 * et de compatibilité avec l'architecture modulaire existante.
 */

// Désactiver l'initialisation automatique pour contrôler l'ordre d'initialisation
window.LDAPManagerNoAutoInit = true;

document.addEventListener('DOMContentLoaded', function() {
  console.log('Initializing user creation page...');
  
  // Initialiser LDAPManager avec des options spécifiques
  LDAPManager.init({
    debug: false,           // Activer si nécessaire pendant le développement
    enhanceLinks: true,
    enhanceForms: true,
    initDataTables: false,  // Pas de tables dans la page de création d'utilisateur
    initAutocomplete: true, // Nécessaire pour l'autocomplétion du manager
    initGroupManagement: false // Pas de gestion de groupe à ce stade
  });
  
  // Initialiser le module de validation avec les champs qui peuvent avoir des overrides
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
    
    // Initialiser la normalisation du numéro de registre national
    const favvNatNrInput = document.getElementById('favvNatNr');
    if (favvNatNrInput) {
      ValidationUtils.normalizeFavvNatNr(favvNatNrInput);
    }
  }
  
  // Initialiser les fonctionnalités spécifiques à la création d'utilisateur
  UserCreationUtils.init();
  
  console.log('User creation page initialization complete');
});