/**
 * Utilitaires pour l'initialisation des tables DataTables
 */
const DataTableUtils = {
  /**
   * Active les lignes cliquables dans une table
   * @param {string} tableSelector - Sélecteur jQuery pour la table
   * @param {string} urlBase - URL de base pour la redirection
   * @param {string} dataAttribute - Attribut data à récupérer (par défaut 'cn')
   * @param {string} ldapSource - Source LDAP à inclure dans l'URL
   */
  enableClickableRows: function(tableSelector, urlBase, dataAttribute='cn', ldapSource='meta') {
    const table = $(tableSelector);
    if (table.length === 0) return;
    
    table.on('click', 'tr', function() {
      const dataValue = $(this).data(dataAttribute);
      if (dataValue) {
        // Construire l'URL avec le paramètre et la source LDAP
        window.location.href = urlBase + '?'+ dataAttribute + '=' + 
          encodeURIComponent(dataValue) + '&source=' + ldapSource;
      }
    });
  },
  
  /**
   * Options par défaut pour les tables d'utilisateurs
   */
  defaultUserTableOptions: {
    responsive: true,
    paging: true,
    pageLength: 10,
    lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
    searching: true,
    info: true,
    order: [[1, 'asc']], // Tri par défaut sur la colonne "Full Name"
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
  },
  
  /**
   * Options par défaut pour les tables de groupes
   */
  defaultGroupTableOptions: {
    responsive: true,
    paging: true,
    pageLength: 10,
    lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
    searching: true,
    info: true,
    order: [[0, 'asc']], // Tri par défaut sur la colonne "Group Name"
    language: {
      search: "",
      searchPlaceholder: "Search groups...",
      zeroRecords: "No matching groups found",
      info: "Showing _START_ to _END_ of _TOTAL_ groups",
      infoEmpty: "No groups found",
      infoFiltered: "(filtered from _MAX_ total groups)"
    }
  },
  
  /**
   * Initialise une table d'utilisateurs avec DataTables
   * @param {string} tableSelector - Sélecteur jQuery pour la table
   * @param {Object} customOptions - Options personnalisées pour écraser les valeurs par défaut
   * @param {Object} clickableOptions - Options pour rendre les lignes cliquables (null pour désactiver)
   * @returns {Object} L'instance DataTable initialisée
   */
  initUserTable: function(tableSelector, customOptions = {}, clickableOptions = null) {
    // Vérifier si la table existe
    const table = $(tableSelector);
    if (table.length === 0) return null;
    
    // Détruire la table existante si elle est déjà initialisée
    if ($.fn.DataTable.isDataTable(tableSelector)) {
      table.DataTable().destroy();
    }
    
    // Fusionner les options par défaut avec les options personnalisées
    const options = {...this.defaultUserTableOptions, ...customOptions};
    
    // Initialiser la table
    const dataTable = table.DataTable(options);
    
    // Améliorer le style des éléments DataTables
    this.enhanceDataTableStyle();
    
    // Activer les lignes cliquables si des options sont fournies
    if (clickableOptions) {
      const ldapSource = clickableOptions.ldapSource || LDAPUtils.getCurrentSource();
      this.enableClickableRows(
        tableSelector, 
        clickableOptions.urlBase, 
        clickableOptions.dataAttribute || 'cn', 
        ldapSource
      );
      
      // Ajouter un style de curseur pointer aux lignes de données
      table.find('tbody tr').css('cursor', 'pointer');
    }
    
    return dataTable;
  },
  
  /**
   * Initialise une table de groupes avec DataTables
   * @param {string} tableSelector - Sélecteur jQuery pour la table
   * @param {Object} customOptions - Options personnalisées pour écraser les valeurs par défaut
   * @returns {Object} L'instance DataTable initialisée
   */
  initGroupTable: function(tableSelector, customOptions = {}) {
    // Vérifier si la table existe
    const table = $(tableSelector);
    if (table.length === 0) return null;
    
    // Détruire la table existante si elle est déjà initialisée
    if ($.fn.DataTable.isDataTable(tableSelector)) {
      table.DataTable().destroy();
    }
    
    // Fusionner les options par défaut avec les options personnalisées
    const options = {...this.defaultGroupTableOptions, ...customOptions};
    
    // Initialiser la table
    const dataTable = table.DataTable(options);
    
    // Améliorer le style des éléments DataTables
    this.enhanceDataTableStyle();
    
    return dataTable;
  },
  
  /**
   * Initialise une table générique avec DataTables
   * @param {string} tableSelector - Sélecteur jQuery pour la table
   * @param {Object} options - Options pour DataTables
   * @param {Object} clickableOptions - Options pour rendre les lignes cliquables (null pour désactiver)
   * @returns {Object} L'instance DataTable initialisée
   */
  initGenericTable: function(tableSelector, options = {}, clickableOptions = null) {
    // Vérifier si la table existe
    const table = $(tableSelector);
    if (table.length === 0) return null;
    
    // Détruire la table existante si elle est déjà initialisée
    if ($.fn.DataTable.isDataTable(tableSelector)) {
      table.DataTable().destroy();
    }
    
    // Initialiser la table
    const dataTable = table.DataTable(options);
    
    // Améliorer le style des éléments DataTables
    this.enhanceDataTableStyle();
    
    // Activer les lignes cliquables si des options sont fournies
    if (clickableOptions) {
      const ldapSource = clickableOptions.ldapSource || LDAPUtils.getCurrentSource();
      this.enableClickableRows(
        tableSelector, 
        clickableOptions.urlBase, 
        clickableOptions.dataAttribute || 'cn', 
        ldapSource
      );
      
      // Ajouter un style de curseur pointer aux lignes de données
      table.find('tbody tr').css('cursor', 'pointer');
    }
    
    return dataTable;
  },
  
  /**
   * Améliore le style des éléments DataTables pour s'intégrer à Bootstrap
   */
  enhanceDataTableStyle: function() {
    // Rendre la boîte de recherche plus Bootstrap
    $('.dataTables_filter input').addClass('form-control');
    $('.dataTables_filter input').css('margin-left', '0.5em');
    
    // Rendre le sélecteur de longueur plus Bootstrap
    $('.dataTables_length select').addClass('form-select form-select-sm');
    $('.dataTables_length select').css('width', 'auto');
  },
  
  /**
   * Configure le filtrage personnalisé sur une colonne spécifique
   * @param {Object} table - L'instance DataTable
   * @param {string} inputSelector - Sélecteur pour l'input de filtrage
   * @param {number} columnIndex - Index de la colonne à filtrer
   */
  setupColumnFilter: function(table, inputSelector, columnIndex) {
    $(inputSelector).on('keyup', function() {
      table.column(columnIndex).search(this.value).draw();
    });
  }
};