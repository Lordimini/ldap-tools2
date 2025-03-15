// Sidebar Toggle
document.getElementById('sidebarToggle').addEventListener('click', function() {
    document.body.classList.toggle('sidebar-collapsed');
});

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Make table rows clickable if they have the 'clickable-row' class
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', function() {
            window.location = this.dataset.href;
        });
    });
    
    // LDAP Source Selector functionality
    const sourceSelector = document.getElementById('ldap_source_selector');
    if (sourceSelector) {
        sourceSelector.addEventListener('change', function() {
            // Get CSRF token if it exists
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            
            fetch('/set_ldap_source', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({source: this.value})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show loading state
                    document.body.style.cursor = 'wait';
                    sourceSelector.disabled = true;
                    
                    // Create a new URL with the source parameter
                    const url = new URL(window.location.href);
                    url.searchParams.set('source', this.value);
                    
                    // Redirect to the new URL instead of reloading
                    window.location.href = url.toString();
                } else {
                    console.error('Failed to change LDAP source:', data.error);
                    alert('Failed to change LDAP source: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error changing LDAP source:', error);
                alert('An error occurred while changing LDAP source');
            });
        });
    }
});