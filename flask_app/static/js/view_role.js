// $(document).ready(function() {
//     // Get the current LDAP source
//     const currentLdapSource = $('#current_ldap_source')?.val() || 'meta';
    
//     // Add LDAP source to all links that don't already have it
//     $('a[href]').each(function() {
//         // Only process internal links
//         if ($(this).attr('href') && $(this).attr('href').startsWith('/')) {
//             if (!$(this).attr('href').includes('source=')) {
//                 let url;
//                 try {
//                     url = new URL($(this).attr('href'), window.location.origin);
//                     url.searchParams.set('source', currentLdapSource);
//                     $(this).attr('href', url.toString());
//                 } catch (e) {
//                     // Handle edge cases for malformed URLs
//                     const href = $(this).attr('href');
//                     if (href.includes('?')) {
//                         $(this).attr('href', href + '&source=' + currentLdapSource);
//                     } else {
//                         $(this).attr('href', href + '?source=' + currentLdapSource);
//                     }
//                 }
//             }
//         }
//     });
    
//     // Add LDAP source to all forms that don't already have it
//     $('form').each(function() {
//         // Check if the form already has an ldap_source input
//         let hasLdapSource = false;
//         $(this).find('input').each(function() {
//             if ($(this).attr('name') === 'ldap_source') {
//                 hasLdapSource = true;
//                 $(this).val(currentLdapSource);
//             }
//         });
        
//         // If not, add a hidden input for ldap_source
//         if (!hasLdapSource) {
//             const input = $('<input>').attr({
//                 type: 'hidden',
//                 name: 'ldap_source',
//                 value: currentLdapSource
//             });
//             $(this).append(input);
//         }
//     });

//     // Initialize DataTables on the table if it exists
//     const usersTable = $('#usersTable');
//     if (usersTable.length > 0 && $.fn.DataTable) {
//         usersTable.DataTable({
//             paging: true, // Enable pagination
//             searching: true, // Enable search bar
//             info: true, // Show "Showing X of Y entries" text
//             order: [[0, 'asc']], // Default sorting by the first column (CN) in ascending order
//             columnDefs: [
//                 { orderable: true, targets: '_all' } // Enable sorting for all columns
//             ]
//         });
//     }
    
//     // Attach a click event listener to the table
//     usersTable.on('click', 'tr', function() {
//         const cn = $(this).data('cn');
//         if (cn) {
//             // Redirect to the search_user page with the CN parameter and source parameter
//             window.location.href = window.searchUserUrl + '?cn=' + encodeURIComponent(cn) + '&source=' + currentLdapSource;
//         }
//     });
// });