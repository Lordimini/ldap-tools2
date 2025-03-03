import React, { useEffect, useRef } from 'react';
import { Modal } from 'bootstrap';

function PreviewModal({ previewData, formData, show, onClose, onConfirm, userTypeChoices }) {
  const modalRef = useRef(null);
  const modalInstance = useRef(null);

  // Trouver le texte du type d'utilisateur
  const getUserTypeText = () => {
    const userTypeChoice = userTypeChoices.find(
      choice => choice[0] === formData.userType
    );
    return userTypeChoice ? userTypeChoice[1] : formData.userType;
  };

  // Créer le HTML de résumé utilisateur
  const createUserSummaryHTML = () => {
    if (!previewData) return '';
    
    const { cn, password, template_details } = previewData;
    const email = formData.email || 'No email specified (Override)';
    const favvNatNr = formData.favvNatNr || 'No National Register Number (Override)';
    const manager = formData.manager || 'No manager specified (Override)';
    
    let html = `
      <table class="table table-striped">
        <tr>
          <th>User Type:</th>
          <td>${getUserTypeText()} (${formData.userType})</td>
        </tr>
        <tr>
          <th>Full Name:</th>
          <td>${formData.sn} ${formData.givenName}</td>
        </tr>
        <tr class="table-primary">
          <th>Common Name (CN):</th>
          <td><strong>${cn}</strong></td>
        </tr>
        <tr class="table-primary">
          <th>Generated Password:</th>
          <td><code>${password}</code></td>
        </tr>
        <tr>
          <th>Email:</th>
          <td>${email}</td>
        </tr>`;
    
    // Ajouter les champs conditionnels
    if (['BOODOCI', 'OCI'].includes(formData.userType)) {
      html += `
        <tr>
          <th>National Register Number:</th>
          <td>${favvNatNr}</td>
        </tr>`;
    }
    
    if (formData.userType === 'STAG') {
      html += `
        <tr>
          <th>Hierarchical Manager:</th>
          <td>${manager}</td>
        </tr>`;
    }
    
    // Ajouter les détails du template
    if (template_details) {
      html += `<tr><th colspan="2" class="table-secondary">Template Attributes</th></tr>`;
      
      if (template_details.description) {
        html += `
          <tr>
            <th>Description:</th>
            <td>${template_details.description}</td>
          </tr>`;
      }
      
      if (template_details.title) {
        html += `
          <tr>
            <th>Title:</th>
            <td>${template_details.title}</td>
          </tr>`;
      }
      
      if (template_details.ou) {
        html += `
          <tr>
            <th>Service/OU:</th>
            <td>${template_details.ou}</td>
          </tr>`;
      }
      
      if (template_details.FavvEmployeeType) {
        html += `
          <tr>
            <th>Employee Type:</th>
            <td>${template_details.FavvEmployeeType}</td>
          </tr>`;
      }
      
      if (template_details.FavvEmployeeSubType) {
        html += `
          <tr>
            <th>Employee SubType:</th>
            <td>${template_details.FavvEmployeeSubType}</td>
          </tr>`;
      }
      
      if (template_details.FavvExtDienstMgrDn) {
        html += `
          <tr>
            <th>Service Manager:</th>
            <td>${template_details.ServiceManagerName || 'Non disponible'} <span class="text-muted small">(${template_details.FavvExtDienstMgrDn})</span></td>
          </tr>`;
      }
    }
    
    html += `</table>
      <div class="alert alert-info">
        <strong>Note:</strong> Le CN et le mot de passe sont générés automatiquement en fonction du nom.
        ${template_details ? 'Les attributs du template seront automatiquement appliqués lors de la création.' : ''}
      </div>`;
    
    return html;
  };

  // Gestion du cycle de vie de la modal Bootstrap
  useEffect(() => {
    if (modalRef.current) {
      modalInstance.current = new Modal(modalRef.current);
      
      if (show) {
        modalInstance.current.show();
      }
      
      const handleHidden = () => {
        onClose();
      };
      
      modalRef.current.addEventListener('hidden.bs.modal', handleHidden);
      
      return () => {
        if (modalRef.current) {
          modalRef.current.removeEventListener('hidden.bs.modal', handleHidden);
        }
        if (modalInstance.current) {
          modalInstance.current.hide();
        }
      };
    }
  }, [show, onClose]);

  return (
    <div className="modal fade" ref={modalRef} tabIndex="-1" aria-labelledby="previewModalLabel" aria-hidden="true">
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header bg-info text-white">
            <h5 className="modal-title" id="previewModalLabel">Confirm User Creation</h5>
            <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div className="modal-body">
            <h6>Please review the user information before creating:</h6>
            
            <div 
              className="card p-3 mb-3" 
              dangerouslySetInnerHTML={{ __html: createUserSummaryHTML() }}
            ></div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" className="btn btn-primary" onClick={onConfirm}>Create User</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PreviewModal;