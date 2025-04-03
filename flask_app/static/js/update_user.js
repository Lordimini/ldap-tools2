$(document).ready(function() {
    // Get the current LDAP source
    const currentLdapSource = $('input[name="ldap_source"]')?.val() || 'meta';
    
    // Add LDAP source to all links that don't already have it
    $('a[href]').each(function() {
        // Only process internal links
        if ($(this).attr('href') && $(this).attr('href').startsWith('/')) {
            if (!$(this).attr('href').includes('source=')) {
                let url;
                try {
                    url = new URL($(this).attr('href'), window.location.origin);
                    url.searchParams.set('source', currentLdapSource);
                    $(this).attr('href', url.toString());
                } catch (e) {
                    // Handle edge cases for malformed URLs
                    const href = $(this).attr('href');
                    if (href.includes('?')) {
                        $(this).attr('href', href + '&source=' + currentLdapSource);
                    } else {
                        $(this).attr('href', href + '?source=' + currentLdapSource);
                    }
                }
            }
        }
    });

    // Handle search type dropdown
    function initializeAutocomplete() {
        const searchTypeInput = $('#search_type');
        const searchTermInput = $('#search_term');
        
        if (searchTypeInput.length > 0 && searchTermInput.length > 0 && searchTermInput.autocomplete) {
            if (searchTypeInput.val() === 'fullName') {
                searchTermInput.autocomplete({
                    source: function(request, response) {
                        if (request.term.length < 3) {
                            response([]);
                            return;
                        }
                        
                        $.getJSON(window.autocompleteFullNameUrl, {
                            term: request.term,
                            source: currentLdapSource
                        }, function(data) {
                            response(data);
                        });
                    },
                    minLength: 3,
                    delay: 300,
                    select: function(event, ui) {
                        searchTermInput.val(ui.item.value);
                        return false;
                    }
                }).data('ui-autocomplete')._renderItem = function(ul, item) {
                    return $('<li>')
                        .append(`<div>${item.label}</div>`)
                        .appendTo(ul);
                };
            } else {
                // Unbind existing autocomplete if any
                searchTermInput.autocomplete('destroy');
            }
        }
    }

    // Initialize autocomplete on page load
    initializeAutocomplete();
    
    // Re-initialize when search type changes
    $('#search_type').change(function() {
        initializeAutocomplete();
    });
    
    // Manager Autocomplete
    const hierarchicalManagerInput = $('#hierarchical_manager');
    if (hierarchicalManagerInput.length > 0 && hierarchicalManagerInput.autocomplete) {
        hierarchicalManagerInput.autocomplete({
            source: function(request, response) {
                $.getJSON(window.autocompleteManagersUrl, {
                    term: request.term,
                    source: currentLdapSource
                }, function(data) {
                    response(data);
                });
            },
            select: function(event, ui) {
                hierarchicalManagerInput.val(ui.item.value);
                // Extract DN from label
                const dnMatch = ui.item.label.match(/\((.*?)\)$/);
                if (dnMatch && dnMatch[1]) {
                    $('#manager_dn').val(dnMatch[1]);
                }
                return false;
            },
            minLength: 2
        });
    }
    
    // Service (OU) Autocomplete
    const ouInput = $('#ou');
    if (ouInput.length > 0 && ouInput.autocomplete) {
        ouInput.autocomplete({
            source: function(request, response) {
                $.getJSON(window.autocompleteServicesUrl, {
                    term: request.term,
                    source: currentLdapSource
                }, function(data) {
                    response(data);
                });
            },
            select: function(event, ui) {
                ouInput.val(ui.item.value);
                return false;
            },
            minLength: 2
        });
    }
    
    // Group Add Autocomplete
    const groupNameInput = $('#group_name');
    if (groupNameInput.length > 0 && groupNameInput.autocomplete) {
        groupNameInput.autocomplete({
            source: function(request, response) {
                $.getJSON(window.autocompleteGroupsUrl, {
                    term: request.term,
                    source: currentLdapSource
                }, function(data) {
                    response(data);
                });
            },
            select: function(event, ui) {
                groupNameInput.val(ui.item.value);
                return false;
            },
            minLength: 2
        });
    }
    
    // Group Remove Autocomplete - Only show groups the user is a member of
    const groupRemoveInput = $('#group_remove');
    if (groupRemoveInput.length > 0 && groupRemoveInput.autocomplete) {
        groupRemoveInput.autocomplete({
            source: function(request, response) {
                const term = request.term.toLowerCase();
                
                // Filter current groups based on input
                if (window.userGroups && window.userGroups.length > 0) {
                    const filteredGroups = window.userGroups.filter(group => 
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
    
    // Groups to Add Management
    let groupsToAdd = [];
    
    $('#add_group_btn').click(function() {
        const groupName = groupNameInput?.val()?.trim() || '';
        if (groupName) {
            // Check if group already exists in the selection
            if (!groupsToAdd.some(g => g.name === groupName)) {
                groupsToAdd.push({
                    name: groupName,
                    dn: ""
                });
                updateGroupsToAddDisplay();
                groupNameInput.val('');
            }
        }
    });
    
    function updateGroupsToAddDisplay() {
        const container = $('#groups_to_add');
        if (!container.length) return;
        
        container.empty();
        
        if (groupsToAdd.length === 0) {
            container.append('<div class="text-muted">No groups selected to add</div>');
        } else {
            groupsToAdd.forEach((group, index) => {
                container.append(`
                    <div class="badge bg-success me-2 mb-2 p-2">
                        ${group.name}
                        <button type="button" class="btn-close btn-close-white ms-2" 
                                style="font-size: 0.5rem;" 
                                onclick="removeAddGroup(${index})"></button>
                    </div>
                `);
            });
        }
        
        // Update hidden field with JSON data
        $('#groups_to_add_data').val(JSON.stringify(groupsToAdd));
    }
    
    // Groups to Remove Management
    let groupsToRemove = [];
    
    $('#remove_group_btn').click(function() {
        const groupName = groupRemoveInput?.val()?.trim() || '';
        if (groupName) {
            // Check if group already exists in the selection
            if (!groupsToRemove.some(g => g.name === groupName)) {
                // Find the group DN if it exists in current groups
                let groupDn = "";
                if (window.userGroups) {
                    const foundGroup = window.userGroups.find(g => g.value === groupName);
                    if (foundGroup) {
                        groupDn = foundGroup.dn || "";
                    }
                }
                
                groupsToRemove.push({
                    name: groupName,
                    dn: groupDn
                });
                updateGroupsToRemoveDisplay();
                groupRemoveInput.val('');
            }
        }
    });
    
    function updateGroupsToRemoveDisplay() {
        const container = $('#groups_to_remove');
        if (!container.length) return;
        
        container.empty();
        
        if (groupsToRemove.length === 0) {
            container.append('<div class="text-muted">No groups selected to remove</div>');
        } else {
            groupsToRemove.forEach((group, index) => {
                container.append(`
                    <div class="badge bg-danger me-2 mb-2 p-2">
                        ${group.name}
                        <button type="button" class="btn-close btn-close-white ms-2" 
                                style="font-size: 0.5rem;" 
                                onclick="removeRemoveGroup(${index})"></button>
                    </div>
                `);
            });
        }
        
        // Update hidden field with JSON data
        $('#groups_to_remove_data').val(JSON.stringify(groupsToRemove));
    }
    
    // Initialize displays
    updateGroupsToAddDisplay();
    updateGroupsToRemoveDisplay();
    
    // Expose remove functions to global scope for the onclick handlers
    window.removeAddGroup = function(index) {
        if (index >= 0 && index < groupsToAdd.length) {
            groupsToAdd.splice(index, 1);
            updateGroupsToAddDisplay();
        }
    };
    
    window.removeRemoveGroup = function(index) {
        if (index >= 0 && index < groupsToRemove.length) {
            groupsToRemove.splice(index, 1);
            updateGroupsToRemoveDisplay();
        }
    };
    
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
    
    // Variables pour le tri
    let groupSortAsc = true;
    let roleSortAsc = true;
    
    // Groupes - Trier
    $('#sort-groups').click(function() {
        const groups = $('#current_groups .group-badge').get();
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
                $('#current_groups').append(group);
            });
        }
    });
    
    // Rôles - Trier
    $('#sort-roles').click(function() {
        const roles = $('#current_roles .role-badge').get();
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
                $('#current_roles').append(role);
            });
        }
    });

    // Handle tab-specific Apply Changes buttons
    $('.apply-changes-btn').on('click', function(event) {
        event.preventDefault(); // Prevent default button behavior

        const $button = $(this);
        const tabId = $button.data('tab-id');
        const $form = $('#userUpdateForm');
        const formAction = $form.attr('action');

        // Disable button to prevent multiple clicks
        $button.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');

        // Serialize the entire form data
        let formData = $form.serializeArray();

        // Add the identifier for the tab being saved
        formData.push({ name: 'update_section', value: tabId });

        // Send data via AJAX
        $.ajax({
            url: formAction,
            type: 'POST',
            data: $.param(formData), // Convert array to URL-encoded string
            dataType: 'json', // Expect JSON response from server
            success: function(response) {
                // Display success message (using alert for simplicity, consider Bootstrap toasts)
                if (response.status === 'success') {
                    alert('Success: ' + response.message);
                    // Optionally reload parts of the page or update UI based on response
                    if (tabId === 'groups' || tabId === 'roles') {
                         // Reload might be needed if group/role memberships changed display
                         // window.location.reload(); // Or more targeted update
                    }
                     if (tabId === 'DirXML') {
                         // Reload might be needed if associations changed display
                         // window.location.reload(); // Or more targeted update
                    }
                } else {
                    alert('Error: ' + (response.message || 'An unknown error occurred.'));
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // Display error message
                alert('AJAX Error: ' + textStatus + ' - ' + errorThrown);
                console.error("AJAX Error:", jqXHR.responseText);
            },
            complete: function() {
                // Re-enable button and restore original text
                 // Find the icon class (adjust if icons change)
                const iconClass = $button.find('i').attr('class') || 'bi bi-check-circle';
                // Attempt to get original text more robustly
                let originalText = $button.text().replace('Saving...', '').trim();
                if (!originalText) {
                    // Fallback based on tabId if text was completely replaced by spinner
                    switch(tabId) {
                        case 'general': originalText = 'Apply General Changes'; break;
                        case 'groups': originalText = 'Apply Group Changes'; break;
                        case 'security': originalText = 'Apply Security Changes'; break;
                        case 'account': originalText = 'Apply Account Changes'; break;
                        case 'restrictions': originalText = 'Apply Restriction Changes'; break;
                        case 'container': originalText = 'Apply Container Changes'; break;
                        case 'protime': originalText = 'Apply Protime Changes'; break;
                        case 'misc': originalText = 'Apply Miscellaneous Changes'; break;
                        default: originalText = 'Apply Changes'; // Generic fallback
                    }
                }
                $button.prop('disabled', false).html(`<i class="${iconClass}"></i> ${originalText}`);
            }
        });
    });
});

// JavaScript to handle DirXML Association deletion (UI only)
$(document).ready(function() {
    // Initialize the array of associations to delete
    let associationsToDelete = [];
    
    // Handle delete/undo button clicks
    $(document).on('click', '.delete-association-btn', function() {
        const associationIndex = $(this).data('association-index');
        const associationValue = $(this).data('association-value');
        const $button = $(this);
        const $row = $button.closest('tr');

        if ($button.hasClass('btn-secondary')) { // Handle UNDO
            // Remove from the delete list
            associationsToDelete = associationsToDelete.filter(item => item.index !== associationIndex);
            
            // Update the hidden input
            $('#associations_to_delete').val(JSON.stringify(associationsToDelete));
            
            // Restore visual appearance
            $row.removeClass('deleted-association');
            $row.find('td.text-break').removeClass('text-decoration-line-through text-muted');
            
            // Change button back to "Delete"
            $button.removeClass('btn-secondary')
                   .addClass('btn-danger')
                   .html('<i class="bi bi-trash"></i>')
                   .attr('title', 'Delete association');
            
        } else { // Handle DELETE
            // Confirm deletion
            if (confirm('Are you sure you want to delete this association?')) {
                // Add to the delete list
                associationsToDelete.push({
                    index: associationIndex,
                    value: associationValue
                });
                
                // Update the hidden input with the JSON data
                $('#associations_to_delete').val(JSON.stringify(associationsToDelete));
                
                // Visual feedback - fade out the row
                $row.fadeOut(300, function() {
                    // Add a class to indicate deleted status
                    $(this).addClass('deleted-association')
                           .removeClass('d-none') // Ensure it's not hidden if previously undone
                           .fadeIn(300);
                    
                    // Change the button to "Undo"
                    $button.removeClass('btn-danger')
                           .addClass('btn-secondary')
                           .html('<i class="bi bi-arrow-counterclockwise"></i>')
                           .attr('title', 'Undo deletion');
                    
                    // Add strikethrough to the text
                    $(this).find('td.text-break').addClass('text-decoration-line-through text-muted');
                });
            }
        }
    });
});