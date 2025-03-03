import React, { useState, useEffect } from 'react';

function NameFields({ givenName, surname, onGivenNameChange, onSurnameChange, checkNameUrl, onVerificationResult }) {
  const [isChecking, setIsChecking] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  // Réinitialiser le résultat de vérification lorsque les entrées changent
  useEffect(() => {
    setVerificationResult(null);
  }, [givenName, surname]);

  const checkName = async () => {
    if (!givenName || !surname) {
      const result = {
        status: 'error',
        message: 'Veuillez saisir le prénom et le nom.'
      };
      setVerificationResult(result);
      onVerificationResult(result);
      return;
    }
    
    setIsChecking(true);
    
    try {
      const response = await fetch(checkNameUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          givenName: givenName,
          sn: surname
        })
      });
      
      const result = await response.json();
      setVerificationResult(result);
      onVerificationResult(result);
    } catch (error) {
      console.error('Error checking name:', error);
      const errorResult = {
        status: 'error',
        message: 'Erreur lors de la vérification. Veuillez réessayer.'
      };
      setVerificationResult(errorResult);
      onVerificationResult(errorResult);
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
        return (
          <div className="alert alert-danger">
            Un utilisateur avec le nom '{surname} {givenName}' existe déjà dans l'annuaire ({message}).
          </div>
        );
      } else if (status === 'ok') {
        return (
          <div className="alert alert-success">
            Aucun utilisateur existant avec le nom '{surname} {givenName}'.
          </div>
        );
      } else {
        return <div className="alert alert-warning">{message}</div>;
      }
    }
    
    return null;
  };

  return (
    <div>
      {/* Given Name */}
      <div className="mb-3">
        <label htmlFor="givenName" className="form-label">Given Name:</label>
        <input 
          type="text" 
          id="givenName" 
          className="form-control" 
          value={givenName}
          onChange={(e) => onGivenNameChange(e.target.value)}
          required
        />
      </div>

      {/* Surname */}
      <div className="mb-3">
        <label htmlFor="sn" className="form-label">Surname:</label>
        <div className="input-group">
          <input 
            type="text" 
            id="sn" 
            className="form-control" 
            value={surname}
            onChange={(e) => onSurnameChange(e.target.value)}
            required
          />
          <button 
            type="button" 
            className="btn btn-outline-primary" 
            onClick={checkName}
          >
            <i className="fas fa-check"></i> Vérifier
          </button>
        </div>
        <div className="mt-2">
          {getVerificationMessage()}
        </div>
      </div>
    </div>
  );
}

export default NameFields;