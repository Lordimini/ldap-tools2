$(document).ready(function () {
    // Get the current LDAP source
    const currentLdapSource = $('#current_ldap_source')?.val() || 'meta';
    
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
    
    // Initialize DataTables on the containers table if it exists
    const containersTable = $('#containersTable');
    if (containersTable.length > 0 && $.fn.DataTable) {
        containersTable.DataTable({
            paging: false, // Disable pagination if not needed
            searching: true, // Enable search bar
            info: false, // Disable "Showing X of Y entries" text
            order: [[0, 'asc']] // Default sorting by the first column (Name) in ascending order
        });
    }

    // Initialize DataTables on the roles table if it exists
    const rolesTable = $('#rolesTable');
    if (rolesTable.length > 0 && $.fn.DataTable) {
        rolesTable.DataTable({
            paging: false, // Disable pagination if not needed
            searching: true, // Enable search bar
            info: false, // Disable "Showing X of Y entries" text
            order: [[0, 'asc']] // Default sorting by the first column (Name) in ascending order
        });
    }
});