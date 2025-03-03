import React, { useState, useEffect } from 'react';
import UserTypeSelect from './components/UserTypeSelect';
import NameFields from './components/NameFields';
import EmailField from './components/EmailField';
import ManagerField from './components/ManagerField';
import FavvNatNrField from './components/FavvNatNrField';
import PreviewModal from './components/PreviewModal';

function UserCreationForm({ config }) {
  // État du formulaire
  const [formData, setFormData] = useState({
    userType: config.formData.initialValues.userType || '',
    givenName: config.formData.initialValues.givenName || '',
    sn: config.formData.initialValues.sn || '',
    email: config.formData.initialValues.email || '',
    emailOverride: false,
    manager: config.formData.initialValues.manager || '',
    managerOverride: false,
    favvNatNr: config.formData.initialValues.favvNatNr || '',
    favvNatNrOverride: false,
  });

  // État pour les vérifications
  const [nameVerificationResult, setNameVerificationResult] = useState(null);
  const [favvNatNrVerificationResult, setFavvNatNrVerificationResult] = useState(null);
  
  // État pour la prévisualisation
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Conditions d'affichage des champs
  const showManagerField = formData.userType === 'STAG';
  const showFavvNatNrField = ['BOODOCI', 'OCI'].includes(formData.userType);

  // Handler pour les changements de champs
  const handleInputChange = (field, value) => {
    setFormData(prevData => ({
      ...prevData,
      [field]: value
    }));
  };

  // Fonction pour gérer le changement de type d'utilisateur
  const handleUserTypeChange = (value) => {
    setFormData(prevData => {
      const newData = { ...prevData, userType: value };
      
      // Réinitialiser les champs conditionnels si nécessaire
      if (value !== 'STAG') {
        newData.manager = '';
        newData.managerOverride = false;
      }
      
      if (!['BOODOCI', 'OCI'].includes(value)) {
        newData.favvNatNr = '';
        newData.favvNatNrOverride = false;
      }
      
      return newData;
    });
  };

  // Validation du formulaire
  const validateForm = (e) => {
    e.preventDefault();
    
    // Validation de base
    if (!formData.givenName || !formData.sn) {
      alert('Given name and surname are required');
      return;
    }
    
    // Validation du champ email
    if (!formData.email && !formData.emailOverride) {
      alert('Email is required unless overridden');
      return;
    }
    
    // Validation du champ manager
    if (showManagerField && !formData.manager && !formData.managerOverride) {
      alert('Manager is required for trainees unless overridden');
      return;
    }
    
    // Validation du numéro national
    if (showFavvNatNrField && !formData.favvNatNr && !formData.favvNatNrOverride) {
      alert('National number is required for this user type unless overridden');
      return;
    }
    
    // Prévisualisation des détails utilisateur
    fetchPreviewDetails();
  };

  // Récupération des détails de prévisualisation
  const fetchPreviewDetails = async () => {
    try {
      const response = await fetch(config.urls.previewUserDetails, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          givenName: formData.givenName,
          sn: formData.sn,
          user_type: formData.userType
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setPreviewData(data);
        setShowPreviewModal(true);
      } else {
        const error = await response.json();
        alert('Error fetching preview: ' + (error.message || 'Unknown error'));
      }
    } catch (error) {
      console.error('Preview fetch error:', error);
      alert('An error occurred while fetching preview details');
    }
  };

  // Soumission du formulaire
  const submitForm = async () => {
    // Créer un FormData pour envoyer le formulaire
    const formDataObj = new FormData();
    
    // Ajouter les champs du formulaire
    formDataObj.append('user_type', formData.userType);
    formDataObj.append('givenName', formData.givenName);
    formDataObj.append('sn', formData.sn);
    formDataObj.append('email', formData.email);
    formDataObj.append('email_override', formData.emailOverride);
    
    if (showManagerField) {
      formDataObj.append('manager', formData.manager);
      formDataObj.append('manager_override', formData.managerOverride);
    }
    
    if (showFavvNatNrField) {
      formDataObj.append('favvNatNr', formData.favvNatNr);
      formDataObj.append('favvNatNr_override', formData.favvNatNrOverride);
    }
    
    // Ajouter le token CSRF
    formDataObj.append('csrf_token', config.formData.csrfToken);
    
    try {
      const response = await fetch(config.urls.submitForm, {
        method: 'POST',
        body: formDataObj
      });
      
      // Rediriger vers la réponse
      if (response.ok) {
        // Recharger la page pour afficher les messages flash
        window.location.reload();
      } else {
        alert('Error submitting form');
      }
    } catch (error) {
      console.error('Form submission error:', error);
      alert('An error occurred while submitting the form');
    }
  };

  return (
    <form onSubmit={validateForm} className="card p-4 shadow">
      {/* Sélection du type d'utilisateur */}
      <UserTypeSelect 
        choices={config.formData.userTypeChoices}
        value={formData.userType}
        onChange={handleUserTypeChange}
      />

      {/* Champs nom et prénom */}
      <NameFields 
        givenName={formData.givenName}
        surname={formData.sn}
        onGivenNameChange={(value) => handleInputChange('givenName', value)}
        onSurnameChange={(value) => handleInputChange('sn', value)}
        checkNameUrl={config.urls.checkNameExists}
        onVerificationResult={setNameVerificationResult}
      />

      {/* Champ Email avec possibilité d'override */}
      <EmailField 
        value={formData.email}
        override={formData.emailOverride}
        onChange={(value) => handleInputChange('email', value)}
        onOverrideChange={(value) => handleInputChange('emailOverride', value)}
      />
      
      {/* Champ Manager (conditionnel) */}
      {showManagerField && (
        <ManagerField 
          value={formData.manager}
          override={formData.managerOverride}
          onChange={(value) => handleInputChange('manager', value)}
          onOverrideChange={(value) => handleInputChange('managerOverride', value)}
          autocompleteUrl={config.urls.autocompleteManagers}
        />
      )}
      
      {/* Champ FavvNatNr (conditionnel) */}
      {showFavvNatNrField && (
        <FavvNatNrField 
          value={formData.favvNatNr}
          override={formData.favvNatNrOverride}
          onChange={(value) => handleInputChange('favvNatNr', value)}
          onOverrideChange={(value) => handleInputChange('favvNatNrOverride', value)}
          checkUrl={config.urls.checkFavvNatNrExists}
          onVerificationResult={setFavvNatNrVerificationResult}
        />
      )}

      {/* Bouton de soumission */}
      <button type="submit" className="btn btn-primary">Preview & Create User</button>
      
      {/* Modal de prévisualisation */}
      {showPreviewModal && (
        <PreviewModal 
          previewData={previewData}
          formData={formData}
          show={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          onConfirm={submitForm}
          userTypeChoices={config.formData.userTypeChoices}
        />
      )}
    </form>
  );
}

export default UserCreationForm;