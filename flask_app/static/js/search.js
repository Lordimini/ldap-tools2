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
    
    // Function to initialize autocomplete
    function initializeAutocomplete() {
        const searchTermInput = $('#search_term');
        if (searchTermInput.length > 0 && searchTermInput.autocomplete && $('#search_type').val() === 'fullName') {
            searchTermInput.autocomplete({
                source: function(request, response) {
                    // Ne déclencher la recherche que si au moins 3 caractères sont saisis
                    if (request.term.length < 3) {
                        response([]);
                        return;
                    }
                    
                    // Récupérer la source LDAP actuelle
                    var ldapSource = currentLdapSource;
                    
                    // Ajouter une variable pour stocker la requête AJAX en cours
                    if (this.xhr) {
                        this.xhr.abort();
                    }
                    
                    // Effectuer la requête AJAX avec un délai
                    this.xhr = $.getJSON(window.autocompleteFullNameUrl, {
                        term: request.term,
                        source: ldapSource
                    }, function(data) {
                        response(data);
                    });
                },
                minLength: 3,  // Définir une longueur minimale avant de déclencher l'autocomplétion
                delay: 300,    // Ajouter un délai de 300ms entre les frappes et la recherche
                select: function(event, ui) {
                    searchTermInput.val(ui.item.value);
                    return false;
                }
            }).data('ui-autocomplete')._renderItem = function(ul, item) {
                return $('<li>')
                    .append(`<div>${item.label}</div>`)
                    .appendTo(ul);
            };
        } else if (searchTermInput.length > 0 && searchTermInput.autocomplete) {
            // Unbind existing autocomplete if any
            searchTermInput.autocomplete('destroy');
        }
    }

    // Check the selected search type and initialize autocomplete if needed
    $('#search_type').change(function() {
        initializeAutocomplete();
    });

    // Initialize autocomplete on page load for the selected option
    initializeAutocomplete();
    
    // Astuce pour la recherche avec caractères génériques
    const cardForm = $('.card form');
    if (cardForm.length > 0) {
        var wildcardTip = `
            <div class="alert alert-info mt-2">
                <i class="bi bi-info-circle-fill"></i> 
                <strong>Search tip:</strong> You can use the asterisk (*) as a wildcard.
            </div>
        `;
        cardForm.append(wildcardTip);
    }
    
    // Groupes - Filtrer
    $('#group-filter').on('keyup', function() {
        let filter = $(this).val().toLowerCase();
        $('.group-badge').each(function() {
            let text = $(this).text().toLowerCase();
            $(this).toggle(text.indexOf(filter) > -1);
        });
    });
    
    // Rôles - Filtrer
    $('#role-filter').on('keyup', function() {
        let filter = $(this).val().toLowerCase();
        $('.role-badge').each(function() {
            let text = $(this).text().toLowerCase();
            $(this).toggle(text.indexOf(filter) > -1);
        });
    });
    
    // Variables pour le tri
    let groupSortAsc = true;
    let roleSortAsc = true;
    
    // Groupes - Trier
    $('#sort-groups').click(function() {
        const groups = $('#groups .group-badge').get();
        if (groups.length > 0) {
            groups.sort(function(a, b) {
                let textA = $(a).text().trim().toLowerCase();
                let textB = $(b).text().trim().toLowerCase();
                return groupSortAsc ? (textA > textB ? 1 : -1) : (textA < textB ? 1 : -1);
            });
            
            // Changer l'icône
            $(this).find('i').toggleClass('bi-sort-alpha-down bi-sort-alpha-up');
            
            // Inverser pour le prochain clic
            groupSortAsc = !groupSortAsc;
            
            // Réinsérer les éléments triés
            $.each(groups, function(index, group) {
                $('#groups').append(group);
            });
        }
    });
    
    // Rôles - Trier
    $('#sort-roles').click(function() {
        const roles = $('#roles .role-badge').get();
        if (roles.length > 0) {
            roles.sort(function(a, b) {
                let textA = $(a).text().trim().toLowerCase();
                let textB = $(b).text().trim().toLowerCase();
                return roleSortAsc ? (textA > textB ? 1 : -1) : (textA < textB ? 1 : -1);
            });
            
            // Changer l'icône
            $(this).find('i').toggleClass('bi-sort-alpha-down bi-sort-alpha-up');
            
            // Inverser pour le prochain clic
            roleSortAsc = !roleSortAsc;
            
            // Réinsérer les éléments triés
            $.each(roles, function(index, role) {
                $('#roles').append(role);
            });
        }
    });
});