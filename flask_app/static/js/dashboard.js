// Make sure all links and forms include the current LDAP source
document.addEventListener('DOMContentLoaded', function() {
    const currentLdapSource = document.getElementById('current_ldap_source')?.value;
    
    if (currentLdapSource) {
        // Add LDAP source to all links that don't already have it
        document.querySelectorAll('a[href]').forEach(function(link) {
            if (!link.href.includes('source=') && link.href.includes(window.location.hostname)) {
                const url = new URL(link.href);
                url.searchParams.set('source', currentLdapSource);
                link.href = url.toString();
            }
        });
        
        // Add LDAP source to all forms
        document.querySelectorAll('form').forEach(function(form) {
            // Check if the form already has an ldap_source input
            let hasLdapSource = false;
            form.querySelectorAll('input').forEach(function(input) {
                if (input.name === 'ldap_source') {
                    hasLdapSource = true;
                    input.value = currentLdapSource;
                }
            });
            
            // If not, add a hidden input for ldap_source
            if (!hasLdapSource) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'ldap_source';
                input.value = currentLdapSource;
                form.appendChild(input);
            }
        });
    }
});