/**
 * Utilitaires pour la gestion de la création d'utilisateur
 */
const UserCreationUtils = {
  /**
   * État de vérification pour la création d'utilisateurs
   */
  verificationState: {
    nameVerified: false,
    favvNatNrVerified: false
  },
  
  /**
   * Nettoie complètement la modale et ses effets sur le DOM
   */
  cleanupModal: function() {
    // Supprimer tous les backdrops
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
   * Met à jour le texte du bouton de soumission en fonction de l'état de vérification
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
    
    if (nameVerified && (favvNatNrVerified || !userTypeRequiresFavvNatNr)) {
      submitButton.textContent = 'Preview & Create User';
      submitButton.classList.remove('btn-secondary');
      submitButton.classList.add('btn-primary');
      
      // Changer le gestionnaire d'événements
      submitButton.removeEventListener('click', this.verifyUserInfo);
      submitButton.addEventListener('click', this.validateForm.bind(this));
    } else {
      submitButton.textContent = 'Verify User Information';
      submitButton.classList.remove('btn-primary');
      submitButton.classList.add('btn-secondary');
      
      // Changer le gestionnaire d'événements
      submitButton.removeEventListener('click', this.validateForm);
      submitButton.addEventListener('click', this.verifyUserInfo.bind(this));
    }
  },
  
  /**
   * Vérifie les informations utilisateur avant de permettre la création
   * @param {Event} event - L'événement de clic
   */
  verifyUserInfo: function(event) {
    event.preventDefault();
    
    // Obtenir les éléments du formulaire
    const form = document.getElementById('userCreationForm');
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const userTypeSelect = document.getElementById('user_type');
    const favvNatNrInput = document.getElementById('favvNatNr');
    const favvNatNrContainer = document.getElementById('favvNatNr_container');
    const ldapSource = LDAPUtils.getCurrentSource();
    
    // Vérifier si les champs requis sont remplis
    if (!form || !givenNameInput || !snInput || !userTypeSelect) return false;
    
    if (!form.checkValidity()) {
      // Déclencher la validation native du navigateur
      form.reportValidity();
      return false;
    }
    
    // Déterminer si nous devons vérifier FavvNatNr
    const userTypeRequiresFavvNatNr = (userTypeSelect.value === 'BOODOCI' || userTypeSelect.value === 'OCI');
    const needFavvNatNrVerification = userTypeRequiresFavvNatNr && 
                                     favvNatNrContainer.style.display !== 'none' && 
                                     favvNatNrInput && 
                                     favvNatNrInput.value.trim() !== '';
    
    // Obtenir les valeurs
    const givenName = givenNameInput.value.trim();
    const sn = snInput.value.trim();
    const favvNatNr = favvNatNrInput?.value.trim() || '';
    
    // Initialiser les promesses de vérification
    const promises = [];
    
    // Créer un conteneur pour les résultats de vérification
    const verificationResults = document.createElement('div');
    
    // Initialiser les drapeaux de détection de doublons
    let nameIsDuplicate = false;
    let favvNatNrIsDuplicate = false;
    
    // Ajouter la promesse de vérification de nom
    promises.push(
      fetch(window.checkNameExistsUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          givenName: givenName,
          sn: sn,
          ldap_source: ldapSource
        })
      })
      .then(response => response.json())
      .then(data => {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'mb-3';
        
        const title = document.createElement('h5');
        title.textContent = 'Name Verification';
        resultDiv.appendChild(title);
        
        const alert = document.createElement('div');
        alert.className = data.status === 'exists' ? 
          'alert alert-danger' : 
          'alert alert-success';
        
        if (data.status === 'exists') {
          alert.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Un utilisateur avec le nom '${sn} ${givenName}' existe déjà dans l'annuaire (${data.message}).`;
          nameIsDuplicate = true;
        } else {
          alert.innerHTML = `<i class="fas fa-check-circle"></i> Aucun utilisateur existant avec le nom '${sn} ${givenName}'.`;
          // Marquer le nom comme vérifié
          UserCreationUtils.verificationState.nameVerified = true;
        }
        
        resultDiv.appendChild(alert);
        verificationResults.appendChild(resultDiv);
        
        return data;
      })
    );
    
    // Ajouter la promesse de vérification FavvNatNr si nécessaire
    if (needFavvNatNrVerification) {
      promises.push(
        fetch(window.checkFavvNatNrExistsUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            favvNatNr: favvNatNr,
            ldap_source: ldapSource
          })
        })
        .then(response => response.json())
        .then(data => {
          const resultDiv = document.createElement('div');
          resultDiv.className = 'mb-3';
          
          const title = document.createElement('h5');
          title.textContent = 'National Register Number Verification';
          resultDiv.appendChild(title);
          
          const alert = document.createElement('div');
          alert.className = data.status === 'exists' ? 
            'alert alert-danger' : 
            'alert alert-success';
          
          alert.innerHTML = data.status === 'exists' ?
            `<i class="fas fa-exclamation-triangle"></i> ${data.message}` :
            `<i class="fas fa-check-circle"></i> ${data.message}`;
          
          if (data.status === 'exists') {
            favvNatNrIsDuplicate = true;
          } else {
            // Marquer FavvNatNr comme vérifié
            UserCreationUtils.verificationState.favvNatNrVerified = true;
          }
          
          resultDiv.appendChild(alert);
          verificationResults.appendChild(resultDiv);
          
          return data;
        })
      );
    } else {
      // Pas besoin de vérifier FavvNatNr
      UserCreationUtils.verificationState.favvNatNrVerified = true;
    }
    
    // Attendre que toutes les vérifications soient terminées
    Promise.all(promises)
      .then(results => {
        // Nettoyer toute modale précédente avant d'afficher la nouvelle
        this.cleanupModal();
        
        // Afficher les résultats de vérification dans la modale
        const verificationModal = document.getElementById('verificationModal');
        const verificationModalBody = document.getElementById('verificationModalBody');
        const verificationModalFooter = document.getElementById('verificationModalFooter');
        
        if (verificationModal && verificationModalBody) {
          verificationModalBody.innerHTML = '';
          verificationModalBody.appendChild(verificationResults);
          
          // Ajouter la conclusion et les étapes suivantes
          const conclusion = document.createElement('div');
          conclusion.className = 'mt-3';
          
          const hasDuplicate = nameIsDuplicate || favvNatNrIsDuplicate;
          
          if (!hasDuplicate) {
            conclusion.innerHTML = `
              <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> 
                Toutes les vérifications sont réussies. Vous pouvez maintenant continuer avec la création de l'utilisateur.
              </div>
            `;
            
            // Réinitialiser le footer (pas besoin d'override administrateur)
            if (verificationModalFooter) {
              verificationModalFooter.innerHTML = `
                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Fermer</button>
              `;
            }
          } else {
            conclusion.innerHTML = `
              <div class="alert alert-warning">
                <i class="fas fa-exclamation-circle"></i> 
                Des doublons potentiels ont été détectés. Vous pouvez modifier les informations et vérifier à nouveau.
              </div>
            `;
            
            // Vérifier si l'utilisateur est un administrateur pour afficher le bouton d'override
            const adminStatusField = document.getElementById('admin_status');
            const isAdminUser = adminStatusField && adminStatusField.value === 'true';
            
            if (isAdminUser && verificationModalFooter) {
              verificationModalFooter.innerHTML = `
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                <button type="button" class="btn btn-danger" id="adminOverrideBtn">
                  <i class="fas fa-exclamation-triangle"></i> Override Admin
                </button>
              `;
            } else {
              // Réinitialiser le footer (pour les utilisateurs non-administrateurs)
              if (verificationModalFooter) {
                verificationModalFooter.innerHTML = `
                  <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Fermer</button>
                `;
              }
            }
          }
          
          verificationModalBody.appendChild(conclusion);
          
          // Afficher la modale de vérification
          const modal = new bootstrap.Modal(verificationModal);
          modal.show();
          
          // Ajouter un gestionnaire d'événements pour le bouton d'override administrateur s'il existe
          const adminOverrideBtn = document.getElementById('adminOverrideBtn');
          if (adminOverrideBtn) {
            // Supprimer les gestionnaires d'événements précédents en clonant le bouton
            const newAdminOverrideBtn = adminOverrideBtn.cloneNode(true);
            adminOverrideBtn.parentNode.replaceChild(newAdminOverrideBtn, adminOverrideBtn);
            
            newAdminOverrideBtn.addEventListener('click', () => {
              // Forcer la vérification à réussir
              this.verificationState.nameVerified = true;
              this.verificationState.favvNatNrVerified = true;
              
              // Mettre à jour le bouton de soumission
              this.updateSubmitButtonText();
              
              // Nettoyer le DOM avant de fermer la modale
              this.cleanupModal();
              
              // Fermer la modale
              const bsModal = bootstrap.Modal.getInstance(verificationModal);
              if (bsModal) {
                bsModal.hide();
              }
              
              // Double vérification pour s'assurer que tout est bien nettoyé
              setTimeout(() => {
                this.cleanupModal();
              }, 300);
              
              // Afficher un message de confirmation
              alert('Vérification contournée par l\'administrateur. Vous pouvez maintenant prévisualiser et créer l\'utilisateur.');
            });
          }
          
          // Mettre à jour le texte du bouton de soumission
          this.updateSubmitButtonText();
          
          // Ajouter un gestionnaire pour nettoyer correctement lors de la fermeture normale
          verificationModal.addEventListener('hidden.bs.modal', () => {
            setTimeout(() => {
              this.cleanupModal();
            }, 300);
          });
        }
      })
      .catch(error => {
        console.error('Error during verification:', error);
        alert('Une erreur est survenue pendant la vérification. Veuillez réessayer.');
      });
    
    return false;
  },
  
  /**
   * Valide le formulaire après vérification et affiche la prévisualisation
   * @param {Event} event - L'événement de clic
   */
  validateForm: function(event) {
    event.preventDefault();
    
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
    
    // Récupérer le CN et le mot de passe avant d'afficher la modale
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const userTypeInput = document.getElementById('user_type');
    
    if (!givenNameInput || !snInput || !userTypeInput) return false;
    
    // Vérifier si un des noms est court (3 caractères ou moins)
    const hasShortName = givenNameInput.value.trim().length <= 3 || snInput.value.trim().length <= 3;
    
    // Nettoyer toute modale précédente avant d'afficher la nouvelle
    this.cleanupModal();
    
    // Envoyer la requête AJAX
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
          
          // Ajouter un gestionnaire pour nettoyer correctement lors de la fermeture
          confirmationModal.addEventListener('hidden.bs.modal', () => {
            setTimeout(() => {
              this.cleanupModal();
            }, 300);
          });
        }
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Une erreur est survenue lors de la prévisualisation des détails utilisateur.');
    });
    
    return false; // Empêcher la soumission normale du formulaire
  },
  
  /**
   * Remplit la modale de confirmation avec les informations utilisateur
   * @param {string} cn - Common Name de l'utilisateur
   * @param {string} password - Mot de passe généré
   * @param {Object} template_details - Détails du template
   * @param {boolean} hasShortName - Indique si un nom court est présent
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
    
    // Remplir également le formulaire caché pour la soumission
    const hiddenUserTypeInput = document.getElementById('hidden_user_type');
    const hiddenGivenNameInput = document.getElementById('hidden_givenName');
    const hiddenSnInput = document.getElementById('hidden_sn');
    const hiddenEmailInput = document.getElementById('hidden_email');
    const hiddenEmailOverrideInput = document.getElementById('hidden_email_override');
    const hiddenFavvNatNrInput = document.getElementById('hidden_favvNatNr');
    const hiddenFavvNatNrOverrideInput = document.getElementById('hidden_favvNatNr_override');
    const hiddenManagerInput = document.getElementById('hidden_manager');
    const hiddenManagerOverrideInput = document.getElementById('hidden_manager_override');
    const hiddenLdapSourceInput = document.getElementById('hidden_ldap_source');
    
    if (hiddenUserTypeInput) hiddenUserTypeInput.value = userTypeSelect.value;
    if (hiddenGivenNameInput) hiddenGivenNameInput.value = givenName;
    if (hiddenSnInput) hiddenSnInput.value = sn;
    if (hiddenEmailInput) hiddenEmailInput.value = emailInput.value;
    if (hiddenEmailOverrideInput) hiddenEmailOverrideInput.value = document.getElementById('email_override')?.value || 'false';
    if (hiddenFavvNatNrInput) hiddenFavvNatNrInput.value = favvNatNrInput.value;
    if (hiddenFavvNatNrOverrideInput) hiddenFavvNatNrOverrideInput.value = document.getElementById('favvNatNr_override')?.value || 'false';
    if (hiddenManagerInput) hiddenManagerInput.value = managerInput.value;
    if (hiddenManagerOverrideInput) hiddenManagerOverrideInput.value = document.getElementById('manager_override')?.value || 'false';
    if (hiddenLdapSourceInput) hiddenLdapSourceInput.value = ldapSource;
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
   * Configure les événements pour la soumission du formulaire et les boutons de la modale
   */
  setupFormSubmission: function() {
    // Configurer le bouton "Créer l'utilisateur" dans la modale de confirmation
    const confirmCreateBtn = document.getElementById('confirmCreate');
    if (confirmCreateBtn) {
      // Supprimer les gestionnaires d'événements précédents en clonant le bouton
      const newConfirmCreateBtn = confirmCreateBtn.cloneNode(true);
      confirmCreateBtn.parentNode.replaceChild(newConfirmCreateBtn, confirmCreateBtn);
      
      newConfirmCreateBtn.addEventListener('click', () => {
        // Nettoyer les modales et backdrops avant la soumission
        this.cleanupModal();
        
        // Soumettre le formulaire caché avec toutes les données
        const actualSubmitForm = document.getElementById('actualSubmitForm');
        if (actualSubmitForm) {
          actualSubmitForm.submit();
        }
      });
    }
    
    // Configurer le bouton initial
    const submitButton = document.getElementById('submitBtn');
    if (submitButton) {
      // Supprimer les gestionnaires d'événements précédents
      const newSubmitButton = submitButton.cloneNode(true);
      submitButton.parentNode.replaceChild(newSubmitButton, submitButton);
      
      // Attacher l'écouteur d'événements initial
      newSubmitButton.addEventListener('click', this.verifyUserInfo.bind(this));
      
      // Mettre à jour la référence globale
      window.submitButton = newSubmitButton;
    }
    
    // Ajouter un gestionnaire d'événements sur les modales pour le nettoyage
    document.querySelectorAll('.modal').forEach(modal => {
      modal.addEventListener('hidden.bs.modal', () => {
        setTimeout(() => this.cleanupModal(), 300);
      });
    });
    
    // Configurer les boutons d'override pour les champs facultatifs
    this.setupOverrideButtons();
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
    
    // Initialiser les écouteurs d'événements pour la soumission du formulaire
    this.setupFormSubmission();
    
    // Initialiser l'affichage du bouton de soumission
    this.updateSubmitButtonText();
    
    // Ajouter un gestionnaire pour gérer les événements de rechargement/navigation
    window.addEventListener('beforeunload', () => {
      // Nettoyer les modales et backdrops avant de quitter la page
      this.cleanupModal();
    });
    
    console.log('UserCreationUtils: Initialization complete');
  }
};

