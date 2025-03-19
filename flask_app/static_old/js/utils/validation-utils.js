/**
 * Utilitaires pour la validation des formulaires
 */
const ValidationUtils = {
    /**
     * Initialise les overrides de champs requis
     * @param {Array} fieldIds - Liste des IDs des champs qui peuvent avoir des overrides
     */
    initRequiredFieldOverrides: function(fieldIds) {
      // Fonctions pour gérer l'état des overrides
      const updateOverrideUI = (fieldId, overrideActive) => {
        const field = document.getElementById(fieldId);
        const overrideBtn = document.getElementById(fieldId + 'OverrideBtn');
        const overrideIndicator = document.getElementById(fieldId + 'OverrideIndicator');
        const overrideInput = document.getElementById(fieldId + '_override');
        
        if (!field || !overrideBtn || !overrideIndicator || !overrideInput) return;
        
        // Mettre à jour l'indicateur d'override
        if (overrideActive) {
          field.required = false;
          overrideIndicator.style.display = 'block';
          overrideBtn.classList.remove('btn-warning');
          overrideBtn.classList.add('btn-danger');
          overrideBtn.innerHTML = '<i class="fas fa-times-circle"></i> Annuler Override';
          overrideInput.value = 'true';
        } else {
          field.required = true;
          overrideIndicator.style.display = 'none';
          overrideBtn.classList.remove('btn-danger');
          overrideBtn.classList.add('btn-warning');
          overrideBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Override';
          overrideInput.value = 'false';
        }
      };
      
      // Fonction pour préparer les modales selon l'état d'override
      const prepareOverrideModal = (fieldId, modalId) => {
        const modal = document.getElementById(modalId);
        const modalBody = document.getElementById(fieldId + 'ModalBody');
        const modalFooter = document.getElementById(fieldId + 'ModalFooter');
        const overrideInput = document.getElementById(fieldId + '_override');
        
        if (!modal || !modalBody || !modalFooter || !overrideInput) return;
        
        const overrideActive = overrideInput.value === 'true';
        
        if (overrideActive) {
          // Si l'override est actif, montrer option pour le désactiver
          modalBody.innerHTML = `
            <p><strong>Override Actif</strong></p>
            <p>Le champ '${fieldId}' est actuellement optionnel. Voulez-vous le rendre à nouveau obligatoire?</p>
          `;
          modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
            <button type="button" class="btn btn-success" id="disable${fieldId.charAt(0).toUpperCase() + fieldId.slice(1)}Override">Rendre obligatoire</button>
          `;
          
          // Ajouter event listener pour désactiver l'override
          const disableBtn = document.getElementById(`disable${fieldId.charAt(0).toUpperCase() + fieldId.slice(1)}Override`);
          if (disableBtn) {
            disableBtn.addEventListener('click', function() {
              updateOverrideUI(fieldId, false);
              if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                bootstrap.Modal.getInstance(modal)?.hide();
              }
            });
          }
        } else {
          // Si l'override n'est pas actif, montrer avertissement normal
          modalBody.innerHTML = `
            <p><strong>Attention, à vos risques et périls!</strong></p>
            <p>Rendre ce champ optionnel n'est pas recommandé. Êtes-vous sûr de vouloir continuer?</p>
          `;
          modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
            <button type="button" class="btn btn-danger" id="confirm${fieldId.charAt(0).toUpperCase() + fieldId.slice(1)}Override">Confirmer</button>
          `;
          
          // Ajouter event listener pour activer l'override
          const confirmBtn = document.getElementById(`confirm${fieldId.charAt(0).toUpperCase() + fieldId.slice(1)}Override`);
          if (confirmBtn) {
            confirmBtn.addEventListener('click', function() {
              updateOverrideUI(fieldId, true);
              if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                bootstrap.Modal.getInstance(modal)?.hide();
              }
            });
          }
        }
      };
      
      // Attacher les gestionnaires d'événements pour chaque champ
      fieldIds.forEach(fieldId => {
        const overrideBtn = document.getElementById(fieldId + 'OverrideBtn');
        if (overrideBtn) {
          overrideBtn.addEventListener('click', function() {
            prepareOverrideModal(fieldId, fieldId + 'WarningModal');
          });
        }
        
        // Initialiser l'UI basée sur les valeurs stockées
        const overrideInput = document.getElementById(fieldId + '_override');
        if (overrideInput && overrideInput.value === 'true') {
          updateOverrideUI(fieldId, true);
        }
      });
    },
    
    /**
     * Effectue une requête AJAX pour vérifier si un nom existe
     * @param {string} url - URL pour la vérification
     * @param {Object} data - Données à envoyer
     * @param {string} resultDivId - ID de l'élément pour afficher le résultat
     */
    checkNameExists: function(url, data, resultDivId) {
      const resultDiv = document.getElementById(resultDivId);
      
      if (!resultDiv) return;
      
      // Valider les données
      if (!data.givenName || !data.sn) {
        resultDiv.innerHTML = '<div class="alert alert-warning">Veuillez saisir le prénom et le nom.</div>';
        return;
      }
      
      // Afficher un indicateur de chargement
      resultDiv.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Vérification en cours...</div>';
      
      // Envoyer la requête AJAX
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'exists') {
          // Afficher sn + givenName (au lieu de givenName + sn) pour être cohérent avec le format LDAP
          resultDiv.innerHTML = `<div class="alert alert-danger">Un utilisateur avec le nom '${data.message}' existe déjà dans l'annuaire.</div>`;
        } else if (data.status === 'ok') {
          resultDiv.innerHTML = `<div class="alert alert-success">Aucun utilisateur existant avec ce nom.</div>`;
        } else {
          resultDiv.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
        }
      })
      .catch(error => {
        console.error('Error:', error);
        resultDiv.innerHTML = '<div class="alert alert-danger">Erreur lors de la vérification. Veuillez réessayer.</div>';
      });
    },
    
    /**
     * Normalise un numéro de registre national en supprimant les caractères non numériques
     * @param {HTMLElement} input - Élément input à normaliser
     */
    normalizeFavvNatNr: function(input) {
      if (!input) return;
      
      input.addEventListener('input', function(e) {
        // Supprimer tous les caractères non numériques
        const normalized = e.target.value.replace(/[^0-9]/g, '');
        
        // Mettre à jour la valeur de l'input avec la chaîne normalisée
        e.target.value = normalized;
        
        // Effacer le résultat de vérification lorsque l'input change
        const checkResult = document.getElementById('favvNatNrCheckResult');
        if (checkResult) {
          checkResult.innerHTML = '';
        }
      });
    },
    
    /**
     * Vérifie si un numéro de registre national existe déjà
     * @param {string} url - URL pour la vérification
     * @param {string} favvNatNr - Numéro à vérifier
     * @param {string} ldapSource - Source LDAP actuelle
     * @param {string} resultDivId - ID de l'élément pour afficher le résultat
     */
    checkFavvNatNrExists: function(url, favvNatNr, ldapSource, resultDivId) {
      const resultDiv = document.getElementById(resultDivId);
      
      if (!resultDiv) return;
      
      // Valider le numéro
      if (!favvNatNr) {
        resultDiv.innerHTML = '<div class="alert alert-warning">Veuillez saisir un numéro de registre national.</div>';
        return;
      }
      
      // Afficher un indicateur de chargement
      resultDiv.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Vérification en cours...</div>';
      
      // Envoyer la requête AJAX
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          favvNatNr: favvNatNr,
          ldap_source: ldapSource
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'exists') {
          resultDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        } else if (data.status === 'ok') {
          resultDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
        } else {
          resultDiv.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
        }
      })
      .catch(error => {
        console.error('Error:', error);
        resultDiv.innerHTML = '<div class="alert alert-danger">Erreur lors de la vérification. Veuillez réessayer.</div>';
      });
    },
    
    /**
     * Initialise les gestionnaires d'événements pour effacer les résultats de vérification
     * @param {Array} inputIds - Tableau des IDs d'input à surveiller
     * @param {string} resultDivId - ID de l'élément de résultat à effacer
     */
    initClearResults: function(inputIds, resultDivId) {
      inputIds.forEach(inputId => {
        const input = document.getElementById(inputId);
        const resultDiv = document.getElementById(resultDivId);
        
        if (input && resultDiv) {
          input.addEventListener('input', function() {
            resultDiv.innerHTML = '';
          });
        }
      });
    }
  };