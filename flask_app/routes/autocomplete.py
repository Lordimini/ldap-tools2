from flask import Blueprint, request, jsonify, session, flash, json
from flask_app.models.ldap import LDAPModel
from flask_app.utils.ldap_utils import login_required

autocomplete_bp = Blueprint('autocomplete', __name__)

@autocomplete_bp.route('/autocomplete_groups', methods=['GET'])
@login_required
def autocomplete_groups():
    search_term = request.args.get('term', '')
    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete_group(search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500
    
@autocomplete_bp.route('/autocomplete_fullName', methods=['GET'])
@login_required
def autocomplete_fullName():
    search_term = request.args.get('term', '')
    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete_fullName(search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500

@autocomplete_bp.route('/autocomplete_roles', methods=['GET'])
@login_required
def autocomplete_roles():
    search_term = request.args.get('term', '')
    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete_role(search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500


@autocomplete_bp.route('/autocomplete_services', methods=['GET'])
@login_required
def autocomplete_services():
    search_term = request.args.get('term', '')

    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete_services(search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500