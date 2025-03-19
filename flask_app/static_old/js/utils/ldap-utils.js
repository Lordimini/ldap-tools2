/**
 * Utilitaires pour la gestion des sources LDAP et l'amélioration des liens/formulaires
 */
const LDAPUtils = {
    /**
     * Récupère la source LDAP courante depuis l'élément caché du DOM
     * @returns {string} La source LDAP actuelle (par défaut 'meta')
     */
    getCurrentSource: function() {
      return $('#current_ldap_source').val() || 'meta';
    },
    
    /**
     * Ajoute le paramètre source à tous les liens internes
     * @param {string} source - La source LDAP à ajouter aux liens
     */
    enhanceLinks: function(source) {
      $('a[href]').each(function() {
        // Ne traiter que les liens internes
        if (this.href.startsWith(window.location.origin)) {
          const url = new URL(this.href);
          // N'ajouter le paramètre que s'il n'existe pas déjà
          if (!url.searchParams.has('source')) {
            url.searchParams.set('source', source);
            this.href = url.toString();
          }
        }
      });
    },
    
    /**
     * Ajoute le paramètre source à tous les formulaires
     * @param {string} source - La source LDAP à ajouter aux formulaires
     */
    enhanceForms: function(source) {
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
    },
    
    /**
     * Gère le bouton de rafraîchissement pour changer de source LDAP
     */
    setupRefreshButton: function() {
      $('.refresh-btn').click(function() {
        const source = $(this).data('source') || LDAPUtils.getCurrentSource();
        
        // Créer une nouvelle URL avec les paramètres actuels plus la source
        const url = new URL(window.location.pathname, window.location.origin);
        const urlParams = new URLSearchParams(window.location.search);
        
        // Copier tous les paramètres existants sauf source
        for (const [key, value] of urlParams.entries()) {
          if (key !== 'source') {
            url.searchParams.append(key, value);
          }
        }
        
        // Ajouter le paramètre source
        url.searchParams.set('source', source);
        
        // Naviguer vers l'URL
        window.location.href = url.toString();
      });
    },
    
    /**
     * Initialiser tout ce qui concerne la source LDAP
     */
    init: function() {
      const source = this.getCurrentSource();
      this.enhanceLinks(source);
      this.enhanceForms(source);
      this.setupRefreshButton();
    }
  };