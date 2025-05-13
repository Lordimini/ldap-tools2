$(document).ready(function() {
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
    
    // Add LDAP source to all forms that don't already have it
    $('form').each(function() {
        // Check if the form already has an ldap_source input
        let hasLdapSource = false;
        $(this).find('input').each(function() {
            if ($(this).attr('name') === 'ldap_source') {
                hasLdapSource = true;
                $(this).val(currentLdapSource);
            }
        });
        
        // If not, add a hidden input for ldap_source
        if (!hasLdapSource) {
            const input = $('<input>').attr({
                type: 'hidden',
                name: 'ldap_source',
                value: currentLdapSource
            });
            $(this).append(input);
        }
    });
    
    // Service name autocomplete
    const serviceNameInput = $('#service_name');
    if (serviceNameInput.length > 0 && serviceNameInput.autocomplete) {
        serviceNameInput.autocomplete({
            source: function(request, response) {
                $.getJSON(window.autocompleteServicesUrl, {
                    term: request.term,
                    source: currentLdapSource
                }, function(data) {
                    response(data);
                });
            },
            select: function(event, ui) {
                serviceNameInput.val(ui.item.value);
                return false;
            },
            minLength: 2
        }).data('ui-autocomplete')._renderItem = function(ul, item) {
            return $('<li>')
                .append(`<div>${item.label}</div>`)
                .appendTo(ul);
        };
    }
});