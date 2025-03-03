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
    
    # Ne pas effectuer de recherche si moins de 3 caractères
    if len(search_term) < 3:
        return jsonify([])
        
    try:
        # Mise en cache simple en utilisant une variable globale ou Redis/Memcached
        # Exemple simple avec les 10 dernières recherches
        if not hasattr(autocomplete_fullName, 'cache'):
            autocomplete_fullName.cache = {}
        
        # Vérifier si le résultat existe dans le cache
        if search_term in autocomplete_fullName.cache:
            return jsonify(autocomplete_fullName.cache[search_term])
        
        # Effectuer la requête LDAP
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete_fullName(search_term)
        
        # Limiter les résultats retournés
        limited_result = result[:20]  # Limiter à 20 résultats maximum
        
        # Stocker dans le cache
        autocomplete_fullName.cache[search_term] = limited_result
        
        # Nettoyer le cache s'il devient trop grand
        if len(autocomplete_fullName.cache) > 100:
            # Supprimer les premiers éléments ajoutés
            keys = list(autocomplete_fullName.cache.keys())
            for key in keys[:50]:
                del autocomplete_fullName.cache[key]
                
        return jsonify(limited_result)
    except Exception as e:
        print(f"Erreur d'autocomplétion: {str(e)}")
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
    

@autocomplete_bp.route('/autocomplete_managers', methods=['GET'])
@login_required
def autocomplete_managers():
    search_term = request.args.get('term', '')
    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete_managers(search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500