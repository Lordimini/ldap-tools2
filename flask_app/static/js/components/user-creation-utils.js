/**
 * Utilitaires simplifiés pour la gestion de la création d'utilisateur
 * Cette version réduit la complexité et minimise les problèmes de clignotement/duplication
 */
const UserCreationUtils = {
  // État global de vérification
  verificationState: {
    nameVerified: false,
    favvNatNrVerified: false
  },
  
  // Cache pour stocker le résultat des vérifications
  verificationResults: {
    nameResult: null,
    favvNatNrResult: null
  },
  
  /**
   * Fonction simplifiée pour nettoyer les modales
   */
  cleanupModal: function() {
    // Supprimer tous les backdrops Bootstrap
    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
    
    // Réinitialiser les classes et styles du body
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // Réinitialiser les attributs sur les modales
    document.querySelectorAll('.modal').forEach(el => {
      if (el.style.display === 'block') {
        el.style.display = 'none';
        el.setAttribute('aria-hidden', 'true');
        el.removeAttribute('aria-modal');
        el.removeAttribute('role');
      }
    });
  },
  
  /**
   * Vérifie l'existence d'un utilisateur avec le même nom
   */
  checkNameExists: function(givenName, sn, ldapSource) {
    return fetch(window.checkNameExistsUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ givenName, sn, ldap_source: ldapSource })
    })
    .then(response => response.json())
    .then(data => {
      // Stocker le résultat dans le cache
      this.verificationResults.nameResult = data;
      
      // Mettre à jour l'état de vérification
      this.verificationState.nameVerified = (data.status !== 'exists');
      
      return data;
    });
  },
  
  /**
   * Vérifie l'existence d'un utilisateur avec le même numéro national
   */
  checkFavvNatNrExists: function(favvNatNr, ldapSource) {
    return fetch(window.checkFavvNatNrExistsUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ favvNatNr, ldap_source: ldapSource })
    })
    .then(response => response.json())
    .then(data => {
      // Stocker le résultat dans le cache
      this.verificationResults.favvNatNrResult = data;
      
      // Mettre à jour l'état de vérification
      this.verificationState.favvNatNrVerified = (data.status !== 'exists');
      
      return data;
    });
  },
  
  /**
   * Construit le contenu HTML pour la modale de vérification
   */
  buildVerificationModalContent: function() {
    const container = document.createElement('div');
    
    // Ajouter les résultats de vérification de nom
    if (this.verificationResults.nameResult) {
      const nameSection = document.createElement('div');
      nameSection.className = 'mb-3';
      
      const nameTitle = document.createElement('h5');
      nameTitle.textContent = 'Name Verification';
      nameSection.appendChild(nameTitle);
      
      const nameData = this.verificationResults.nameResult;
      const nameAlert = document.createElement('div');
      
      nameAlert.className = nameData.status === 'exists' ? 
        'alert alert-danger' : 'alert alert-success';
      
      const givenName = document.getElementById('givenName').value.trim();
      const sn = document.getElementById('sn').value.trim();
      
      if (nameData.status === 'exists') {
        nameAlert.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Un utilisateur avec le nom '${sn} ${givenName}' existe déjà dans l'annuaire (${nameData.message}).`;
      } else {
        nameAlert.innerHTML = `<i class="fas fa-check-circle"></i> Aucun utilisateur existant avec le nom '${sn} ${givenName}'.`;
      }
      
      nameSection.appendChild(nameAlert);
      container.appendChild(nameSection);
    }
    
    // Ajouter les résultats de vérification FavvNatNr si disponibles
    if (this.verificationResults.favvNatNrResult) {
      const natNrSection = document.createElement('div');
      natNrSection.className = 'mb-3';
      
      const natNrTitle = document.createElement('h5');
      natNrTitle.textContent = 'National Register Number Verification';
      natNrSection.appendChild(natNrTitle);
      
      const natNrData = this.verificationResults.favvNatNrResult;
      const natNrAlert = document.createElement('div');
      
      natNrAlert.className = natNrData.status === 'exists' ? 
        'alert alert-danger' : 'alert alert-success';
      
      natNrAlert.innerHTML = natNrData.status === 'exists' ?
        `<i class="fas fa-exclamation-triangle"></i> ${natNrData.message}` :
        `<i class="fas fa-check-circle"></i> ${natNrData.message}`;
      
      natNrSection.appendChild(natNrAlert);
      container.appendChild(natNrSection);
    }
    
    // Ajouter la conclusion
    const conclusion = document.createElement('div');
    conclusion.className = 'mt-3';
    
    const hasDuplicate = !this.verificationState.nameVerified || 
                        (!this.verificationState.favvNatNrVerified && 
                          this.verificationResults.favvNatNrResult);
    
    if (!hasDuplicate) {
      conclusion.innerHTML = `
        <div class="alert alert-info">
          <i class="fas fa-info-circle"></i> 
          Toutes les vérifications sont réussies. Vous pouvez maintenant continuer avec la création de l'utilisateur.
        </div>
      `;
    } else {
      conclusion.innerHTML = `
        <div class="alert alert-warning">
          <i class="fas fa-exclamation-circle"></i> 
          Des doublons potentiels ont été détectés. Vous pouvez modifier les informations et vérifier à nouveau.
        </div>
      `;
    }
    
    container.appendChild(conclusion);
    return container;
  },
  
  /**
   * Prépare les boutons pour la modale de vérification
   */
  setupVerificationModalButtons: function(modalFooter) {
    if (!modalFooter) return;
    
    const hasDuplicate = !this.verificationState.nameVerified || 
                        (!this.verificationState.favvNatNrVerified && 
                          this.verificationResults.favvNatNrResult);
    
    // Réinitialiser le contenu
    modalFooter.innerHTML = '';
    
    // Ajouter le bouton de fermeture standard
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn btn-primary';
    closeButton.setAttribute('data-bs-dismiss', 'modal');
    closeButton.textContent = 'Fermer';
    modalFooter.appendChild(closeButton);
    
    // Si des doublons sont détectés et l'utilisateur est admin, ajouter le bouton d'override
    if (hasDuplicate) {
      const adminStatusField = document.getElementById('admin_status');
      const isAdminUser = adminStatusField && adminStatusField.value === 'true';
      
      if (isAdminUser) {
        const adminOverrideBtn = document.createElement('button');
        adminOverrideBtn.type = 'button';
        adminOverrideBtn.className = 'btn btn-danger';
        adminOverrideBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Override Admin';
        
        // Ajouter le gestionnaire d'événements directement
        adminOverrideBtn.addEventListener('click', () => {
          // Forcer la vérification à réussir
          this.verificationState.nameVerified = true;
          this.verificationState.favvNatNrVerified = true;
          
          // Mettre à jour le bouton de soumission
          this.updateSubmitButtonText();
          
          // Fermer la modale
          const verificationModal = document.getElementById('verificationModal');
          if (verificationModal && bootstrap.Modal) {
            const bsModal = bootstrap.Modal.getInstance(verificationModal);
            if (bsModal) bsModal.hide();
          }
          
          // Afficher un message de confirmation
          alert('Vérification contournée par l\'administrateur. Vous pouvez maintenant prévisualiser et créer l\'utilisateur.');
        });
        
        modalFooter.appendChild(adminOverrideBtn);
      }
    }
  },
  
  /**
   * Fonction simplifiée pour vérifier les informations utilisateur
   */
  verifyUserInfo: function(event) {
    if (event) event.preventDefault();
    
    // Obtenir les éléments du formulaire
    const form = document.getElementById('userCreationForm');
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const userTypeSelect = document.getElementById('user_type');
    const favvNatNrInput = document.getElementById('favvNatNr');
    const favvNatNrContainer = document.getElementById('favvNatNr_container');
    
    // Vérifier si les champs requis sont remplis
    if (!form || !givenNameInput || !snInput || !userTypeSelect) return false;
    
    if (!form.checkValidity()) {
      form.reportValidity();
      return false;
    }
    
    // Nettoyer toute modale précédente
    this.cleanupModal();
    
    // Obtenir les valeurs
    const givenName = givenNameInput.value.trim();
    const sn = snInput.value.trim();
    const ldapSource = LDAPUtils.getCurrentSource();
    
    // Déterminer si nous devons vérifier FavvNatNr
    const userTypeRequiresFavvNatNr = (userTypeSelect.value === 'BOODOCI' || userTypeSelect.value === 'OCI');
    const needFavvNatNrVerification = userTypeRequiresFavvNatNr && 
                                     favvNatNrContainer.style.display !== 'none' && 
                                     favvNatNrInput && 
                                     favvNatNrInput.value.trim() !== '';
    
    // Réinitialiser les résultats précédents
    this.verificationResults.nameResult = null;
    this.verificationResults.favvNatNrResult = null;
    
    // Créer un tableau de promesses à exécuter
    const promises = [
      this.checkNameExists(givenName, sn, ldapSource)
    ];
    
    // Ajouter la vérification de FavvNatNr si nécessaire
    if (needFavvNatNrVerification) {
      promises.push(this.checkFavvNatNrExists(favvNatNrInput.value.trim(), ldapSource));
    } else {
      // Pas besoin de vérifier, considérer comme vérifié
      this.verificationState.favvNatNrVerified = true;
    }
    
    // Afficher un indicateur de chargement
    const verificationModal = document.getElementById('verificationModal');
    const verificationModalBody = document.getElementById('verificationModalBody');
    const verificationModalFooter = document.getElementById('verificationModalFooter');
    
    if (verificationModalBody) {
      verificationModalBody.innerHTML = `
        <div class="text-center p-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Chargement...</span>
          </div>
          <p class="mt-2">Vérification en cours...</p>
        </div>
      `;
    }
    
    // Afficher la modale
    if (verificationModal && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
      const modal = new bootstrap.Modal(verificationModal);
      modal.show();
    }
    
    // Exécuter toutes les vérifications
    Promise.all(promises)
      .then(() => {
        // Mettre à jour l'interface avec les résultats
        if (verificationModalBody) {
          verificationModalBody.innerHTML = '';
          verificationModalBody.appendChild(this.buildVerificationModalContent());
        }
        
        // Mettre à jour les boutons
        this.setupVerificationModalButtons(verificationModalFooter);
        
        // Mettre à jour le texte du bouton de soumission
        this.updateSubmitButtonText();
      })
      .catch(error => {
        console.error('Error during verification:', error);
        
        if (verificationModalBody) {
          verificationModalBody.innerHTML = `
            <div class="alert alert-danger">
              <i class="fas fa-exclamation-circle"></i>
              Une erreur est survenue pendant la vérification. Veuillez réessayer.
            </div>
          `;
        }
      });
    
    return false;
  },
  
  /**
   * Met à jour le texte du bouton de soumission selon l'état de vérification
   */
  updateSubmitButtonText: function() {
    const submitButton = document.getElementById('submitBtn');
    if (!submitButton) return;
    
    // Accéder à l'état de vérification
    const nameVerified = this.verificationState.nameVerified;
    const favvNatNrVerified = this.verificationState.favvNatNrVerified;
    
    // Vérifier si le type d'utilisateur nécessite FavvNatNr
    const userTypeSelect = document.getElementById('user_type');
    const userTypeRequiresFavvNatNr = userTypeSelect && 
                                     (userTypeSelect.value === 'BOODOCI' || 
                                      userTypeSelect.value === 'OCI');
    
    // Déterminer si toutes les vérifications ont passé
    const allChecksPass = nameVerified && (favvNatNrVerified || !userTypeRequiresFavvNatNr);
    
    // Mettre à jour le bouton en fonction de l'état
    if (allChecksPass) {
      submitButton.textContent = 'Preview & Create User';
      submitButton.classList.remove('btn-secondary');
      submitButton.classList.add('btn-primary');
      
      // Supprimer l'ancien gestionnaire et ajouter le nouveau
      const newButton = submitButton.cloneNode(true);
      submitButton.parentNode.replaceChild(newButton, submitButton);
      newButton.addEventListener('click', this.validateForm.bind(this));
    } else {
      submitButton.textContent = 'Verify User Information';
      submitButton.classList.remove('btn-primary');
      submitButton.classList.add('btn-secondary');
      
      // Supprimer l'ancien gestionnaire et ajouter le nouveau
      const newButton = submitButton.cloneNode(true);
      submitButton.parentNode.replaceChild(newButton, submitButton);
      newButton.addEventListener('click', this.verifyUserInfo.bind(this));
    }
  },
  
  /**
   * Valide le formulaire avant de prévisualiser l'utilisateur
   */
  validateForm: function(event) {
    if (event) event.preventDefault();
    
    // Obtenir la source LDAP actuelle
    const ldapSource = LDAPUtils.getCurrentSource();
    
    // Vérifier la validité du formulaire
    const form = document.getElementById('userCreationForm');
    if (!form) return false;
    
    if (!form.checkValidity()) {
      // Activer la validation native du navigateur
      form.reportValidity();
      return false;
    }
    
    // Effectuer les vérifications d'override
    // Vérifier les champs requis avec overrides
    const emailField = document.getElementById('email');
    const emailOverrideInput = document.getElementById('email_override');
    
    if (emailField && emailOverrideInput) {
      const emailOverride = emailOverrideInput.value === 'true';
      if (!emailField.value && !emailOverride) {
        alert('Email address is required. Use the override button if you want to proceed without an email.');
        return false;
      }
    }
    
    // Vérifier FavvNatNr si nécessaire
    const favvNatNrContainer = document.getElementById('favvNatNr_container');
    if (favvNatNrContainer && favvNatNrContainer.style.display !== 'none') {
      const favvNatNrField = document.getElementById('favvNatNr');
      const favvNatNrOverrideInput = document.getElementById('favvNatNr_override');
      
      if (favvNatNrField && favvNatNrOverrideInput) {
        const favvNatNrOverride = favvNatNrOverrideInput.value === 'true';
        if (!favvNatNrField.value && !favvNatNrOverride) {
          alert('National Register Number is required for this user type. Use the override button if you want to proceed without it.');
          return false;
        }
      }
    }
    
    // Vérifier Manager si nécessaire
    const managerContainer = document.getElementById('manager_container');
    if (managerContainer && managerContainer.style.display !== 'none') {
      const managerField = document.getElementById('manager');
      const managerOverrideInput = document.getElementById('manager_override');
      
      if (managerField && managerOverrideInput) {
        const managerOverride = managerOverrideInput.value === 'true';
        if (!managerField.value && !managerOverride) {
          alert('Hierarchical Manager is required for trainees. Use the override button if you want to proceed without it.');
          return false;
        }
      }
    }
    
    // Nettoyer toute modale précédente avant d'afficher la nouvelle
    this.cleanupModal();
    
    // Récupérer les valeurs nécessaires
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const userTypeInput = document.getElementById('user_type');
    
    if (!givenNameInput || !snInput || !userTypeInput) return false;
    
    // Vérifier si un des noms est court (3 caractères ou moins)
    const hasShortName = givenNameInput.value.trim().length <= 3 || snInput.value.trim().length <= 3;
    
    // Envoyer la requête AJAX pour prévisualiser les détails
    this.showLoading();

    // Définir un timeout de sécurité pour garantir que l'indicateur de chargement disparait
    const loadingTimeout = setTimeout(() => {
      this.hideLoading();
    }, 2000); // 10 secondes maximum

    fetch(window.previewUserDetailsUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        givenName: givenNameInput.value,
        sn: snInput.value,
        user_type: userTypeInput.value,
        ldap_source: ldapSource
      })
    })
    .then(response => response.json())
    .then(data => {
      // Annuler le timeout de sécurité
      clearTimeout(loadingTimeout);

      this.hideLoading();
      if (data.error) {
        alert('Erreur lors de la prévisualisation: ' + data.error);
        return;
      }
      
      // Remplir la modale avec les données
      this.populateConfirmationModal(data.cn, data.password, data.template_details, data.has_short_name || hasShortName);
      
      // Afficher la modale de confirmation
      if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const confirmationModal = document.getElementById('confirmationModal');
        if (confirmationModal) {
          const modal = new bootstrap.Modal(confirmationModal);
          modal.show();
        }
      }
    })
    .catch(error => {
      // Annuler le timeout de sécurité
      clearTimeout(loadingTimeout);
      this.hideLoading();
      console.error('Error:', error);
      alert('Une erreur est survenue lors de la prévisualisation des détails utilisateur.');
    });
    
    return false;
  },
  
  /**
   * Affiche un indicateur de chargement
   */
  showLoading: function() {
    // Créer un élément de chargement s'il n'existe pas déjà
    if (!document.getElementById('loadingIndicator')) {
      const loadingDiv = document.createElement('div');
      loadingDiv.id = 'loadingIndicator';
      loadingDiv.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center';
      loadingDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
      loadingDiv.style.zIndex = '9999';
      
      loadingDiv.innerHTML = `
        <div class="card p-4 shadow-lg">
          <div class="text-center">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Chargement...</span>
            </div>
            <p class="mt-2 mb-0">Préparation de la prévisualisation...</p>
          </div>
        </div>
      `;
      
      document.body.appendChild(loadingDiv);
    } else {
      document.getElementById('loadingIndicator').style.display = 'flex';
    }
  },
  
  /**
   * Cache l'indicateur de chargement
   */
  hideLoading: function() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
      // Plutôt que simplement masquer, supprimons-le complètement du DOM
      loadingIndicator.remove();
    }
  },
  
  /**
   * Remplit la modale de confirmation avec les détails utilisateur
   */
  populateConfirmationModal: function(cn, password, template_details, hasShortName) {
    const userTypeSelect = document.getElementById('user_type');
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const emailInput = document.getElementById('email');
    const favvNatNrInput = document.getElementById('favvNatNr');
    const managerInput = document.getElementById('manager');
    const userSummaryDiv = document.getElementById('userSummary');
    const ldapSource = LDAPUtils.getCurrentSource();
    const hiddenPasswordInput = document.getElementById('hidden_password');

    if (hiddenPasswordInput) hiddenPasswordInput.value = password;

    if (!userTypeSelect || !givenNameInput || !snInput || !emailInput || 
        !favvNatNrInput || !managerInput || !userSummaryDiv) {
      return;
    }
    
    const userTypeText = userTypeSelect.options[userTypeSelect.selectedIndex]?.text || userTypeSelect.value;
    const givenName = givenNameInput.value;
    const sn = snInput.value;
    const email = emailInput.value || 'No email specified (Override)';
    const favvNatNr = favvNatNrInput.value || 'No National Register Number (Override)';
    const manager = managerInput.value || 'No manager specified (Override)';
    
    // Générer le contenu HTML de la modale
    // (ce code reste identique à l'original)
    // Déterminer si un nom est court (3 caractères ou moins)
    const shortNameWarning = hasShortName ? `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i> 
        <strong>Remarque importante :</strong> Un ou plusieurs noms étant courts (3 caractères ou moins), 
        le format du mot de passe a été modifié pour se conformer aux politiques Active Directory.
      </div>` : '';
    
    // Créer le HTML pour le résumé
    let html = `
      ${shortNameWarning}
      <table class="table table-striped">
        <tr>
          <th>User Type:</th>
          <td>${userTypeText} (${userTypeSelect.value})</td>
        </tr>
        <tr>
          <th>Full Name:</th>
          <td>${sn} ${givenName}</td>
        </tr>
        <tr class="table-primary">
          <th>Common Name (CN):</th>
          <td><strong>${cn}</strong></td>
        </tr>
        <tr class="table-primary">
          <th>Generated Password:</th>
          <td><code>${password}</code>${hasShortName ? ' <span class="badge bg-info">Format spécial</span>' : ''}</td>
        </tr>
        <tr>
          <th>Email:</th>
          <td>${email}</td>
        </tr>
        <tr>
          <th>LDAP Source:</th>
          <td>${ldapSource}</td>
        </tr>`;
    
    // Ajouter les champs conditionnels
    const favvNatNrContainer = document.getElementById('favvNatNr_container');
    if (favvNatNrContainer && favvNatNrContainer.style.display !== 'none') {
      html += `
        <tr>
          <th>National Register Number:</th>
          <td>${favvNatNr}</td>
        </tr>`;
    }
    
    const managerContainer = document.getElementById('manager_container');
    if (managerContainer && managerContainer.style.display !== 'none') {
      html += `
        <tr>
          <th>Hierarchical Manager:</th>
          <td>${manager}</td>
        </tr>`;
    }
    
    // Ajouter les détails du template si disponibles
    if (template_details) {
      html += `<tr><th colspan="2" class="table-secondary">Template Attributes</th></tr>`;
      
      if (template_details.description) {
        html += `
          <tr>
            <th>Description:</th>
            <td>${template_details.description}</td>
          </tr>`;
      }
      
      if (template_details.title) {
        html += `
          <tr>
            <th>Title:</th>
            <td>${template_details.title}</td>
          </tr>`;
      }
      
      if (template_details.ou) {
        html += `
          <tr>
            <th>Service/OU:</th>
            <td>${template_details.ou}</td>
          </tr>`;
      }
      
      if (template_details.FavvEmployeeType) {
        html += `
          <tr>
            <th>Employee Type:</th>
            <td>${template_details.FavvEmployeeType}</td>
          </tr>`;
      }
      
      if (template_details.FavvEmployeeSubType) {
        html += `
          <tr>
            <th>Employee SubType:</th>
            <td>${template_details.FavvEmployeeSubType}</td>
          </tr>`;
      }
      
      if (template_details.FavvExtDienstMgrDn) {
        html += `
          <tr>
            <th>Service Manager:</th>
            <td>${template_details.ServiceManagerName || 'Non disponible'} <span class="text-muted small">(${template_details.FavvExtDienstMgrDn})</span></td>
          </tr>`;
      }

      if (template_details.groups_info && template_details.groups_info.length > 0) {
        html += `<tr><th colspan="2" class="table-secondary">Groupes associés</th></tr>`;
        
        template_details.groups_info.forEach(function(group) {
          html += `
            <tr>
              <th>Groupe:</th>
              <td>${group.cn} <span class="text-muted small">(${group.dn})</span></td>
            </tr>`;
        });
      }
    }
    
    html += `</table>
      <div class="alert alert-info">
        <strong>Note:</strong> Le CN et le mot de passe sont générés automatiquement en fonction du nom.
        ${template_details ? 'Les attributs du template seront automatiquement appliqués lors de la création.' : ''}
      </div>`;
    
    // Définir le HTML dans la modale
    userSummaryDiv.innerHTML = html;
    
    // Remplir le formulaire caché
    this.fillHiddenForm({
      userType: userTypeSelect.value,
      givenName: givenName,
      sn: sn,
      email: emailInput.value,
      emailOverride: document.getElementById('email_override')?.value || 'false',
      favvNatNr: favvNatNrInput.value,
      favvNatNrOverride: document.getElementById('favvNatNr_override')?.value || 'false',
      manager: managerInput.value,
      managerOverride: document.getElementById('manager_override')?.value || 'false',
      ldapSource: ldapSource,
      password: password
    });
    
    // Configurer le bouton de confirmation
    this.setupConfirmationButton();
  },
  
  /**
   * Remplit le formulaire caché avec les valeurs pour la soumission
   */
  fillHiddenForm: function(data) {
    console.log("Data being filled into hidden form:", data);
    // Liste des champs à remplir
    const fields = [
      'user_type', 'givenName', 'sn', 'email', 'email_override',
      'favvNatNr', 'favvNatNr_override', 'manager', 'manager_override',
      'ldap_source', 'password'
    ];
    
    
// Remplir chaque champ s'il existe
fields.forEach(field => {
  const hiddenInput = document.getElementById(`hidden_${field}`);
  if (hiddenInput && data[field] !== undefined) {
    hiddenInput.value = data[field];
  }
});
},

/**
* Configure le bouton de confirmation pour soumettre le formulaire
*/
setupConfirmationButton: function() {
const confirmCreateBtn = document.getElementById('confirmCreate');
if (!confirmCreateBtn) return;

// Supprimer les gestionnaires d'événements précédents
const newConfirmCreateBtn = confirmCreateBtn.cloneNode(true);
confirmCreateBtn.parentNode.replaceChild(newConfirmCreateBtn, confirmCreateBtn);

// Ajouter un nouveau gestionnaire d'événements
newConfirmCreateBtn.addEventListener('click', () => {
  // Nettoyer les modales avant la soumission
  this.cleanupModal();
  
  // Soumettre le formulaire caché
  const actualSubmitForm = document.getElementById('actualSubmitForm');
  if (actualSubmitForm) {
    actualSubmitForm.submit();
  }
});

// Ajouter un gestionnaire pour la fermeture de la modale
const confirmationModal = document.getElementById('confirmationModal');
if (confirmationModal) {
  confirmationModal.addEventListener('hidden.bs.modal', () => {
    // Nettoyer les backdrops potentiellement restants après la fermeture
    setTimeout(() => this.cleanupModal(), 300);
  });
}
},

/**
* Initialise les champs conditionnels en fonction du type d'utilisateur
*/
initConditionalFields: function() {
const userTypeSelect = document.getElementById('user_type');
const favvNatNrContainer = document.getElementById('favvNatNr_container');
const managerContainer = document.getElementById('manager_container');

if (!userTypeSelect || !favvNatNrContainer || !managerContainer) return;

// Fonction pour basculer la visibilité des champs
const toggleFields = () => {
  // Types OCI
  const userType = userTypeSelect.value;
  const userTypeRequiresFavvNatNr = (userType === 'BOODOCI' || userType === 'OCI');

  if (userTypeRequiresFavvNatNr) {
    favvNatNrContainer.style.display = 'block';
    // Réinitialiser l'état de vérification pour FavvNatNr en cas de changement de type d'utilisateur
    this.verificationState.favvNatNrVerified = false;
  } else {
    favvNatNrContainer.style.display = 'none';
    // Pas besoin de vérifier FavvNatNr si non requis
    this.verificationState.favvNatNrVerified = true;
  }
  
  // Type STAG (stagiaire)
  if (userType === 'STAG') {
    managerContainer.style.display = 'block';
  } else {
    managerContainer.style.display = 'none';
  }
  
  // Réinitialiser l'état de vérification du nom en cas de changement de type d'utilisateur
  this.verificationState.nameVerified = false;
  this.updateSubmitButtonText();
};

// Vérification initiale
toggleFields.bind(this)();

// Écouter les changements de type d'utilisateur
userTypeSelect.addEventListener('change', toggleFields.bind(this));

// Réinitialiser la vérification lorsque les champs de nom changent
const givenNameInput = document.getElementById('givenName');
const snInput = document.getElementById('sn');

if (givenNameInput) {
  givenNameInput.addEventListener('input', () => {
    this.verificationState.nameVerified = false;
    this.updateSubmitButtonText();
  });
}

if (snInput) {
  snInput.addEventListener('input', () => {
    this.verificationState.nameVerified = false;
    this.updateSubmitButtonText();
  });
}

// Normalisation de FavvNatNr
const favvNatNrInput = document.getElementById('favvNatNr');
if (favvNatNrInput) {
  favvNatNrInput.addEventListener('input', (e) => {
    // Supprimer tous les caractères non numériques
    const normalized = e.target.value.replace(/[^0-9]/g, '');
    
    // Mettre à jour la valeur de l'input avec la chaîne normalisée
    e.target.value = normalized;
    
    // Réinitialiser l'état de vérification
    this.verificationState.favvNatNrVerified = false;
    this.updateSubmitButtonText();
  });
}
},

/**
* Initialise l'autocomplétion pour le champ de manager
*/
initManagerAutocomplete: function() {
const ldapSource = LDAPUtils.getCurrentSource();
const managerInput = $('#manager');

if (managerInput.length > 0 && managerInput.autocomplete && window.autocompleteManagersUrl) {
  managerInput.autocomplete({
    source: function(request, response) {
      $.getJSON(window.autocompleteManagersUrl, {
        term: request.term,
        source: ldapSource
      }, function(data) {
        response(data);
      });
    },
    select: function(event, ui) {
      managerInput.val(ui.item.value);
      
      // Extraire le DN de l'étiquette (format est "fullName - email - title (DN)")
      const dnMatch = ui.item.label.match(/\((.*?)\)$/);
      if (dnMatch && dnMatch[1]) {
        $('#manager_dn').val(dnMatch[1]);
      }
      
      return false;
    },
    minLength: 2
  }).data('ui-autocomplete')._renderItem = function(ul, item) {
    return $('<li>')
      .append(`<div>${item.label}</div>`)
      .appendTo(ul);
  };
}
},

/**
* Configure les boutons d'override pour les champs facultatifs
*/
setupOverrideButtons: function() {
// Liste des champs avec boutons d'override
const overrideFields = [
  { fieldId: 'email', overrideId: 'email_override_btn' },
  { fieldId: 'favvNatNr', overrideId: 'favvNatNr_override_btn' },
  { fieldId: 'manager', overrideId: 'manager_override_btn' }
];

// Configurer chaque bouton d'override
overrideFields.forEach(item => {
  const overrideBtn = document.getElementById(item.overrideId);
  const field = document.getElementById(item.fieldId);
  const overrideInput = document.getElementById(`${item.fieldId}_override`);
  
  if (overrideBtn && field && overrideInput) {
    // Supprimer les gestionnaires d'événements précédents
    const newOverrideBtn = overrideBtn.cloneNode(true);
    overrideBtn.parentNode.replaceChild(newOverrideBtn, overrideBtn);
    
    newOverrideBtn.addEventListener('click', () => {
      // Inverser l'état d'override
      const currentState = overrideInput.value === 'true';
      const newState = !currentState;
      
      // Mettre à jour l'input caché
      overrideInput.value = newState.toString();
      
      // Mettre à jour l'apparence du bouton et du champ
      if (newState) {
        // Activer l'override
        newOverrideBtn.classList.remove('btn-outline-secondary');
        newOverrideBtn.classList.add('btn-danger');
        newOverrideBtn.innerHTML = '<i class="fas fa-times"></i> Cancel Override';
        
        // Désactiver le champ et ajouter une classe visuelle
        field.setAttribute('readonly', 'readonly');
        field.classList.add('override-active');
        field.placeholder = `(Optional - Override active)`;
      } else {
        // Désactiver l'override
        newOverrideBtn.classList.remove('btn-danger');
        newOverrideBtn.classList.add('btn-outline-secondary');
        newOverrideBtn.innerHTML = '<i class="fas fa-check"></i> Override';
        
        // Réactiver le champ
        field.removeAttribute('readonly');
        field.classList.remove('override-active');
        field.placeholder = `Enter ${item.fieldId}...`;
      }
      
      // Mettre à jour l'état de vérification pour manager et FavvNatNr
      if (item.fieldId === 'favvNatNr') {
        this.verificationState.favvNatNrVerified = newState;  // Si override est activé, considérer comme vérifié
        this.updateSubmitButtonText();
      }
    });
  }
});
},

/**
* Initialise les vérifications de noms courts pour alerter sur le format du mot de passe
*/
initNameLengthChecks: function() {
const givenNameInput = document.getElementById('givenName');
const snInput = document.getElementById('sn');
const nameCheckResult = document.getElementById('nameCheckResult');

if (!givenNameInput || !snInput || !nameCheckResult) return;

// Fonction pour vérifier la longueur des noms
const checkNameLength = () => {
  const givenName = givenNameInput.value.trim();
  const sn = snInput.value.trim();
  
  // Effacer les avertissements existants
  const existingWarnings = nameCheckResult.querySelectorAll('.short-name-warning');
  existingWarnings.forEach(warning => warning.remove());
  
  // Vérifier si l'un des noms a 3 caractères ou moins
  if ((givenName.length > 0 && givenName.length <= 3) || (sn.length > 0 && sn.length <= 3)) {
    const shortNameWarning = document.createElement('div');
    shortNameWarning.className = 'alert alert-warning short-name-warning mt-2';
    shortNameWarning.innerHTML = `
      <i class="fas fa-exclamation-triangle"></i> 
      <strong>Remarque:</strong> Un des noms est court (3 caractères ou moins). 
      Le mot de passe utilisera un format spécial pour se conformer aux politiques Active Directory.
    `;
    nameCheckResult.appendChild(shortNameWarning);
  }
};

// Ajouter des écouteurs d'événements pour les champs de nom
givenNameInput.addEventListener('input', checkNameLength);
snInput.addEventListener('input', checkNameLength);

// Vérifier au chargement de la page
checkNameLength();
},

/**
* Initialise toutes les fonctionnalités pour la création d'utilisateur
*/
init: function() {
console.log('UserCreationUtils: Starting initialization...');

// Nettoyer les modales et backdrops au cas où
this.cleanupModal();

// Initialiser la vérification de la longueur des noms
this.initNameLengthChecks();

// Initialiser les champs conditionnels
this.initConditionalFields();

// Initialiser l'autocomplétion du manager
this.initManagerAutocomplete();

// Configurer les boutons d'override pour les champs facultatifs
this.setupOverrideButtons();

// Configurer le bouton de soumission initial
const submitButton = document.getElementById('submitBtn');
if (submitButton) {
  submitButton.addEventListener('click', this.verifyUserInfo.bind(this));
}

// Ajouter un gestionnaire pour gérer les événements de navigation
window.addEventListener('beforeunload', () => {
  this.cleanupModal();
});

console.log('UserCreationUtils: Initialization complete');
}
};