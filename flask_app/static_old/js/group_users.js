$(document).ready(function () {
    // Get the current LDAP source
    const ldapSource = $('#current_ldap_source')?.val() || 'meta';
    
    // Initialize DataTables on the table if it exists
    const usersTable = $('#usersTable');
    if (usersTable.length > 0) {
        if ($.fn.DataTable.isDataTable('#usersTable')) {
            usersTable.DataTable().destroy();
        }
        
        // Initialize DataTable with pagination and responsive features
        var table = usersTable.DataTable({
            responsive: true,
            paging: true,
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
            searching: true,
            info: true,
            order: [[1, 'asc']], // Default sorting by Full Name
            columnDefs: [
                { orderable: true, targets: [0, 1, 2, 3] }
            ],
            language: {
                search: "",
                searchPlaceholder: "Search in all columns...",
                zeroRecords: "No matching records found",
                info: "Showing _START_ to _END_ of _TOTAL_ users",
                infoEmpty: "No users found",
                infoFiltered: "(filtered from _MAX_ total users)"
            }
        });
        
        // Custom filtering for Service column (index 3)
        $('#serviceFilter').on('keyup', function() {
            table.column(3).search(this.value).draw();
        });

        // Make DataTables search box more Bootstrap-like
        $('.dataTables_filter input').addClass('form-control');
        $('.dataTables_filter input').css('margin-left', '0.5em');
        $('.dataTables_length select').addClass('form-select form-select-sm');
        $('.dataTables_length select').css('width', 'auto');
    }
    
    // Hidden field for storing the group DN
    if (!$('#group_dn').length) {
        $('<input>').attr({
            type: 'hidden',
            id: 'group_dn',
            name: 'group_dn'
        }).appendTo('form');
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
            }
        }).data('ui-autocomplete')._renderItem = function(ul, item) {
            return $('<li>')
                .append(`<div>${item.label}</div>`)
                .appendTo(ul);
        };
    }
    
    // Make sure all links include the LDAP source
    $('a[href]').each(function() {
        // Only process links from the same origin
        if (this.href.startsWith(window.location.origin)) {
            const url = new URL(this.href, window.location.origin);
            if (!url.searchParams.has('source')) {
                url.searchParams.set('source', ldapSource);
                this.href = url.toString();
            }
        }
    });
    
    // Handle refresh button
    $('.refresh-btn').click(function() {
        const source = $(this).data('source') || ldapSource;
        
        // Create new URL with current parameters plus the source
        const url = new URL(window.location.pathname, window.location.origin);
        const urlParams = new URLSearchParams(window.location.search);
        
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