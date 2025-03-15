/**
 * Utilitaires pour la gestion des groupes et des utilisateurs dans les groupes
 */
const GroupManagementUtils = {
    /**
     * Utilisateurs sélectionnés pour l'ajout à un groupe
     */
    selectedUsers: [],
    
    /**
     * Groupes sélectionnés pour l'ajout
     */
    groupsToAdd: [],
    
    /**
     * Groupes sélectionnés pour la suppression
     */
    groupsToRemove: [],
    
    /**
     * Initialise la gestion des utilisateurs pour l'ajout à un groupe
     * @param {Array} initialUsers - Utilisateurs initialement sélectionnés (facultatif)
     */
    initUserSelection: function(initialUsers = []) {
      this.selectedUsers = initialUsers || [];
      this.updateSelectedUsersUI();
      
      // Gestionnaire pour le bouton d'ajout d'utilisateur
      $(document).on('click', '.add-user-btn', function() {
        const dn = $(this).data('dn');
        const cn = $(this).data('cn');
        const fullName = $(this).data('fullname');
        
        // Vérifier si l'utilisateur est déjà dans la liste sélectionnée
        if (!GroupManagementUtils.selectedUsers.some(user => user.dn === dn)) {
          GroupManagementUtils.selectedUsers.push({
            dn: dn,
            cn: cn,
            fullName: fullName
          });
          
          GroupManagementUtils.updateSelectedUsersUI();
          
          // Changer le bouton en "Added" et le désactiver
          $(this).removeClass('btn-success').addClass('btn-secondary')
                 .html('<i class="bi bi-check-circle"></i> Added')
                 .prop('disabled', true);
        }
      });
      
      // Gestionnaire pour le bouton de suppression d'utilisateur
      $(document).on('click', '.remove-user-btn', function() {
        const index = $(this).data('index');
        if (index >= 0 && index < GroupManagementUtils.selectedUsers.length) {
          const removedUser = GroupManagementUtils.selectedUsers[index];
          
          // Supprimer l'utilisateur du tableau
          GroupManagementUtils.selectedUsers.splice(index, 1);
          GroupManagementUtils.updateSelectedUsersUI();
          
          // Si l'utilisateur est dans les résultats de recherche, réinitialiser son bouton
          $(`.add-user-btn[data-dn="${removedUser.dn}"]`)
            .removeClass('btn-secondary').addClass('btn-success')
            .html('<i class="bi bi-plus-circle"></i> Add')
            .prop('disabled', false);
        }
      });
      
      // Gestionnaire pour le formulaire de recherche d'utilisateurs
      $('#userSearchForm').on('submit', function(e) {
        // Mettre à jour le champ caché avec les utilisateurs actuellement sélectionnés
        $('#hidden_selected_users').val(JSON.stringify(GroupManagementUtils.selectedUsers));
      });
      
      // Gestionnaire pour le bouton de traitement des CN en masse
      $('#processBulkCNButton').on('click', function() {
        // Montrer le spinner, cacher le texte
        $('#processBulkCNButtonText').addClass('d-none');
        $('#processBulkCNSpinner').removeClass('d-none');
        
        // Obtenir les CN depuis la zone de texte
        const cnText = $('#bulkCNInput').val()?.trim() || '';
        if (!cnText) {
          alert('Please enter at least one CN.');
          // Réinitialiser le bouton
          $('#processBulkCNButtonText').removeClass('d-none');
          $('#processBulkCNSpinner').addClass('d-none');
          return;
        }
        
        // Analyser la liste des CN (séparés par des sauts de ligne, supprimer les lignes vides)
        const cnList = cnText.split('\n')
          .map(cn => cn.trim())
          .filter(cn => cn);
        
        if (cnList.length === 0) {
          alert('No valid CNs found.');
          // Réinitialiser le bouton
          $('#processBulkCNButtonText').removeClass('d-none');
          $('#processBulkCNSpinner').addClass('d-none');
          return;
        }
        
        // Faire une requête AJAX pour valider et obtenir les détails des utilisateurs
        $.ajax({
          url: window.validateBulkCNsUrl,
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({
            cn_list: cnList,
            group_dn: $('#group_dn').val() || '',
            ldap_source: LDAPUtils.getCurrentSource()
          }),
          success: function(response) {
            // Traiter les utilisateurs valides
            if (response.valid_users && response.valid_users.length > 0) {
              // Ajouter chaque utilisateur valide aux utilisateurs sélectionnés
              response.valid_users.forEach(user => {
                // Vérifier si l'utilisateur est déjà dans la liste sélectionnée
                if (!GroupManagementUtils.selectedUsers.some(u => u.dn === user.dn)) {
                  GroupManagementUtils.selectedUsers.push({
                    dn: user.dn,
                    cn: user.cn,
                    fullName: user.fullName
                  });
                }
              });
              
              // Mettre à jour l'interface
              GroupManagementUtils.updateSelectedUsersUI();
              
              // Afficher un message de succès
              alert(`Added ${response.valid_users.length} users. ${response.invalid_users.length} CNs were invalid or already in the group.`);
            } else {
              alert('No valid users found. Make sure the CNs exist and are not already in the group.');
            }
            
            // Fermer la modal
            $('#bulkCNModal').modal('hide');
          },
          error: function(xhr, status, error) {
            console.error("Error validating CNs:", error);
            alert('Error processing CNs. Please try again.');
          },
          complete: function() {
            // Réinitialiser le bouton
            $('#processBulkCNButtonText').removeClass('d-none');
            $('#processBulkCNSpinner').addClass('d-none');
            
            // Effacer la zone de texte
            $('#bulkCNInput').val('');
          }
        });
      });
    },
    
    /**
     * Met à jour l'interface utilisateur basée sur les utilisateurs sélectionnés
     */
    updateSelectedUsersUI: function() {
      const container = $('#selected_users_list');
      
      if (!container.length) return;
      
      // Effacer le contenu précédent sauf le message "aucun utilisateur"
      container.find('.list-group-item').remove();
      
      const noUsersMessage = $('#no_users_message');
      const confirmAddBtn = $('#confirm_add_btn');
      
      if (this.selectedUsers.length === 0) {
        if (noUsersMessage.length) noUsersMessage.show();
        if (confirmAddBtn.length) confirmAddBtn.prop('disabled', true);
      } else {
        if (noUsersMessage.length) noUsersMessage.hide();
        if (confirmAddBtn.length) confirmAddBtn.prop('disabled', false);
        
        // Ajouter chaque utilisateur sélectionné à la liste
        this.selectedUsers.forEach(function(user, index) {
          container.append(`
            <div class="list-group-item d-flex justify-content-between align-items-center">
              <div>
                <strong>${user.cn}</strong> - ${user.fullName}
              </div>
              <button type="button" class="btn btn-sm btn-danger remove-user-btn" data-index="${index}">
                <i class="bi bi-x-circle"></i> Remove
              </button>
            </div>
          `);
        });
      }
      
      // Mettre à jour les champs cachés avec les données JSON
      const jsonData = JSON.stringify(this.selectedUsers);
      $('#selected_users_data').val(jsonData);
      $('#hidden_selected_users').val(jsonData);
    },
    
    /**
     * Initialise la gestion des groupes à ajouter
     */
    initGroupsToAdd: function() {
      this.groupsToAdd = [];
      this.updateGroupsToAddDisplay();
      
      // Gestionnaire pour le bouton d'ajout de groupe
      $('#add_group_btn').click(function() {
        const groupName = $('#group_name').val()?.trim() || '';
        if (groupName) {
          // Vérifier si le groupe existe déjà dans notre sélection
          if (!GroupManagementUtils.groupsToAdd.some(g => g.name === groupName)) {
            // Créer un objet groupe avec le nom et le DN si disponible
            const groupDN = $('#group_name').data('dn') || "";
            const newGroup = {
              name: groupName,
              dn: groupDN
            };
            
            // Ajouter à notre tableau
            GroupManagementUtils.groupsToAdd.push(newGroup);
            
            // Mettre à jour l'affichage et le champ caché
            GroupManagementUtils.updateGroupsToAddDisplay();
            
            // Effacer le champ de saisie et le DN stocké
            $('#group_name').val('');
            $('#group_name').data('dn', '');
          } else {
            alert('This group is already in your selection.');
          }
        }
      });
      
      // Gestionnaire pour le formulaire de validation
      const userCompletionForm = $('#userCompletionForm');
      if (userCompletionForm.length > 0) {
        userCompletionForm.submit(function(e) {
          // S'assurer que le champ caché a les dernières données de groupe
          $('#selected_groups_data').val(JSON.stringify(GroupManagementUtils.groupsToAdd));
          
          // Continuer avec la soumission du formulaire
          return true;
        });
      }
    },
    
    /**
     * Met à jour l'affichage des groupes à ajouter
     */
    updateGroupsToAddDisplay: function() {
      const container = $('#selected_groups');
      if (!container.length) return;
      
      container.empty();
      
      if (this.groupsToAdd.length === 0) {
        container.append('<div class="text-muted">No groups selected</div>');
      } else {
        this.groupsToAdd.forEach((group, index) => {
          container.append(`
            <div class="badge bg-primary me-2 mb-2 p-2">
              ${group.name}
              <button type="button" class="btn-close btn-close-white ms-2" 
                      style="font-size: 0.5rem;" 
                      onclick="GroupManagementUtils.removeAddGroup(${index})"></button>
            </div>
          `);
        });
      }
      
      // Mettre à jour le champ caché avec les données JSON
      $('#selected_groups_data').val(JSON.stringify(this.groupsToAdd));
    },
    
    /**
     * Supprime un groupe de la liste des groupes à ajouter
     * @param {number} index - Index du groupe à supprimer
     */
    removeAddGroup: function(index) {
      if (index >= 0 && index < this.groupsToAdd.length) {
        this.groupsToAdd.splice(index, 1);
        this.updateGroupsToAddDisplay();
      }
    },
    
    /**
     * Initialise la gestion des groupes à supprimer
     * @param {Array} userGroups - Liste des groupes de l'utilisateur pour l'autocomplétion
     */
    initGroupsToRemove: function(userGroups = []) {
      this.groupsToRemove = [];
      this.updateGroupsToRemoveDisplay();
      
      // Autocomplétion - Afficher uniquement les groupes dont l'utilisateur est membre
      const groupRemoveInput = $('#group_remove');
      if (groupRemoveInput.length > 0 && groupRemoveInput.autocomplete) {
        groupRemoveInput.autocomplete({
          source: function(request, response) {
            const term = request.term.toLowerCase();
            
            // Filtrer les groupes actuels en fonction de la saisie
            if (userGroups && userGroups.length > 0) {
              const filteredGroups = userGroups.filter(group => 
                group.label.toLowerCase().includes(term)
              );
              
              response(filteredGroups);
            } else {
              response([]);
            }
          },
          minLength: 1
        });
      }
      
      // Gestionnaire pour le bouton de suppression de groupe
      $('#remove_group_btn').click(function() {
        const groupName = $('#group_remove').val()?.trim() || '';
        if (groupName) {
          // Vérifier si le groupe existe déjà dans la sélection
          if (!GroupManagementUtils.groupsToRemove.some(g => g.name === groupName)) {
            // Trouver le DN du groupe s'il existe dans les groupes actuels
            let groupDn = "";
            if (userGroups) {
              const foundGroup = userGroups.find(g => g.value === groupName);
              if (foundGroup) {
                groupDn = foundGroup.dn || "";
              }
            }
            
            GroupManagementUtils.groupsToRemove.push({
              name: groupName,
              dn: groupDn
            });
            
            GroupManagementUtils.updateGroupsToRemoveDisplay();
            $('#group_remove').val('');
          }
        }
      });
    },
    
    /**
     * Met à jour l'affichage des groupes à supprimer
     */
    updateGroupsToRemoveDisplay: function() {
      const container = $('#groups_to_remove');
      if (!container.length) return;
      
      container.empty();
      
      if (this.groupsToRemove.length === 0) {
        container.append('<div class="text-muted">No groups selected to remove</div>');
      } else {
        this.groupsToRemove.forEach((group, index) => {
          container.append(`
            <div class="badge bg-danger me-2 mb-2 p-2">
              ${group.name}
              <button type="button" class="btn-close btn-close-white ms-2" 
                      style="font-size: 0.5rem;" 
                      onclick="GroupManagementUtils.removeRemoveGroup(${index})"></button>
            </div>
          `);
        });
      }
      
      // Mettre à jour le champ caché avec les données JSON
      $('#groups_to_remove_data').val(JSON.stringify(this.groupsToRemove));
    },
    
    /**
     * Supprime un groupe de la liste des groupes à supprimer
     * @param {number} index - Index du groupe à supprimer
     */
    removeRemoveGroup: function(index) {
      if (index >= 0 && index < this.groupsToRemove.length) {
        this.groupsToRemove.splice(index, 1);
        this.updateGroupsToRemoveDisplay();
      }
    },
    
    /**
     * Initialise les filtres et tris pour les groupes et rôles
     */
    initSortAndFilter: function() {
      // Variables pour le tri
      let groupSortAsc = true;
      let roleSortAsc = true;
      
      // Groupes - Filtrer
      $('#group-filter').on('keyup', function() {
        const filter = $(this).val()?.toLowerCase() || '';
        $('.group-badge').each(function() {
          const text = $(this).text().toLowerCase();
          $(this).toggle(text.indexOf(filter) > -1);
        });
      });
      
      // Rôles - Filtrer
      $('#role-filter').on('keyup', function() {
        const filter = $(this).val()?.toLowerCase() || '';
        $('.role-badge').each(function() {
          const text = $(this).text().toLowerCase();
          $(this).toggle(text.indexOf(filter) > -1);
        });
      });
      
      // Groupes - Trier
      $('#sort-groups').click(function() {
        const groups = $('#groups .group-badge').get();
        if (groups.length > 0) {
          groups.sort(function(a, b) {
            const textA = $(a).text().trim().toLowerCase();
            const textB = $(b).text().trim().toLowerCase();
            return groupSortAsc ? (textA > textB ? 1 : -1) : (textA < textB ? 1 : -1);
          });
          
          // Changer l'icône
          $(this).find('i').toggleClass('bi-sort-alpha-down bi-sort-alpha-up');
          
          // Inverser pour le prochain clic
          groupSortAsc = !groupSortAsc;
          
          // Réinsérer les éléments triés
          $.each(groups, function(index, group) {
            $('#groups').append(group);
          });
        }
      });
      
      // Rôles - Trier
      $('#sort-roles').click(function() {
        const roles = $('#roles .role-badge').get();
        if (roles.length > 0) {
          roles.sort(function(a, b) {
            const textA = $(a).text().trim().toLowerCase();
            const textB = $(b).text().trim().toLowerCase();
            return roleSortAsc ? (textA > textB ? 1 : -1) : (textA < textB ? 1 : -1);
          });
          
          // Changer l'icône
          $(this).find('i').toggleClass('bi-sort-alpha-down bi-sort-alpha-up');
          
          // Inverser pour le prochain clic
          roleSortAsc = !roleSortAsc;
          
          // Réinsérer les éléments triés
          $.each(roles, function(index, role) {
            $('#roles').append(role);
          });
        }
      });
    }
  }