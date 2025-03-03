// user_creation.js
function userCreationApp() {
    return {
        formData: {
            userType: '',
            givenName: '',
            sn: '',
            email: '',
            favvNatNr: '',
            manager: '',
            emailOverride: false,
            favvNatNrOverride: false,
            managerOverride: false
        },
        nameCheckStatus: '',
        nameCheckMessage: '',
        favvNatNrCheckStatus: '',
        favvNatNrCheckMessage: '',
        managerSuggestions: [],
        managerSearchTimeout: null,
        
        init() {
            // Initialiser les champs avec les valeurs existantes
            const userTypeElement = document.getElementById('user_type');
            if (userTypeElement) this.formData.userType = userTypeElement.value;
            
            // Surveiller les changements de type d'utilisateur pour afficher/masquer les champs
            this.$watch('formData.userType', value => {
                this.updateVisibleFields();
            });
            
            // Initialisation des champs visibles
            this.updateVisibleFields();
        },
        
        updateVisibleFields() {
            // Afficher/masquer les champs en fonction du type d'utilisateur
            const userType = this.formData.userType;
            
            // Manager field for STAG users
            const managerContainer = document.getElementById('manager_container');
            if (managerContainer) {
                managerContainer.style.display = userType === 'STAG' ? 'block' : 'none';
            }
            
            // FavvNatNr field for OCI users
            const favvNatNrContainer = document.getElementById('favvNatNr_container');
            if (favvNatNrContainer) {
                favvNatNrContainer.style.display = 
                    (userType === 'BOODOCI' || userType === 'OCI') ? 'block' : 'none';
            }
        },
        
        async checkNameExists() {
            const givenName = this.formData.givenName;
            const sn = this.formData.sn;
            
            if (!givenName || !sn) {
                alert('Both given name and surname are required.');
                return;
            }
            
            this.nameCheckStatus = 'loading';
            this.nameCheckMessage = '';
            
            try {
                const csrf_token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                const response = await fetch("/usercreation/check_name_exists", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf_token
                    },
                    body: JSON.stringify({ givenName, sn })
                });
                
                const data = await response.json();
                
                this.nameCheckStatus = data.status;
                this.nameCheckMessage = data.message;
                
                // Update the UI
                const nameCheckResult = document.getElementById('nameCheckResult');
                if (nameCheckResult) {
                    nameCheckResult.innerHTML = this.nameCheckMessage;
                    nameCheckResult.className = `mt-2 text-${data.status === 'exists' ? 'danger' : 'success'}`;
                }
            } catch (error) {
                this.nameCheckStatus = 'error';
                this.nameCheckMessage = `Error checking name: ${error.message}`;
                
                const nameCheckResult = document.getElementById('nameCheckResult');
                if (nameCheckResult) {
                    nameCheckResult.innerHTML = this.nameCheckMessage;
                    nameCheckResult.className = 'mt-2 text-danger';
                }
            }
        },
        
        async checkFavvNatNrExists() {
            const favvNatNr = this.formData.favvNatNr;
            
            if (!favvNatNr) {
                alert('National Register Number is required for this check.');
                return;
            }
            
            this.favvNatNrCheckStatus = 'loading';
            this.favvNatNrCheckMessage = '';
            
            try {
                const csrf_token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                const response = await fetch("/usercreation/check_favvnatnr_exists", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf_token
                    },
                    body: JSON.stringify({ favvNatNr })
                });
                
                const data = await response.json();
                
                this.favvNatNrCheckStatus = data.status;
                this.favvNatNrCheckMessage = data.message;
                
                // Update the UI
                const favvNatNrCheckResult = document.getElementById('favvNatNrCheckResult');
                if (favvNatNrCheckResult) {
                    favvNatNrCheckResult.innerHTML = this.favvNatNrCheckMessage;
                    favvNatNrCheckResult.className = `mt-2 text-${data.status === 'exists' ? 'danger' : 'success'}`;
                }
            } catch (error) {
                this.favvNatNrCheckStatus = 'error';
                this.favvNatNrCheckMessage = `Error checking National Register Number: ${error.message}`;
                
                const favvNatNrCheckResult = document.getElementById('favvNatNrCheckResult');
                if (favvNatNrCheckResult) {
                    favvNatNrCheckResult.innerHTML = this.favvNatNrCheckMessage;
                    favvNatNrCheckResult.className = 'mt-2 text-danger';
                }
            }
        },
        
        debounceManagerSearch() {
            clearTimeout(this.managerSearchTimeout);
            this.managerSearchTimeout = setTimeout(() => {
                this.searchManagers();
            }, 300);
        },
        
        async searchManagers() {
            const searchTerm = this.formData.manager;
            
            if (searchTerm.length < 2) {
                this.managerSuggestions = [];
                return;
            }
            
            try {
                const response = await fetch(`/autocomplete/managers?term=${encodeURIComponent(searchTerm)}`);
                const data = await response.json();
                this.managerSuggestions = data;
            } catch (error) {
                console.error('Error fetching manager suggestions:', error);
                this.managerSuggestions = [];
            }
        },
        
        selectManager(suggestion) {
            this.formData.manager = suggestion.value;
            this.managerSuggestions = [];
        },
        
        toggleEmailOverride() {
            this.formData.emailOverride = !this.formData.emailOverride;
            document.getElementById('email_override').value = this.formData.emailOverride.toString();
        },
        
        toggleFavvNatNrOverride() {
            this.formData.favvNatNrOverride = !this.formData.favvNatNrOverride;
            document.getElementById('favvNatNr_override').value = this.formData.favvNatNrOverride.toString();
        },
        
        toggleManagerOverride() {
            this.formData.managerOverride = !this.formData.managerOverride;
            document.getElementById('manager_override').value = this.formData.managerOverride.toString();
        },
        
        validateForm(event) {
            // Vérifier les champs obligatoires
            if (!this.formData.userType || !this.formData.givenName || !this.formData.sn) {
                alert('User type, given name, and surname are required.');
                return false;
            }
            
            // Vérifier l'email
            if (!this.formData.email && !this.formData.emailOverride) {
                alert('Email is required unless overridden.');
                return false;
            }
            
            // Vérifier FavvNatNr pour les utilisateurs OCI
            if ((this.formData.userType === 'BOODOCI' || this.formData.userType === 'OCI') 
                && !this.formData.favvNatNr && !this.formData.favvNatNrOverride) {
                alert('National Register Number is required for OCI users unless overridden.');
                return false;
            }
            
            // Vérifier le chef hiérarchique pour les stagiaires
            if (this.formData.userType === 'STAG' && !this.formData.manager && !this.formData.managerOverride) {
                alert('Manager is required for trainees unless overridden.');
                return false;
            }
            
            // Afficher la modale de confirmation
            this.showConfirmationModal();
            return false;
        },
        
        showConfirmationModal() {
            // Remplir la modale avec les informations de l'utilisateur
            const userSummary = document.getElementById('userSummary');
            if (userSummary) {
                userSummary.innerHTML = `
                    <p><strong>User Type:</strong> ${this.formData.userType}</p>
                    <p><strong>Given Name:</strong> ${this.formData.givenName}</p>
                    <p><strong>Surname:</strong> ${this.formData.sn}</p>
                    <p><strong>Email:</strong> ${this.formData.email || '(None - Override active)'}</p>
                `;
                
                // Ajouter les champs conditionnels si applicable
                if (this.formData.userType === 'STAG') {
                    userSummary.innerHTML += `
                        <p><strong>Manager:</strong> ${this.formData.manager || '(None - Override active)'}</p>
                    `;
                }
                
                if (this.formData.userType === 'BOODOCI' || this.formData.userType === 'OCI') {
                    userSummary.innerHTML += `
                        <p><strong>National Register Number:</strong> ${this.formData.favvNatNr || '(None - Override active)'}</p>
                    `;
                }
            }
            
            // Afficher la modale
            const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
            confirmationModal.show();
        },
        
        submitFinalForm() {
            // Transférer les valeurs au formulaire caché et soumettre
            document.getElementById('hidden_user_type').value = this.formData.userType;
            document.getElementById('hidden_givenName').value = this.formData.givenName;
            document.getElementById('hidden_sn').value = this.formData.sn;
            document.getElementById('hidden_email').value = this.formData.email;
            document.getElementById('hidden_email_override').value = this.formData.emailOverride.toString();
            
            if (this.formData.userType === 'BOODOCI' || this.formData.userType === 'OCI') {
                document.getElementById('hidden_favvNatNr').value = this.formData.favvNatNr;
                document.getElementById('hidden_favvNatNr_override').value = this.formData.favvNatNrOverride.toString();
            }
            
            if (this.formData.userType === 'STAG') {
                document.getElementById('hidden_manager').value = this.formData.manager;
                document.getElementById('hidden_manager_override').value = this.formData.managerOverride.toString();
            }
            
            document.getElementById('actualSubmitForm').submit();
        }
    };
}