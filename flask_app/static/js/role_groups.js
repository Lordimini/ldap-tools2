$(function() {
    // Get the current LDAP source
    const ldapSource = $('#current_ldap_source')?.val() || 'meta';
    
    // Role CN autocomplete
    const roleCnInput = $('#role_cn');
    if (roleCnInput.length > 0 && roleCnInput.autocomplete) {
        roleCnInput.autocomplete({
            source: function(request, response) {
                $.getJSON(window.autocompleteRolesUrl, {
                    term: request.term,
                    source: ldapSource
                }, function(data) {
                    response(data);
                });
            },
            select: function(event, ui) {
                roleCnInput.val(ui.item.value);
                return false;
            },
            minLength: 2
        }).data('ui-autocomplete')._renderItem = function(ul, item) {
            return $('<li>')
                .append(`<div>${item.label}</div>`)
                .appendTo(ul);
        };
    }
    
    // Initialize DataTables for groups table if it exists
    const groupsTable = $('#groupsTable');
    if (groupsTable.length > 0) {
        if ($.fn.DataTable && $.fn.DataTable.isDataTable('#groupsTable')) {
            groupsTable.DataTable().destroy();
        }
        
        if ($.fn.DataTable) {
            groupsTable.DataTable({
                responsive: true,
                paging: true,
                pageLength: 10,
                lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
                searching: true,
                info: true,
                order: [[0, 'asc']], // Default sorting by Group Name
                language: {
                    search: "",
                    searchPlaceholder: "Search groups...",
                    zeroRecords: "No matching groups found",
                    info: "Showing _START_ to _END_ of _TOTAL_ groups",
                    infoEmpty: "No groups found",
                    infoFiltered: "(filtered from _MAX_ total groups)"
                }
            });
            
            // Make DataTables search box more Bootstrap-like
            $('.dataTables_filter input').addClass('form-control');
            $('.dataTables_filter input').css('margin-left', '0.5em');
            $('.dataTables_length select').addClass('form-select form-select-sm');
            $('.dataTables_length select').css('width', 'auto');
        }
    }
    
    // // Search tip for wildcard search
    // const cardForm = $('.card form');
    // if (cardForm.length > 0) {
    //     const wildcardTip = `
    //         <div class="alert alert-info mt-2">
    //             <i class="bi bi-info-circle-fill"></i> 
    //             <strong>Search tip:</strong> You can use the asterisk (*) as a wildcard. 
    //         </div>
    //     `;
    //     cardForm.append(wildcardTip);
    // }
    
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