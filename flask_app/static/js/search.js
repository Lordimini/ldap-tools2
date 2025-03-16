$(document).ready(function() {
    // Obtenir la source LDAP actuelle depuis l'élément DOM dédié
    // Cette valeur devrait être injectée par le serveur via un template
    const currentLdapSource = $('#current_ldap_source').val() || 'meta';
    
    // ===== AMÉLIORATION 1: Gérer les erreurs d'authentification =====
    // Ajouter un gestionnaire d'événements global pour intercepter les erreurs 401/403
    $(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
        if (jqXHR.status === 401 || jqXHR.status === 403) {
            // Rediriger vers la page de connexion si l'utilisateur n'est pas authentifié
            // ou n'a pas les permissions nécessaires
            window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
        }
    });
    
    // ===== AMÉLIORATION 2: Utiliser LDAPUtils pour la gestion des sources LDAP =====
    // Cette approche est plus modulaire et suit le pattern de la bibliothèque LDAP Manager
    if (typeof LDAPUtils !== 'undefined') {
        // Utiliser les méthodes de la bibliothèque si disponible
        LDAPUtils.enhanceLinks(currentLdapSource);
        LDAPUtils.enhanceForms(currentLdapSource);
    } else {
        // Conserver le code original comme fallback
        enhanceLinksWithLdapSource(currentLdapSource);
        enhanceFormsWithLdapSource(currentLdapSource);
    }
    
    // ===== AMÉLIORATION 3: Améliorer la gestion de l'autocomplétion =====
    initializeAutocomplete(currentLdapSource);
    
    // Gestionnaire de changement pour le type de recherche
    $('#search_type').change(function() {
        initializeAutocomplete(currentLdapSource);
    });
    
    // ===== AMÉLIORATION 4: Encapsuler les fonctionnalités de tri et filtrage =====
    initializeFilterAndSort();
    
    // Fonctions d'amélioration des liens (fallback)
    function enhanceLinksWithLdapSource(source) {
        $('a[href]').each(function() {
            // Ne traiter que les liens internes
            if ($(this).attr('href') && $(this).attr('href').startsWith('/')) {
                if (!$(this).attr('href').includes('source=')) {
                    try {
                        const url = new URL($(this).attr('href'), window.location.origin);
                        url.searchParams.set('source', source);
                        $(this).attr('href', url.toString());
                    } catch (e) {
                        // Gérer les cas particuliers pour les URL malformées
                        const href = $(this).attr('href');
                        if (href.includes('?')) {
                            $(this).attr('href', href + '&source=' + source);
                        } else {
                            $(this).attr('href', href + '?source=' + source);
                        }
                    }
                }
            }
        });
    }
    
    // Fonctions d'amélioration des formulaires (fallback)
    function enhanceFormsWithLdapSource(source) {
        $('form').each(function() {
            // Vérifier si le formulaire a déjà un champ ldap_source
            let hasLdapSource = false;
            $(this).find('input').each(function() {
                if ($(this).attr('name') === 'ldap_source') {
                    hasLdapSource = true;
                    $(this).val(source);
                }
            });
            
            // Si non, ajouter un champ caché pour ldap_source
            if (!hasLdapSource) {
                const input = $('<input>').attr({
                    type: 'hidden',
                    name: 'ldap_source',
                    value: source
                });
                $(this).append(input);
            }
        });
    }
    
    // Fonction d'initialisation de l'autocomplétion
    function initializeAutocomplete(source) {
        const searchTypeInput = $('#search_type');
        const searchTermInput = $('#search_term');
        
        if (searchTermInput.length > 0 && searchTermInput.autocomplete) {
            // Détruire l'instance précédente si elle existe
            if (searchTermInput.autocomplete('instance')) {
                searchTermInput.autocomplete('destroy');
            }
            
            // N'initialiser l'autocomplétion que pour le type fullName
            if (searchTypeInput.val() === 'fullName') {
                searchTermInput.autocomplete({
                    source: function(request, response) {
                        // Ne déclencher la recherche que si au moins 3 caractères sont saisis
                        if (request.term.length < 3) {
                            response([]);
                            return;
                        }
                        
                        // Ajouter une variable pour stocker la requête AJAX en cours
                        if (this.xhr) {
                            this.xhr.abort();
                        }
                        
                        // Effectuer la requête AJAX avec un délai
                        this.xhr = $.getJSON(window.autocompleteFullNameUrl, {
                            term: request.term,
                            source: source
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
            }
        }
    }
    
    // Fonction d'initialisation du tri et du filtrage
    function initializeFilterAndSort() {
        // Groupes - Filtrer
        $('#group-filter').on('keyup', function() {
            const filter = $(this).val().toLowerCase();
            $('.group-badge').each(function() {
                const text = $(this).text().toLowerCase();
                $(this).toggle(text.indexOf(filter) > -1);
            });
        });
        
        // Rôles - Filtrer
        $('#role-filter').on('keyup', function() {
            const filter = $(this).val().toLowerCase();
            $('.role-badge').each(function() {
                const text = $(this).text().toLowerCase();
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
                    const textA = $(a).text().trim().toLowerCase();
                    const textB = $(b).text().trim().toLowerCase();
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
                    const textA = $(a).text().trim().toLowerCase();
                    const textB = $(b).text().trim().toLowerCase();
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
    }
});