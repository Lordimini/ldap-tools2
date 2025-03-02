from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_app.models.ldap import LDAPModel
from flask_app.utils.ldap_utils import login_required
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, HiddenField
from wtforms.validators import DataRequired

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
    ldap_model = LDAPModel()
    user_types = ldap_model.get_user_types_from_ldap('ou=tpl,ou=sync,o=copy')  # Adjust the DN as needed
    return jsonify(user_types)

@usercreation_bp.route('/user_creation', methods=['GET', 'POST'])
@login_required
def create_user():
    # Initialiser la forme
    form = UserCreationForm()
    
    # Récupérer les types d'utilisateurs pour le formulaire
    ldap_model = LDAPModel()
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
    
    if request.method == 'POST':
        # Récupérer les données du formulaire (peut être soit du formulaire visible ou caché)
        user_type = request.form.get('user_type') or request.form.get('hidden_user_type')
        given_name = request.form.get('givenName') or request.form.get('hidden_givenName')
        sn = request.form.get('sn') or request.form.get('hidden_sn')
        email = request.form.get('email') or request.form.get('hidden_email')
        favvnatnr = request.form.get('favvNatNr') or request.form.get('hidden_favvNatNr', '')
        manager = request.form.get('manager') or request.form.get('hidden_manager', '')
        
        # Récupérer les valeurs des overrides
        email_override = (request.form.get('email_override') == 'true') or (request.form.get('hidden_email_override') == 'true')
        favvnatnr_override = (request.form.get('favvNatNr_override') == 'true') or (request.form.get('hidden_favvNatNr_override') == 'true')
        manager_override = (request.form.get('manager_override') == 'true') or (request.form.get('hidden_manager_override') == 'true')
        
        
        # Sauvegarder les valeurs du formulaire
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
            return render_template('user_creation.html', form=form, form_data=form_data)
        
        # Valider l'email (obligatoire sauf si override)
        if not email and not email_override:
            flash("L'adresse email est obligatoire.", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data)
        
        # Vérifier si un chef hiérarchique est requis pour ce type d'utilisateur
        is_stag = user_type == "STAG" 
        if is_stag and not manager and not manager_override:
            flash("Un chef hiérarchique est obligatoire pour les stagiaires.", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data)
        
        # Vérifier si un utilisateur avec cette combinaison de nom existe déjà
        exists, existing_dn = ldap_model.check_name_combination_exists(given_name, sn)
        if exists:
            flash(f"Un utilisateur avec le nom '{given_name} {sn}' existe déjà dans l'annuaire ({existing_dn}). Veuillez utiliser une combinaison de nom différente.", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data)
        
        # Vérifier le FavvNatNr si le type d'utilisateur est BOODOCI ou OCI
        if (user_type == "BOODOCI" or user_type == "OCI"):
            if not favvnatnr and not favvnatnr_override:
                flash("Le numéro de registre national est obligatoire pour les utilisateurs de type OCI.", 'error')
                return render_template('user_creation.html', form=form, form_data=form_data)
            
            # Vérifier si ce FavvNatNr existe déjà (seulement s'il est fourni)
            if favvnatnr:
                # Normaliser le FavvNatNr
                normalized_favvnatnr = favvnatnr.replace(' ', '').replace('-', '')
                
                exists, existing_dn, fullname = ldap_model.check_favvnatnr_exists(normalized_favvnatnr)
                if exists:
                    flash(f"Un utilisateur avec le numéro national '{favvnatnr}' existe déjà dans l'annuaire: {fullname} ({existing_dn}). Veuillez utiliser un numéro différent.", 'error')
                    return render_template('user_creation.html', form=form, form_data=form_data)
        
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
            result, generated_password = ldap_model.create_user(cn, ldap_attributes)
            if result:
                # Afficher un message de succès avec le mot de passe généré
                flash(f"Utilisateur {sn} {given_name} (CN: {cn}) créé avec succès! Mot de passe: {generated_password}", 'success')
                # Réinitialiser form_data pour un nouveau formulaire vide
                form_data = {
                    'user_type': '',
                    'givenName': '',
                    'sn': '',
                    'email': '',
                    'favvNatNr': '',
                    'manager': ''
                }
                return render_template('user_creation.html', form=form, form_data=form_data)
            else:
                flash(f"Échec de la création de l'utilisateur.", 'error')
                return render_template('user_creation.html', form=form, form_data=form_data)
        except Exception as e:
            flash(f"Une erreur est survenue: {str(e)}", 'error')
            return render_template('user_creation.html', form=form, form_data=form_data)

    # Rendre le template avec le formulaire (pour les requêtes GET)
    return render_template('user_creation.html', form=form, form_data=form_data)


# @usercreation_bp.route('/get_template_details', methods=['GET'])
# @login_required
# def get_template_details():
#     template_cn = request.args.get('template_cn', '')
#     if not template_cn:
#         return jsonify({'error': 'Template CN is required'}), 400
    
#     ldap_model = LDAPModel()
#     template_details = ldap_model.get_template_details(template_cn)
    
#     if template_details:
#         return jsonify(template_details)
#     else:
#         return jsonify({'error': 'Template not found'}), 404