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
    email = StringField('Email (optional)')
    favvNatNr = HiddenField('FavvNatNr')

@usercreation_bp.route('/fetch_user_types')
def fetch_user_types():
    ldap_model = LDAPModel()
    user_types = ldap_model.get_user_types_from_ldap('ou=tpl,ou=sync,o=copy')  # Adjust the DN as needed
    return jsonify(user_types)

@usercreation_bp.route('/user_creation', methods=['GET', 'POST'])
@login_required
def create_user():
    
    form = UserCreationForm()
    if request.method == 'POST':
        user_type = request.form['user_type']
        given_name = request.form.get('givenName')
        sn = request.form.get('sn')
        email = request.form.get('email')

        # Validate mandatory fields
        if not given_name or not sn:
            flash("Given Name and Surname are required.", 'error')
            return redirect(url_for('usercreation.create_user'))
        
        ldap_model = LDAPModel()
        
        # Check if a user with this name combination already exists
        exists, existing_dn = ldap_model.check_name_combination_exists(given_name, sn)
        if exists:
            flash(f"A user with the name '{given_name} {sn}' already exists in the directory ({existing_dn}). Please use a different name combination.", 'error')
            return redirect(url_for('usercreation.create_user'))
        
        # Get template details for the selected user type
        template_details = ldap_model.get_template_details(user_type)
        
        # Generate a unique CN for the new user
        cn = ldap_model.generate_unique_cn(given_name, sn)
        
        # Define LDAP attributes based on user type
        ldap_attributes = {
            'givenName': [given_name],
            'sn': [sn],
            'cn': [cn],
            # Create fullName as sn + givenName with space in between
            'fullName': [f"{sn} {given_name}"]
        }
        
        # Add email if provided
        if email:
            ldap_attributes['mail'] = [email]
        
        # Add title from template if available
        if template_details and template_details.get('title'):
            ldap_attributes['title'] = [template_details['title']]

        if user_type == "OCI":
            favvNatNr = request.form.get('favvNatNr')
            if not favvNatNr:
                flash("FavvNatNr is required for OCI users.", 'error')
                return redirect(url_for('usercreation.create_user'))
            ldap_attributes['favvNatNr'] = [favvNatNr]

        try:
            result, generated_password = ldap_model.create_user(cn, ldap_attributes)
            if result:
            # Show success message with generated password
                flash(f"User {sn} {given_name} (CN: {cn}) created successfully! Password: {generated_password}", 'success')
                return redirect(url_for('usercreation.create_user'))
            else:
                flash(f"Failed to create user.", 'error')
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')

    # Fetch user types and pre-populate the form
    ldap_model = LDAPModel()
    user_types = ldap_model.get_user_types_from_ldap('ou=tpl,ou=sync,o=copy')
    form.user_type.choices = [(ut['value'], ut['label']) for ut in user_types]

    # Render the template with form
    return render_template('user_creation.html', form=form)