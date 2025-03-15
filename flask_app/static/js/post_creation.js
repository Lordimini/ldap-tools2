// JavaScript code for the post-creation page
$(document).ready(function() {
    // Get the current LDAP source
    const ldapSource = $('#current_ldap_source')?.val() || 'meta';
    
    // Initialize the selected groups array
    let selectedGroups = [];
    
    // Initialize the hidden field with empty array
    $('#selected_groups_data').val(JSON.stringify(selectedGroups));
    
    // Call updateSelectedGroupsDisplay once to initialize the UI
    updateSelectedGroupsDisplay();
    
    // Manager Autocomplete
    const hierarchicalManagerInput = $('#hierarchical_manager');
    if (hierarchicalManagerInput.length > 0 && hierarchicalManagerInput.autocomplete) {
        hierarchicalManagerInput.autocomplete({
            source: function(request, response) {
                $.getJSON(window.autocompleteManagersUrl, {
                    term: request.term,
                    source: ldapSource
                }, function(data) {
                    response(data);
                });
            },
            select: function(event, ui) {
                hierarchicalManagerInput.val(ui.item.value);
                // Extract DN from label (format is "fullName - email - title (DN)")
                const dnMatch = ui.item.label.match(/\((.*?)\)$/);
                if (dnMatch && dnMatch[1]) {
                    $('#manager_dn').val(dnMatch[1]);
                }
                return false;
            },
            minLength: 2
        });
    }
    
    // Group Autocomplete
    const groupNameInput = $('#group_name');
    if (groupNameInput.length > 0 && groupNameInput.autocomplete) {
        groupNameInput.autocomplete({
            source: function(request, response) {
                $.getJSON(window.autocompleteGroupsUrl, {
                    term: request.term,
                    source: ldapSource
                }, function(data) {
                    response(data);
                });
            },
            select: function(event, ui) {
                groupNameInput.val(ui.item.value);
                // Store the DN if available in the response
                const dnMatch = ui.item.label.match(/\((.*?)\)$/);
                if (dnMatch && dnMatch[1]) {
                    groupNameInput.data('dn', dnMatch[1]);
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
                    source: ldapSource
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
    
    // Add Group Button Click Handler
    $('#add_group_btn').click(function() {
        const groupName = groupNameInput.val()?.trim() || '';
        if (groupName) {
            // Check if group already exists in the user's current memberships
            const currentGroups = [];
            $('#current_groups .badge').each(function() {
                currentGroups.push($(this).text().trim());
            });
            
            // Check if the group is already in current memberships
            if (currentGroups.includes(groupName)) {
                alert('This group is already assigned to the user.');
                groupNameInput.val('');
                return;
            }
            
            // Check if group already exists in our selection
            if (!selectedGroups.some(g => g.name === groupName)) {
                // Create a group object with the name and DN if available
                const groupDN = groupNameInput.data('dn') || "";
                const newGroup = {
                    name: groupName,
                    dn: groupDN
                };
                
                console.log("Adding group:", newGroup);
                
                // Add to our array
                selectedGroups.push(newGroup);
                
                // Update the display and hidden field
                updateSelectedGroupsDisplay();
                
                // Clear the input field and stored DN
                groupNameInput.val('');
                groupNameInput.data('dn', '');
            } else {
                alert('This group is already in your selection.');
            }
        }
    });
    
    // Submit form handler to validate before submission
    const userCompletionForm = $('#userCompletionForm');
    if (userCompletionForm.length > 0) {
        userCompletionForm.submit(function(e) {
            // Make sure the hidden field has the latest group data
            $('#selected_groups_data').val(JSON.stringify(selectedGroups));
            console.log("Form submission - Groups data:", $('#selected_groups_data').val());
            
            // Continue with form submission
            return true;
        });
    }
    
    // Define the update function
    function updateSelectedGroupsDisplay() {
        const container = $('#selected_groups');
        if (!container.length) return;
        
        container.empty();
        
        if (selectedGroups.length === 0) {
            container.append('<div class="text-muted">No groups selected</div>');
        } else {
            selectedGroups.forEach((group, index) => {
                container.append(`
                    <div class="badge bg-primary me-2 mb-2 p-2">
                        ${group.name}
                        <button type="button" class="btn-close btn-close-white ms-2" 
                                style="font-size: 0.5rem;" 
                                onclick="removeGroup(${index})"></button>
                    </div>
                `);
            });
        }
        
        // Update hidden field with JSON data
        $('#selected_groups_data').val(JSON.stringify(selectedGroups));
    }
    
    // Expose removeGroup function to global scope for the onclick handlers
    window.removeGroup = function(index) {
        console.log("Removing group at index:", index);
        if (index >= 0 && index < selectedGroups.length) {
            selectedGroups.splice(index, 1);
            updateSelectedGroupsDisplay();
        }
    };
    
    // Make sure all links include the LDAP source parameter
    $('a[href]').each(function() {
        // Only process internal links
        if (this.href.startsWith(window.location.origin)) {
            const url = new URL(this.href);
            // Only add source parameter if it doesn't already exist
            if (!url.searchParams.has('source')) {
                url.searchParams.set('source', ldapSource);
                this.href = url.toString();
            }
        }
    });
    
    // Handle refresh button
    $('.refresh-btn').click(function() {
        const source = $(this).data('source') || ldapSource;
        
        // Create new URL with source parameter
        const url = new URL(window.postCreationUrl, window.location.origin);
        url.searchParams.set('source', source);
        
        // Navigate to the URL
        window.location.href = url.toString();
    });
});