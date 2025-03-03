import React, { useState } from 'react';

function EmailField({ value, override, onChange, onOverrideChange }) {
  const toggleOverride = () => {
    if (override) {
      // Si l'override est déjà actif, le désactiver directement
      onOverrideChange(false);
    } else {
      // Si l'override n'est pas actif, demander confirmation
      if (window.confirm("Attention, rendre ce champ optionnel n'est pas recommandé. Êtes-vous sûr de vouloir continuer?")) {
        onOverrideChange(true);
      }
    }
  };

  return (
    <div className="mb-3">
      <label htmlFor="email" className="form-label">Email:</label>
      <div className="input-group">
        <input 
          type="email" 
          id="email" 
          className="form-control" 
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={!override}
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
    </div>
  );
}

export default EmailField;