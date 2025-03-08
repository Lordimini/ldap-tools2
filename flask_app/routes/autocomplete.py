from flask import Blueprint, request, jsonify, session, flash, json
from flask_app.models.ldap import LDAPModel
from flask_app.utils.ldap_utils import login_required
from functools import lru_cache

autocomplete_bp = Blueprint('autocomplete', __name__)

# Cache pour les résultats d'autocomplétion
autocomplete_cache = {}
MAX_CACHE_SIZE = 100

def get_cached_result(search_type, search_term):
    """Récupère un résultat depuis le cache"""
    cache_key = f"{search_type}:{search_term}"
    return autocomplete_cache.get(cache_key)

def set_cached_result(search_type, search_term, result):
    """Stocke un résultat dans le cache"""
    cache_key = f"{search_type}:{search_term}"
    autocomplete_cache[cache_key] = result
    
    # Nettoyer le cache s'il devient trop grand
    if len(autocomplete_cache) > MAX_CACHE_SIZE:
        keys = list(autocomplete_cache.keys())
        for key in keys[:MAX_CACHE_SIZE//2]:  # Supprimer la moitié du cache
            del autocomplete_cache[key]

@autocomplete_bp.route('/autocomplete_groups', methods=['GET'])
@login_required
def autocomplete_groups():
    search_term = request.args.get('term', '')
    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete('group', search_term)
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
        # Vérifier si le résultat existe dans le cache
        cached_result = get_cached_result('fullName', search_term)
        if cached_result:
            return jsonify(cached_result)
        
        # Effectuer la requête LDAP avec la nouvelle fonction unifiée
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete('fullName', search_term)
        
        # Limiter les résultats retournés
        limited_result = result[:20]  # Limiter à 20 résultats maximum
        
        # Stocker dans le cache
        set_cached_result('fullName', search_term, limited_result)
                
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
        result = ldap_model.autocomplete('roles', search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500


@autocomplete_bp.route('/autocomplete_services', methods=['GET'])
@login_required
def autocomplete_services():
    search_term = request.args.get('term', '')

    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete('services', search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500
    

@autocomplete_bp.route('/autocomplete_managers', methods=['GET'])
@login_required
def autocomplete_managers():
    search_term = request.args.get('term', '')
    try:
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete('managers', search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500


# Route unifiée optionnelle (peut être utilisée parallèlement aux routes existantes)
@autocomplete_bp.route('/autocomplete', methods=['GET'])
@login_required
def unified_autocomplete():
    """
    Route d'autocomplétion unifiée.
    
    Paramètres GET:
    - type: Type de recherche (group, fullName, role, services, managers)
    - term: Terme de recherche
    
    Exemple: /autocomplete?type=fullName&term=dupont
    """
    search_type = request.args.get('type', '')
    search_term = request.args.get('term', '')
    
    # Validation des paramètres
    if not search_type or not search_term:
        return jsonify({"error": "Les paramètres 'type' et 'term' sont requis"}), 400
        
    # Vérification spécifique pour fullName
    if search_type == 'fullName' and len(search_term) < 3:
        return jsonify([])
    
    try:
        # Vérifier si le résultat existe dans le cache
        cached_result = get_cached_result(search_type, search_term)
        if cached_result:
            return jsonify(cached_result)
            
        # Effectuer la recherche
        ldap_model = LDAPModel()
        result = ldap_model.autocomplete(search_type, search_term)
        
        # Mettre en cache le résultat
        set_cached_result(search_type, search_term, result)
        
        return jsonify(result)
    except Exception as e:
        print(f"Erreur d'autocomplétion ({search_type}): {str(e)}")
        return jsonify([]), 500