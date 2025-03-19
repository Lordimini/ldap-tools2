$(document).ready(function () {
    // Global variables for user selection
    // Initialize selectedUsers from passed data if available
    let selectedUsers = window.initialSelectedUsers || [];
    
    // Get the current LDAP source
    const ldapSource = $('#current_ldap_source')?.val() || 'meta';
    
    // Initialize DataTables for current members table
    const currentMembersTable = $('#currentMembersTable');
    if (currentMembersTable.length > 0) {
        if ($.fn.DataTable.isDataTable('#currentMembersTable')) {
            currentMembersTable.DataTable().destroy();
        }
        
        currentMembersTable.DataTable({
            responsive: true,
            paging: true,
            pageLength: 5,
            lengthMenu: [[5, 10, 25, -1], [5, 10, 25, "All"]],
            searching: true,
            info: true,
            order: [[1, 'asc']], // Default sorting by Full Name
            columnDefs: [
                { orderable: true, targets: [0, 1, 2, 3] }
            ],
            language: {
                search: "",
                searchPlaceholder: "Search members...",
                zeroRecords: "No matching records found",
                info: "Showing _START_ to _END_ of _TOTAL_ members",
                infoEmpty: "No members found",
                infoFiltered: "(filtered from _MAX_ total members)"
            }
        });
    }
    
    // Autocomplete for group_name with DN storage
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
                // Set the visible value (CN)
                groupNameInput.val(ui.item.value);
                
                // Store the complete DN
                const dnMatch = ui.item.label.match(/\((.*?)\)$/);
                if (dnMatch && dnMatch[1]) {
                    $('#group_dn').val(dnMatch[1]);
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
    
    // Autocomplete for user search when using fullName
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
                            source: ldapSource
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
    
    // Update the UI based on selected users
    function updateSelectedUsersUI() {
        console.log("Updating UI with users:", selectedUsers);
        const container = $('#selected_users_list');
        
        if (!container.length) return;
        
        // Clear previous content except the "no users" message
        container.find('.list-group-item').remove();
        
        const noUsersMessage = $('#no_users_message');
        const confirmAddBtn = $('#confirm_add_btn');
        
        if (selectedUsers.length === 0) {
            if (noUsersMessage.length) noUsersMessage.show();
            if (confirmAddBtn.length) confirmAddBtn.prop('disabled', true);
        } else {
            if (noUsersMessage.length) noUsersMessage.hide();
            if (confirmAddBtn.length) confirmAddBtn.prop('disabled', false);
            
            // Add each selected user to the list
            selectedUsers.forEach(function(user, index) {
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
        
        // Update hidden inputs with JSON data
        const jsonData = JSON.stringify(selectedUsers);
        $('#selected_users_data').val(jsonData);
        $('#hidden_selected_users').val(jsonData);
        console.log("Updated hidden fields with:", jsonData);
    }
    
    // Add user button click handler
    $(document).on('click', '.add-user-btn', function() {
        const dn = $(this).data('dn');
        const cn = $(this).data('cn');
        const fullName = $(this).data('fullname');
        
        // Check if user is already in selected list
        if (!selectedUsers.some(user => user.dn === dn)) {
            selectedUsers.push({
                dn: dn,
                cn: cn,
                fullName: fullName
            });
            
            updateSelectedUsersUI();
            
            // Change button to "Added" and disable it
            $(this).removeClass('btn-success').addClass('btn-secondary')
                   .html('<i class="bi bi-check-circle"></i> Added')
                   .prop('disabled', true);
        }
    });
    
    // Remove user button click handler
    $(document).on('click', '.remove-user-btn', function() {
        const index = $(this).data('index');
        if (index >= 0 && index < selectedUsers.length) {
            const removedUser = selectedUsers[index];
            
            // Remove user from array
            selectedUsers.splice(index, 1);
            updateSelectedUsersUI();
            
            // If the user is in the search results, reset their button
            $(`.add-user-btn[data-dn="${removedUser.dn}"]`)
                .removeClass('btn-secondary').addClass('btn-success')
                .html('<i class="bi bi-plus-circle"></i> Add')
                .prop('disabled', false);
        }
    });
    
    // Initialize UI with selected users data
    updateSelectedUsersUI();
    console.log("Initialized with users:", selectedUsers);
    
    // Add form submit event to ensure selected users are saved
    $('#userSearchForm').on('submit', function(e) {
        // Update the hidden field with current selected users
        $('#hidden_selected_users').val(JSON.stringify(selectedUsers));
    });
    
    // Handle bulk CN processing
    $('#processBulkCNButton').on('click', function() {
        // Show spinner, hide text
        $('#processBulkCNButtonText').addClass('d-none');
        $('#processBulkCNSpinner').removeClass('d-none');
        
        // Get CNs from textarea
        const cnText = $('#bulkCNInput').val()?.trim() || '';
        if (!cnText) {
            alert('Please enter at least one CN.');
            // Reset button
            $('#processBulkCNButtonText').removeClass('d-none');
            $('#processBulkCNSpinner').addClass('d-none');
            return;
        }
        
        // Parse CN list (split by newline, remove empty lines)
        const cnList = cnText.split('\n')
            .map(cn => cn.trim())
            .filter(cn => cn);
        
        if (cnList.length === 0) {
            alert('No valid CNs found.');
            // Reset button
            $('#processBulkCNButtonText').removeClass('d-none');
            $('#processBulkCNSpinner').addClass('d-none');
            return;
        }
        
        // Make AJAX request to validate and get user details
        $.ajax({
            url: window.validateBulkCNsUrl,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                cn_list: cnList,
                group_dn: $('#group_dn').val() || '',
                ldap_source: ldapSource
            }),
            success: function(response) {
                // Process valid users
                if (response.valid_users && response.valid_users.length > 0) {
                    // Add each valid user to selected users
                    response.valid_users.forEach(user => {
                        // Check if user is already in selected list
                        if (!selectedUsers.some(u => u.dn === user.dn)) {
                            selectedUsers.push({
                                dn: user.dn,
                                cn: user.cn,
                                fullName: user.fullName
                            });
                        }
                    });
                    
                    // Update UI
                    updateSelectedUsersUI();
                    
                    // Show success message
                    alert(`Added ${response.valid_users.length} users. ${response.invalid_users.length} CNs were invalid or already in the group.`);
                } else {
                    alert('No valid users found. Make sure the CNs exist and are not already in the group.');
                }
                
                // Close modal
                $('#bulkCNModal').modal('hide');
            },
            error: function(xhr, status, error) {
                console.error("Error validating CNs:", error);
                alert('Error processing CNs. Please try again.');
            },
            complete: function() {
                // Reset button
                $('#processBulkCNButtonText').removeClass('d-none');
                $('#processBulkCNSpinner').addClass('d-none');
                
                // Clear textarea
                $('#bulkCNInput').val('');
            }
        });
    });
    
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
        const source = $(this).data('source');
        // Determine current URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        
        // Create new URL with current parameters plus the source
        const url = new URL(window.location.pathname, window.location.origin);
        
        // Copy over all existing parameters except source
        for (const [key, value] of urlParams.entries()) {
            if (key !== 'source') {
                url.searchParams.append(key, value);
            }
        }
        
        // Add the source parameter
        url.searchParams.set('source', source);
        
        // Navigate to the URL
        window.location.href = url.toString();
    });
});