from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from flask_app.models.edir_model import EDIRModel
from flask_login import login_required, current_user  # Nouvel import depuis Flask-Login
from flask_app.models.ldap_config_manager import LDAPConfigManager
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, HiddenField
from wtforms.validators import DataRequired
from ldap3 import Server, Connection, ALL, MODIFY_ADD, SUBTREE

usercreation_bp = Blueprint('usercreation', __name__)


class UserCreationForm(FlaskForm):
    user_type = SelectField('User Type', validators=[DataRequired()], choices=[])
    givenName = StringField('Given Name', validators=[DataRequired()])
    sn = StringField('Surname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    manager = StringField('Hierarchical Manager')
    favvNatNr = StringField('FavvNatNr')

@usercreation_bp.route('/fetch_user_types')
def fetch_user_types():
    # Get LDAP source with proper fallback sequence
    ldap_source = request.args.get('source')
    
    # If not in query params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Create EDIR model with the appropriate source
    ldap_model = EDIRModel(source=ldap_source)
    
    user_types = ldap_model.get_user_types_from_ldap('ou=tpl,ou=sync,o=copy')  # Adjust the DN as needed
    return jsonify(user_types)

@usercreation_bp.route('/user_creation', methods=['GET', 'POST'])
@login_required
def create_user():
    # Get LDAP source with proper fallback sequence
    ldap_source = request.args.get('source')
    if request.method == 'POST':
        ldap_source = request.form.get('ldap_source', ldap_source)
    
    # If not in query or form params, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    # Create EDIR model with the appropriate source
    ldap_model = EDIRModel(source=ldap_source)
    
    # Get LDAP name for display purposes
    config = LDAPConfigManager.get_config(ldap_source)
    ldap_name = config.get('LDAP_name', 'META')
    
    # Initialiser la forme
    form = UserCreationForm()
    
    # Récupérer les types d'utilisateurs pour le formulaire
    user_types = ldap_model.get_user_types_from_ldap('ou=tpl,ou=sync,o=copy')
    form.user_type.choices = [(ut['value'], ut['label']) for ut in user_types]
    
    # Variables pour préserver les valeurs du formulaire en cas d'erreur
    form_data = {
        'user_type': '',
        'givenName': '',
        'sn': '',
        'email': '',
        'favvNatNr': '',
        'manager': ''
    }
    
    # Vérifier si l'utilisateur actuel est un administrateur
    # Utilisez la méthode appropriée de votre application pour vérifier si l'utilisateur est admin
    is_admin = current_user.is_admin if hasattr(current_user, 'is_admin') else False
    
    # Si vous utilisez une autre méthode pour déterminer si un utilisateur est admin, utilisez-la ici
    # Par exemple, si vous utilisez une relation de groupe:
    # is_admin = 'admin' in [g.name for g in current_user.groups]
    
     
    if request.method == 'POST':
        # Récupérer les données du formulaire (peut être soit du formulaire visible ou caché)
        user_type = request.form.get('user_type') or request.form.get('hidden_user_type')
        given_name = request.form.get('givenName') or request.form.get('hidden_givenName')
        sn = request.form.get('sn') or request.form.get('hidden_sn')
        email = request.form.get('email') or request.form.get('hidden_email', '')
        favvnatnr = request.form.get('favvNatNr') or request.form.get('hidden_favvNatNr', '')
        manager = request.form.get('manager') or request.form.get('hidden_manager', '')
        
        # Récupérer les valeurs des overrides
        email_override = (request.form.get('email_override') == 'true') or (request.form.get('hidden_email_override') == 'true')
        favvnatnr_override = (request.form.get('favvNatNr_override') == 'true') or (request.form.get('hidden_favvNatNr_override') == 'true')
        manager_override = (request.form.get('manager_override') == 'true') or (request.form.get('hidden_manager_override') == 'true')
        
        # Sauvegarder les valeurs du formulaire pour l'affichage en cas d'erreur
        form_data = {
            'user_type': user_type,
            'givenName': given_name,
            'sn': sn,
            'email': email,
            'favvNatNr': favvnatnr,
            'manager': manager
        }

        # Valider les champs obligatoires
        if not given_name or not sn:
            flash("Les champs Prénom et Nom sont obligatoires.", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data, 
                                  ldap_source=ldap_source, ldap_name=ldap_name)
        
        # Valider l'email (obligatoire sauf si override)
        if not email and not email_override:
            flash("L'adresse email est obligatoire.", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data,
                                  ldap_source=ldap_source, ldap_name=ldap_name)
        
        # Vérifier si un chef hiérarchique est requis pour ce type d'utilisateur
        is_stag = user_type == "STAG" 
        if is_stag and not manager and not manager_override:
            flash("Un chef hiérarchique est obligatoire pour les stagiaires.", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data,
                                  ldap_source=ldap_source, ldap_name=ldap_name)
        
        # Vérifier si le FavvNatNr est requis pour certains types d'utilisateurs
        if (user_type == "BOODOCI" or user_type == "OCI") and not favvnatnr and not favvnatnr_override:
            flash("Le numéro de registre national est obligatoire pour les utilisateurs de type OCI.", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data,
                                  ldap_source=ldap_source, ldap_name=ldap_name)
        
        # Obtenir les détails du modèle sélectionné
        template_details = ldap_model.get_template_details(user_type)

        # Générer un CN unique pour le nouvel utilisateur
        cn = ldap_model.generate_unique_cn(given_name, sn)

        # Définir les attributs LDAP en fonction du type d'utilisateur
        ldap_attributes = {
            'givenName': [given_name],
            'sn': [sn],
            'cn': [cn],
            'fullName': [f"{sn} {given_name}"]
        }

        # Ajouter l'email s'il est fourni
        if email:
            ldap_attributes['mail'] = [email]

        # Ajouter les attributs du template si disponibles
        if template_details:
            # Ajouter le titre
            if template_details.get('title'):
                ldap_attributes['title'] = [template_details['title']]
    
            # Ajouter la description
            if template_details.get('description'):
                ldap_attributes['description'] = [template_details['description']]
    
            # Ajouter l'unité organisationnelle
            if template_details.get('ou'):
                ldap_attributes['ou'] = [template_details['ou']]
    
            # Ajouter FavvExtDienstMgrDn
            if template_details.get('FavvExtDienstMgrDn'):
                ldap_attributes['FavvExtDienstMgrDn'] = [template_details['FavvExtDienstMgrDn']]
    
            # Ajouter FavvEmployeeType
            if template_details.get('FavvEmployeeType'):
                ldap_attributes['FavvEmployeeType'] = [template_details['FavvEmployeeType']]
    
            # Ajouter FavvEmployeeSubType
            if template_details.get('FavvEmployeeSubType'):
                ldap_attributes['FavvEmployeeSubType'] = [template_details['FavvEmployeeSubType']]

        # Ajouter FavvNatNr pour les utilisateurs de type OCI ou BOODOCI (si fourni)
        if (user_type == "BOODOCI" or user_type == "OCI") and favvnatnr:
            normalized_favvnatnr = favvnatnr.replace(' ', '').replace('-', '')
            ldap_attributes['FavvNatNr'] = [normalized_favvnatnr]
            
        # Ajouter le chef hiérarchique pour les stagiaires
        if is_stag and manager:
            # Obtenir le DN du manager pour l'attribut FavvHierarMgrDN
            manager_dn = None
            if manager:
                managers = ldap_model.get_managers()
                for mgr in managers:
                    if mgr['fullName'] == manager:
                        manager_dn = mgr['dn']
                        break
                        
                if manager_dn:
                    ldap_attributes['FavvHierarMgrDN'] = [manager_dn]

        try:
            # Passer les détails du template à la méthode create_user
            result, generated_password, groups_added, groups_failed = ldap_model.create_user(cn, ldap_attributes, template_details)
            if result:
                # Afficher un message de succès avec le mot de passe généré
                message = f"Utilisateur {sn} {given_name} (CN: {cn}) créé avec succès! Mot de passe: {generated_password}"
                
                # Ajouter des informations sur les groupes
                if groups_added > 0:
                    message += f" L'utilisateur a été ajouté à {groups_added} groupe(s)."
                if groups_failed > 0:
                    message += f" Attention: échec d'ajout à {groups_failed} groupe(s)."
                
                flash(message, 'success')
                # Rediriger vers une nouvelle page vide pour éviter la resoumission du formulaire en cas de rafraîchissement
                return redirect(url_for('usercreation.create_user', source=ldap_source))
            else:
                flash(f"Échec de la création de l'utilisateur.", 'error')
                return render_template('user_creation.html', form=form, form_data=form_data,
                                      ldap_source=ldap_source, ldap_name=ldap_name)
        except Exception as e:
            flash(f"Une erreur est survenue: {str(e)}", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data,
                                  ldap_source=ldap_source, ldap_name=ldap_name)

    # Pour les requêtes GET, toujours retourner un formulaire vide
    return render_template('user_creation.html', form=form, form_data=form_data,
                          ldap_source=ldap_source, ldap_name=ldap_name)

@usercreation_bp.route('/preview_user_details', methods=['POST'])
@login_required
def preview_user_details():
    """
    API endpoint to generate a preview of user details before creation,
    including the CN, password, and template attributes.
    """
    try:
        # Get form data
        given_name = request.json.get('givenName', '')
        sn = request.json.get('sn', '')
        user_type = request.json.get('user_type', '')
        
        # Get LDAP source with proper fallback sequence
        ldap_source = request.json.get('ldap_source')
        
        # If not in JSON data, get from session with default fallback
        if not ldap_source:
            ldap_source = session.get('ldap_source', 'meta')
        
        # Make sure session is updated with current source
        session['ldap_source'] = ldap_source
        session.modified = True
        
        if not given_name or not sn or not user_type:
            return jsonify({'error': 'Given name, surname and user type are required'}), 400
        
        # Instantiate the LDAP model
        ldap_model = EDIRModel(source=ldap_source)
        
        # Generate the CN
        cn = ldap_model.generate_unique_cn(given_name, sn)
        
        # Generate password
        password = ldap_model.generate_password_from_cn(cn)
        
        # Get template details
        template_details = ldap_model.get_template_details(user_type)
        
        # Get service manager's fullName if FavvExtDienstMgrDn is present
        if template_details and template_details.get('FavvExtDienstMgrDn'):
            try:
                conn = Connection(ldap_model.edir_server, user=ldap_model.bind_dn, password=ldap_model.password, auto_bind=True)
                conn.search(template_details['FavvExtDienstMgrDn'], '(objectClass=*)', attributes=['fullName'])
                
                if conn.entries and conn.entries[0].fullName:
                    template_details['ServiceManagerName'] = conn.entries[0].fullName.value
                else:
                    template_details['ServiceManagerName'] = "Nom non trouvé"
                
                conn.unbind()
            except Exception as e:
                print(f"Erreur lors de la récupération du nom du manager: {str(e)}")
                template_details['ServiceManagerName'] = "Erreur de recherche"
        
        # Get group names for template groups
        if template_details and 'groupMembership' in template_details and template_details['groupMembership']:
            groups_info = []
            try:
                conn = Connection(ldap_model.edir_server, user=ldap_model.bind_dn, password=ldap_model.password, auto_bind=True)
                
                for group_dn in template_details['groupMembership']:
                    conn.search(group_dn, '(objectClass=*)', attributes=['cn'])
                    if conn.entries:
                        groups_info.append({
                            'dn': group_dn,
                            'cn': conn.entries[0].cn.value
                        })
                
                conn.unbind()
                template_details['groups_info'] = groups_info
            except Exception as e:
                print(f"Erreur lors de la récupération des informations de groupe: {str(e)}")
        
        # Return the generated CN, password, and template details
        return jsonify({
            'cn': cn,
            'password': password,
            'template_details': template_details
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500    
    
    
@usercreation_bp.route('/check_name_exists', methods=['POST'])
@login_required
def check_name_exists():
    """
    Route pour vérifier si un utilisateur avec le nom et prénom donnés existe déjà
    """
    given_name = request.json.get('givenName', '')
    sn = request.json.get('sn', '')
    
    # Get LDAP source with proper fallback sequence
    ldap_source = request.json.get('ldap_source')
    
    # If not in JSON data, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    if not given_name or not sn:
        return jsonify({'status': 'error', 'message': 'Prénom et nom sont requis'}), 400
    
    # Créer une instance du modèle LDAP avec la source spécifiée
    ldap_model = EDIRModel(source=ldap_source)
    
    exists, existing_dn = ldap_model.check_name_combination_exists(given_name, sn)
    
    if exists:
        return jsonify({
            'status': 'exists',
            'message': existing_dn  # On retourne juste le DN, le message complet sera formaté côté client
        })
    else:
        return jsonify({
            'status': 'ok',
            'message': ''  # Le message sera formaté côté client
        })

@usercreation_bp.route('/check_favvnatnr_exists', methods=['POST'])
@login_required
def check_favvnatnr_exists():
    """
    Route pour vérifier si un utilisateur avec le numéro de registre national donné existe déjà
    """
    favvnatnr = request.json.get('favvNatNr', '')
    
    # Get LDAP source with proper fallback sequence
    ldap_source = request.json.get('ldap_source')
    
    # If not in JSON data, get from session with default fallback
    if not ldap_source:
        ldap_source = session.get('ldap_source', 'meta')
    
    # Make sure session is updated with current source
    session['ldap_source'] = ldap_source
    session.modified = True
    
    if not favvnatnr:
        return jsonify({'status': 'error', 'message': 'Numéro de registre national requis'}), 400
    
    # Normaliser le FavvNatNr
    normalized_favvnatnr = favvnatnr.replace(' ', '').replace('-', '')
    
    # Créer une instance du modèle LDAP avec la source spécifiée
    ldap_model = EDIRModel(source=ldap_source)
    
    exists, existing_dn, fullname = ldap_model.check_favvnatnr_exists(normalized_favvnatnr)
    
    if exists:
        return jsonify({
            'status': 'exists',
            'message': f"Un utilisateur avec le numéro national '{favvnatnr}' existe déjà dans l'annuaire: {fullname} ({existing_dn})."
        })
    else:
        return jsonify({
            'status': 'ok',
            'message': f"Aucun utilisateur existant avec le numéro national '{favvnatnr}'."
        })