// Initialize the verification state variables
window.nameVerified = false;
window.favvNatNrVerified = false;

// Global updateSubmitButtonText function
function updateSubmitButtonText() {
    const submitButton = document.getElementById('submitBtn');
    if (!submitButton) return;
    
    // Access the window global variables
    const nameVerified = window.nameVerified || false;
    const favvNatNrVerified = window.favvNatNrVerified || false;
    
    // Check if user type requires FavvNatNr
    const userTypeSelect = document.getElementById('user_type');
    const userTypeRequiresFavvNatNr = userTypeSelect && 
                                     (userTypeSelect.value === 'BOODOCI' || 
                                      userTypeSelect.value === 'OCI');
    
    if (nameVerified && (favvNatNrVerified || !userTypeRequiresFavvNatNr)) {
        submitButton.textContent = 'Preview & Create User';
        submitButton.classList.remove('btn-secondary');
        submitButton.classList.add('btn-primary');
        
        // Change the event handler to validation and creation
        submitButton.removeEventListener('click', verifyUserInfo);
        submitButton.addEventListener('click', validateForm);
    } else {
        submitButton.textContent = 'Verify User Information';
        submitButton.classList.remove('btn-primary');
        submitButton.classList.add('btn-secondary');
        
        // Change the event handler to verification
        submitButton.removeEventListener('click', validateForm);
        submitButton.addEventListener('click', verifyUserInfo);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Get the current LDAP source
    const currentLdapSource = document.getElementById('current_ldap_source')?.value || 'meta';
    
    // State variables to track verification status
    let userTypeRequiresFavvNatNr = false;
    
    // Update the submit button text initially
    updateSubmitButtonText();
    
    // Setup the initial event handler for the submit button
    const submitButton = document.getElementById('submitBtn');
    if (submitButton) {
        submitButton.addEventListener('click', verifyUserInfo);
    }
    
    // Add LDAP source to all links that don't already have it
    document.querySelectorAll('a[href]').forEach(function(link) {
        // Only process internal links
        if (link.href && link.href.startsWith(window.location.origin)) {
            if (!link.href.includes('source=')) {
                try {
                    const url = new URL(link.href);
                    url.searchParams.set('source', currentLdapSource);
                    link.href = url.toString();
                } catch (e) {
                    // Handle edge cases for malformed URLs
                    const href = link.href;
                    if (href.includes('?')) {
                        link.href = href + '&source=' + currentLdapSource;
                    } else {
                        link.href = href + '?source=' + currentLdapSource;
                    }
                }
            }
        }
    });
    
    // Add LDAP source to all forms that don't already have it
    document.querySelectorAll('form').forEach(function(form) {
        // Check if the form already has an ldap_source input
        let hasLdapSource = false;
        form.querySelectorAll('input').forEach(function(input) {
            if (input.name === 'ldap_source') {
                hasLdapSource = true;
                input.value = currentLdapSource;
            }
        });
        
        // If not, add a hidden input for ldap_source
        if (!hasLdapSource) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'ldap_source';
            input.value = currentLdapSource;
            form.appendChild(input);
        }
    });
    
    // Show/hide FavvNatNr field based on user type selection
    const userTypeSelect = document.getElementById('user_type');
    const favvNatNrContainer = document.getElementById('favvNatNr_container');
    const managerContainer = document.getElementById('manager_container');
    
    if (userTypeSelect && favvNatNrContainer && managerContainer) {
        // Fonctions pour gérer l'état des overrides
        function updateOverrideUI(fieldId, overrideActive) {
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
        }
        
        // Fonction pour préparer les modales selon l'état d'override
        function prepareOverrideModal(fieldId, modalId) {
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
        }
        
        // Gestionnaires d'événements pour les boutons d'override
        const emailOverrideBtn = document.getElementById('emailOverrideBtn');
        if (emailOverrideBtn) {
            emailOverrideBtn.addEventListener('click', function() {
                prepareOverrideModal('email', 'emailWarningModal');
            });
        }
        
        const favvNatNrOverrideBtn = document.getElementById('favvNatNrOverrideBtn');
        if (favvNatNrOverrideBtn) {
            favvNatNrOverrideBtn.addEventListener('click', function() {
                prepareOverrideModal('favvNatNr', 'favvNatNrWarningModal');
            });
        }
        
        const managerOverrideBtn = document.getElementById('managerOverrideBtn');
        if (managerOverrideBtn) {
            managerOverrideBtn.addEventListener('click', function() {
                prepareOverrideModal('manager', 'managerWarningModal');
            });
        }
        
        // Initialiser l'UI basée sur les valeurs stockées (utile pour préserver l'état après erreur de formulaire)
        const fields = ['email', 'favvNatNr', 'manager'];
        fields.forEach(field => {
            const overrideInput = document.getElementById(field + '_override');
            if (overrideInput && overrideInput.value === 'true') {
                updateOverrideUI(field, true);
            }
        });
        
        // Function to toggle visibility of fields based on user type
        function toggleFields() {
            // OCI types
            const userType = userTypeSelect.value;
            userTypeRequiresFavvNatNr = (userType === 'BOODOCI' || userType === 'OCI');
            
            if (userTypeRequiresFavvNatNr) {
                favvNatNrContainer.style.display = 'block';
                // Reset verification status for FavvNatNr when user type changes
                window.favvNatNrVerified = false;
            } else {
                favvNatNrContainer.style.display = 'none';
                // No need to verify FavvNatNr if not required
                window.favvNatNrVerified = true;
            }
            
            // STAG type (trainee)
            if (userType === 'STAG') {
                managerContainer.style.display = 'block';
            } else {
                managerContainer.style.display = 'none';
            }
            
            // Reset name verification status when user type changes
            window.nameVerified = false;
            updateSubmitButtonText();
        }
        
        // Initial check
        toggleFields();
        
        // Listen for changes to user type
        userTypeSelect.addEventListener('change', toggleFields);
        
        // Reset verification when name fields change
        const givenNameInput = document.getElementById('givenName');
        const snInput = document.getElementById('sn');
        
        if (givenNameInput) {
            givenNameInput.addEventListener('input', function() {
                window.nameVerified = false;
                updateSubmitButtonText();
            });
        }
        
        if (snInput) {
            snInput.addEventListener('input', function() {
                window.nameVerified = false;
                updateSubmitButtonText();
            });
        }
        
        // FavvNatNr normalization
        const favvNatNrInput = document.getElementById('favvNatNr');
        if (favvNatNrInput) {
            favvNatNrInput.addEventListener('input', function(e) {
                // Remove all non-digit characters
                const normalized = e.target.value.replace(/[^0-9]/g, '');
                
                // Update input value with normalized string
                e.target.value = normalized;
                
                // Reset verification status
                window.favvNatNrVerified = false;
                updateSubmitButtonText();
            });
        }
        
        // Manager Autocomplete
        const managerInput = $('#manager');
        if (managerInput.length > 0 && managerInput.autocomplete) {
            managerInput.autocomplete({
                source: function(request, response) {
                    $.getJSON(window.autocompleteManagersUrl, {
                        term: request.term,
                        source: currentLdapSource
                    }, function(data) {
                        response(data);
                    });
                },
                select: function(event, ui) {
                    managerInput.val(ui.item.value);
                    return false;
                },
                minLength: 2
            }).data('ui-autocomplete')._renderItem = function(ul, item) {
                return $('<li>')
                    .append(`<div>${item.label}</div>`)
                    .appendTo(ul);
            };
        }
    }
});

// Function to perform user verification before creation
function verifyUserInfo(event) {
    event.preventDefault();
    
    // Get form elements
    const form = document.getElementById('userCreationForm');
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const userTypeSelect = document.getElementById('user_type');
    const favvNatNrInput = document.getElementById('favvNatNr');
    const favvNatNrContainer = document.getElementById('favvNatNr_container');
    const ldapSource = document.getElementById('current_ldap_source')?.value || 'meta';
    
    // Check if required fields are filled
    if (!form || !givenNameInput || !snInput || !userTypeSelect) return false;
    
    if (!form.checkValidity()) {
        // Trigger native browser validation
        form.reportValidity();
        return false;
    }
    
    // Determine if we need to verify FavvNatNr
    const userTypeRequiresFavvNatNr = (userTypeSelect.value === 'BOODOCI' || userTypeSelect.value === 'OCI');
    const needFavvNatNrVerification = userTypeRequiresFavvNatNr && 
                                     favvNatNrContainer.style.display !== 'none' && 
                                     favvNatNrInput && 
                                     favvNatNrInput.value.trim() !== '';
    
    // Get values
    const givenName = givenNameInput.value.trim();
    const sn = snInput.value.trim();
    const favvNatNr = favvNatNrInput?.value.trim() || '';
    
    // Initialize verification promises
    const promises = [];
    
    // Create modal content container
    const verificationResults = document.createElement('div');
    
    // Push name verification promise
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
            } else {
                alert.innerHTML = `<i class="fas fa-check-circle"></i> Aucun utilisateur existant avec le nom '${sn} ${givenName}'.`;
                // Mark name as verified
                window.nameVerified = true;
            }
            
            resultDiv.appendChild(alert);
            verificationResults.appendChild(resultDiv);
            
            return data;
        })
    );
    
    // Push FavvNatNr verification promise if needed
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
                
                if (data.status !== 'exists') {
                    // Mark FavvNatNr as verified
                    window.favvNatNrVerified = true;
                }
                
                resultDiv.appendChild(alert);
                verificationResults.appendChild(resultDiv);
                
                return data;
            })
        );
    } else {
        // No need to verify FavvNatNr
        window.favvNatNrVerified = true;
    }
    
    // Wait for all verifications to complete
    Promise.all(promises)
        .then(results => {
            // Display verification results in modal
            const verificationModal = document.getElementById('verificationModal');
            const verificationModalBody = document.getElementById('verificationModalBody');
            
            if (verificationModal && verificationModalBody) {
                verificationModalBody.innerHTML = '';
                verificationModalBody.appendChild(verificationResults);
                
                // Add conclusion and next steps
                const conclusion = document.createElement('div');
                conclusion.className = 'mt-3';
                
                if (window.nameVerified && window.favvNatNrVerified) {
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
                
                verificationModalBody.appendChild(conclusion);
                
                // Show verification modal
                const modal = new bootstrap.Modal(verificationModal);
                modal.show();
                
                // Update submit button text
                updateSubmitButtonText();
            }
        })
        .catch(error => {
            console.error('Error during verification:', error);
            alert('Une erreur est survenue pendant la vérification. Veuillez réessayer.');
        });
    
    return false;
}

// Fonction de validation du formulaire après vérification
function validateForm(event) {
    event.preventDefault();
    
    // Get current LDAP source
    const currentLdapSource = document.getElementById('current_ldap_source')?.value || 'meta';
    
    // Check form validity
    const form = document.getElementById('userCreationForm');
    if (!form) return false;
    
    if (!form.checkValidity()) {
        // Activer la validation native du navigateur
        form.reportValidity();
        return false;
    }
    
    // Check required fields with overrides
    const emailField = document.getElementById('email');
    const emailOverrideInput = document.getElementById('email_override');
    
    if (emailField && emailOverrideInput) {
        const emailOverride = emailOverrideInput.value === 'true';
        if (!emailField.value && !emailOverride) {
            alert('Email address is required. Use the override button if you want to proceed without an email.');
            return false;
        }
    }
    
    // Check FavvNatNr if needed
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
    
    // Check Manager if needed
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
    
    // Récupérer le CN et le mot de passe avant d'afficher la modal
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const userTypeInput = document.getElementById('user_type');
    
    if (!givenNameInput || !snInput || !userTypeInput) return false;
    
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
            ldap_source: currentLdapSource
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Erreur lors de la prévisualisation: ' + data.error);
            return;
        }
        
        // Remplir la modal avec les données
        populateConfirmationModal(data.cn, data.password, data.template_details);
        
        // Afficher la modal de confirmation
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const confirmationModal = document.getElementById('confirmationModal');
            if (confirmationModal) {
                const modal = new bootstrap.Modal(confirmationModal);
                modal.show();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Une erreur est survenue lors de la prévisualisation des détails utilisateur.');
    });
    
    return false; // Empêcher la soumission normale du formulaire
}

// Populate the confirmation modal with user info
function populateConfirmationModal(cn, password, template_details) {
    const userTypeSelect = document.getElementById('user_type');
    const givenNameInput = document.getElementById('givenName');
    const snInput = document.getElementById('sn');
    const emailInput = document.getElementById('email');
    const favvNatNrInput = document.getElementById('favvNatNr');
    const managerInput = document.getElementById('manager');
    const ldapSourceInput = document.getElementById('current_ldap_source');
    const userSummaryDiv = document.getElementById('userSummary');
    
    if (!userTypeSelect || !givenNameInput || !snInput || !emailInput || 
        !favvNatNrInput || !managerInput || !ldapSourceInput || !userSummaryDiv) {
        return;
    }
    
    const userTypeText = userTypeSelect.options[userTypeSelect.selectedIndex]?.text || userTypeSelect.value;
    const givenName = givenNameInput.value;
    const sn = snInput.value;
    const email = emailInput.value || 'No email specified (Override)';
    const favvNatNr = favvNatNrInput.value || 'No National Register Number (Override)';
    const manager = managerInput.value || 'No manager specified (Override)';
    const currentLdapSource = ldapSourceInput.value || 'meta';
    
    // Créer le HTML pour le résumé
    let html = `
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
                <td><code>${password}</code></td>
            </tr>
            <tr>
                <th>Email:</th>
                <td>${email}</td>
            </tr>
            <tr>
                <th>LDAP Source:</th>
                <td>${currentLdapSource}</td>
            </tr>`;
    
    // Add conditional fields
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
    
    // Add template details if available
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

        if (template_details && template_details.groups_info && template_details.groups_info.length > 0) {
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
    
    // Set the HTML in the modal
    userSummaryDiv.innerHTML = html;
    
    // Peupler également le formulaire caché pour la soumission
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
    if (hiddenLdapSourceInput) hiddenLdapSourceInput.value = currentLdapSource;
}