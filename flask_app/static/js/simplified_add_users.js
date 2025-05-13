$(document).ready(function() {
    // Get the current LDAP source
    const ldapSource = $('#current_ldap_source').val() || 'meta';
    
    // Initialize DataTables for current members table
    if ($('#currentMembersTable').length > 0) {
        if ($.fn.DataTable.isDataTable('#currentMembersTable')) {
            $('#currentMembersTable').DataTable().destroy();
        }
        
        $('#currentMembersTable').DataTable({
            responsive: true,
            paging: true,
            pageLength: 10,
            lengthMenu: [[5, 10, 25, -1], [5, 10, 25, "All"]],
            searching: true,
            info: true,
            order: [[1, 'asc']], // Default sorting by Full Name
            language: {
                search: "",
                searchPlaceholder: "Search members...",
                zeroRecords: "No matching records found",
                info: "Showing _START_ to _END_ of _TOTAL_ members",
                infoEmpty: "No members found",
                infoFiltered: "(filtered from _MAX_ total members)"
            }
        });
        
        // Enhance DataTables styling
        $('.dataTables_filter input').addClass('form-control');
        $('.dataTables_filter input').css('margin-left', '0.5em');
        $('.dataTables_length select').addClass('form-select form-select-sm');
        $('.dataTables_length select').css('width', 'auto');
    }
    
    // Group name autocomplete
    initializeGroupAutocomplete();
    
    // Handle Bulk CN processing
    $('#processBulkCNButton').on('click', processBulkCNs);
    
    // Make sure all links include the LDAP source parameter
    enhanceLinksWithLdapSource();
    
    /**
     * Initialize autocomplete for group name field
     */
    function initializeGroupAutocomplete() {
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
    }
    
    /**
     * Process Bulk CNs from the modal
     */
    function processBulkCNs() {
        // Show spinner, hide text
        $('#processBulkCNButtonText').addClass('d-none');
        $('#processBulkCNSpinner').removeClass('d-none');
        
        // Get CNs from textarea
        const cnText = $('#bulkCNInput').val()?.trim() || '';
        if (!cnText) {
            showAlert('Please enter at least one CN.', 'warning');
            // Reset button
            resetProcessButton();
            return;
        }
        
        // Parse CN list (split by newline, remove empty lines)
        const cnList = cnText.split('\n')
            .map(cn => cn.trim())
            .filter(cn => cn);
        
        if (cnList.length === 0) {
            showAlert('No valid CNs found.', 'warning');
            resetProcessButton();
            return;
        }
        
        // Make AJAX request to validate and get user details
        const requestData = {
            cn_list: cnList,
            group_dn: $('#group_dn').val() || '',
            ldap_source: ldapSource
        };
        
        console.log("Sending data to validate_bulk_cns:", requestData);
        
        $.ajax({
            url: window.validateBulkCNsUrl,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requestData),
            success: function(response) {
                let message = '';
                
                // Process valid users
                if (response.valid_users && response.valid_users.length > 0) {
                    // Submit the valid users for addition
                    submitValidUsers(response.valid_users);
                    
                    message = `Added ${response.valid_users.length} users.`;
                    if (response.invalid_users.length > 0) {
                        message += ` ${response.invalid_users.length} CNs were invalid or already in the group.`;
                    }
                    
                    showAlert(message, 'success');
                } else {
                    showAlert('No valid users found. Make sure the CNs exist and are not already in the group.', 'warning');
                }
                
                // Close modal
                $('#bulkCNModal').modal('hide');
            },
            error: function(xhr, status, error) {
                console.error("Error validating CNs:", error);
                showAlert('Error processing CNs. Please try again.', 'danger');
            },
            complete: function() {
                resetProcessButton();
                
                // Clear textarea
                $('#bulkCNInput').val('');
            }
        });
    }
    
    /**
     * Submit valid users to be added to the group
     */
    function submitValidUsers(validUsers) {
        console.log("Submitting valid users:", validUsers);
        
        // Get the correct URL for the confirm_add_users route
        const confirmUrl = window.confirmAddUsersUrl || "/add_users_to_group/confirm_add_users";
        
        // Create a form to submit
        const form = $('<form>', {
            'method': 'POST',
            'action': confirmUrl
        });
        
        // Add the necessary fields
        form.append($('<input>', {
            'type': 'hidden',
            'name': 'ldap_source',
            'value': ldapSource
        }));
        
        form.append($('<input>', {
            'type': 'hidden',
            'name': 'group_name',
            'value': $('#group_name').val()
        }));
        
        form.append($('<input>', {
            'type': 'hidden',
            'name': 'group_dn',
            'value': $('#group_dn').val()
        }));
        
        form.append($('<input>', {
            'type': 'hidden',
            'name': 'selected_users',
            'value': JSON.stringify(validUsers)
        }));
        
        // Log the form data for debugging
        console.log("Form data:", {
            'ldap_source': ldapSource,
            'group_name': $('#group_name').val(),
            'group_dn': $('#group_dn').val(),
            'selected_users': JSON.stringify(validUsers)
        });
        
        // Add the form to the document and submit it
        $('body').append(form);
        form.submit();
    }
    
    /**
     * Reset the process button state
     */
    function resetProcessButton() {
        $('#processBulkCNButtonText').removeClass('d-none');
        $('#processBulkCNSpinner').addClass('d-none');
    }
    
    /**
     * Show an alert at the top of the page
     */
    function showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        // Add alert to the top of the container
        $('.container').prepend(alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            $('.alert').alert('close');
        }, 5000);
    }
    
    /**
     * Enhance links with LDAP source parameter
     */
    function enhanceLinksWithLdapSource() {
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
    }
});