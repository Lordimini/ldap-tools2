import React, { useEffect, useRef } from 'react';
import $ from 'jquery';
import 'jquery-ui/ui/widgets/autocomplete';

function ManagerField({ value, override, onChange, onOverrideChange, autocompleteUrl }) {
  const inputRef = useRef(null);

  // Initialisation de l'autocomplétion jQuery UI
  useEffect(() => {
    if (inputRef.current && autocompleteUrl) {
      $(inputRef.current).autocomplete({
        source: function(request, response) {
          $.getJSON(autocompleteUrl, {
            term: request.term
          }, function(data) {
            response(data);
          });
        },
        select: function(event, ui) {
          onChange(ui.item.value);
          return false;
        },
        minLength: 2
      }).data('ui-autocomplete')._renderItem = function(ul, item) {
        return $('<li>')
          .append(`<div>${item.label}</div>`)
          .appendTo(ul);
      };
    }
    
    // Nettoyage à la destruction du composant
    return () => {
      if (inputRef.current && $(inputRef.current).autocomplete) {
        $(inputRef.current).autocomplete('destroy');
      }
    };
  }, [autocompleteUrl, onChange]);

  // Fonction pour basculer l'override
  const toggleOverride = () => {
    if (override) {
      // Si l'override est déjà actif, le désactiver directement
      onOverrideChange(false);
    } else {
      // Si l'override n'est pas actif, demander confirmation
      if (window.confirm("Créer un stagiaire sans chef hiérarchique n'est pas recommandé. Êtes-vous sûr de vouloir continuer?")) {
        onOverrideChange(true);
      }
    }
  };

  return (
    <div className="mb-3">
      <label htmlFor="manager" className="form-label">Hierarchical Manager:</label>
      <div className="input-group">
        <input 
          type="text" 
          id="manager" 
          className="form-control" 
          placeholder="Start typing to search for managers..." 
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={!override}
          ref={inputRef}
        />
        <button 
          type="button" 
          className={`btn ${override ? 'btn-danger' : 'btn-warning'}`}
          onClick={toggleOverride}
        >
          <i className={`fas ${override ? 'fa-times-circle' : 'fa-exclamation-triangle'}`}></i> 
          {override ? 'Annuler Override' : 'Override'}
        </button>
      </div>
      {override && (
        <div className="mt-1 mb-2 text-danger fw-bold">
          <i className="fas fa-exclamation-circle"></i> Ce champ est actuellement optionnel (override actif)
        </div>
      )}
      <small className="form-text text-muted">Only managers with FavvDienstHoofd=YES are valid.</small>
    </div>
  );
}

export default ManagerField;