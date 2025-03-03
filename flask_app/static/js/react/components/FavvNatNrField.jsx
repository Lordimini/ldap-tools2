import React, { useState } from 'react';

function FavvNatNrField({ 
  value, 
  override, 
  onChange, 
  onOverrideChange, 
  checkUrl, 
  onVerificationResult 
}) {
  const [isChecking, setIsChecking] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  // Fonction pour normaliser l'input (enlever tout sauf les chiffres)
  const handleInputChange = (e) => {
    // Garder uniquement les chiffres
    const normalizedValue = e.target.value.replace(/[^0-9]/g, '');
    onChange(normalizedValue);
    
    // Effacer le résultat de vérification précédent
    setVerificationResult(null);
  };

  // Fonction pour basculer l'override
  const toggleOverride = () => {
    if (override) {
      // Si l'override est déjà actif, le désactiver directement
      onOverrideChange(false);
    } else {
      // Si l'override n'est pas actif, demander confirmation
      if (window.confirm("Rendre ce champ optionnel n'est pas recommandé pour ce type d'utilisateur. Êtes-vous sûr de vouloir continuer?")) {
        onOverrideChange(true);
      }
    }
  };

  // Fonction pour vérifier si le numéro existe déjà
  const checkFavvNatNr = async () => {
    if (!value) {
      setVerificationResult({
        status: 'error',
        message: 'Veuillez saisir un numéro de registre national.'
      });
      return;
    }
    
    setIsChecking(true);
    
    try {
      const response = await fetch(checkUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          favvNatNr: value
        })
      });
      
      const result = await response.json();
      setVerificationResult(result);
      if (onVerificationResult) {
        onVerificationResult(result);
      }
    } catch (error) {
      console.error('Error checking FavvNatNr:', error);
      setVerificationResult({
        status: 'error',
        message: 'Erreur lors de la vérification. Veuillez réessayer.'
      });
    } finally {
      setIsChecking(false);
    }
  };

  // Générer le message de vérification
  const getVerificationMessage = () => {
    if (isChecking) {
      return <div className="text-center"><i className="fas fa-spinner fa-spin"></i> Vérification en cours...</div>;
    }
    
    if (verificationResult) {
      const { status, message } = verificationResult;
      
      if (status === 'exists') {
        return <div className="alert alert-danger">{message}</div>;
      } else if (status === 'ok') {
        return <div className="alert alert-success">{message}</div>;
      } else {
        return <div className="alert alert-warning">{message}</div>;
      }
    }
    
    return null;
  };

  return (
    <div className="mb-3">
      <label htmlFor="favvNatNr" className="form-label">National Register Number:</label>
      <div className="input-group">
        <input 
          type="text" 
          id="favvNatNr" 
          className="form-control" 
          placeholder="Enter National Register Number" 
          value={value}
          onChange={handleInputChange}
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
        <button 
          type="button" 
          className="btn btn-outline-primary"
          onClick={checkFavvNatNr}
        >
          <i className="fas fa-check"></i> Vérifier
        </button>
      </div>
      {override && (
        <div className="mt-1 mb-2 text-danger fw-bold">
          <i className="fas fa-exclamation-circle"></i> Ce champ est actuellement optionnel (override actif)
        </div>
      )}
      <small className="form-text text-muted">Format will be automatically normalized to remove spaces and hyphens.</small>
      <div className="mt-2">
        {getVerificationMessage()}
      </div>
    </div>
  );
}

export default FavvNatNrField;