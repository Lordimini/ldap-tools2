$(document).ready(function () {
    // Get the current LDAP source
    const ldapSource = $('#current_ldap_source')?.val() || 'meta';
    
    // Initialize DataTables on the table if it exists
    const usersTable = $('#usersTable');
    if (usersTable.length > 0) {
        if ($.fn.DataTable && $.fn.DataTable.isDataTable('#usersTable')) {
            usersTable.DataTable().destroy();
        }
        
        if ($.fn.DataTable) {
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
    }

    // Autocomplete for role_cn input
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
            }
        }).data('ui-autocomplete')._renderItem = function(ul, item) {
            return $('<li>')
                .append(`<div>${item.label}</div>`)
                .appendTo(ul);
        };
    }
    
    // Astuce pour la recherche avec caractères génériques
    const cardForm = $('.card form');
    if (cardForm.length > 0) {
        const wildcardTip = `
            <div class="alert alert-info mt-2">
                <i class="bi bi-info-circle-fill"></i> 
                <strong>Search tip:</strong> You can use the asterisk (*) as a wildcard. 
            </div>
        `;
        cardForm.append(wildcardTip);
    }
    
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
});