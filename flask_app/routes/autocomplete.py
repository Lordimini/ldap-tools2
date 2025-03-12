from flask import Blueprint, request, jsonify, session, flash, json
from flask_app.models.edir_model import EDIRModel
from flask_app.utils.ldap_utils import login_required
from functools import lru_cache
from flask_app.models.ldap_config_manager import LDAPConfigManager


autocomplete_bp = Blueprint('autocomplete', __name__)

# Cache pour les résultats d'autocomplétion
autocomplete_cache = {}
MAX_CACHE_SIZE = 100

def get_cached_result(ldap_source, search_type, search_term):
    """Récupère un résultat depuis le cache"""
    cache_key = f"{ldap_source}:{search_type}:{search_term}"
    return autocomplete_cache.get(cache_key)

def set_cached_result(ldap_source, search_type, search_term, result):
    """Stocke un résultat dans le cache"""
    cache_key = f"{ldap_source}:{search_type}:{search_term}"
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
    # Récupérer la source LDAP
    ldap_source = request.args.get('source', 'meta')
    
    try:
        # Créer une instance du modèle LDAP avec la source spécifiée
        ldap_model = EDIRModel(source=ldap_source)
        result = ldap_model.autocomplete('group', search_term)
        return jsonify(result)
    except Exception as e:
        print(f"Erreur d'autocomplétion des groupes: {str(e)}")
        return jsonify([]), 500
    
@autocomplete_bp.route('/autocomplete_fullName', methods=['GET'])
@login_required
def autocomplete_fullName():
    search_term = request.args.get('term', '')
    # Récupérer la source LDAP
    ldap_source = request.args.get('source', 'meta')
    
    # Ne pas effectuer de recherche si moins de 3 caractères
    if len(search_term) < 3:
        return jsonify([])
        
    try:
        # Vérifier si le résultat existe dans le cache
        cached_result = get_cached_result(ldap_source, 'fullName', search_term)
        if cached_result:
            return jsonify(cached_result)
        
        # Créer une instance du modèle LDAP avec la source spécifiée
        ldap_model = EDIRModel(source=ldap_source)
        result = ldap_model.autocomplete('fullName', search_term)
        
        # Limiter les résultats retournés
        limited_result = result[:20]  # Limiter à 20 résultats maximum
        
        # Stocker dans le cache
        set_cached_result(ldap_source, 'fullName', search_term, limited_result)
                
        return jsonify(limited_result)
    except Exception as e:
        print(f"Erreur d'autocomplétion: {str(e)}")
        return jsonify([]), 500

@autocomplete_bp.route('/autocomplete_roles', methods=['GET'])
@login_required
def autocomplete_roles():
    search_term = request.args.get('term', '')
    # Récupérer la source LDAP
    ldap_source = request.args.get('source', 'meta')
    
    print(f"Recherche de rôles avec le terme: '{search_term}' (source: {ldap_source})")
    
    try:
        # Créer une instance du modèle LDAP avec la source spécifiée
        ldap_model = EDIRModel(source=ldap_source)
        # Utiliser la fonction spécifique pour les rôles
        result = ldap_model.autocomplete_role(search_term)
        print(f"Résultats trouvés: {len(result)}")
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"Erreur d'autocomplétion des rôles: {str(e)}")
        print(traceback.format_exc())
        return jsonify([]), 500


@autocomplete_bp.route('/autocomplete_services', methods=['GET'])
@login_required
def autocomplete_services():
    search_term = request.args.get('term', '')
    # Récupérer la source LDAP
    ldap_source = request.args.get('source', 'meta')
    
    print(f"Recherche de services avec le terme: '{search_term}' (source: {ldap_source})")
    
    try:
        # Vérifier si le résultat existe dans le cache
        cached_result = get_cached_result(ldap_source, 'services', search_term)
        if cached_result:
            print(f"Résultats (du cache): {len(cached_result)}")
            return jsonify(cached_result)
        
        # Créer une instance du modèle LDAP avec la source spécifiée
        ldap_model = EDIRModel(source=ldap_source)
        # Utiliser la fonction spécifique pour les services
        result = ldap_model.autocomplete_services(search_term)
        print(f"Résultats trouvés: {len(result)}")
        
        # Mettre en cache le résultat
        set_cached_result(ldap_source, 'services', search_term, result)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"Erreur d'autocomplétion des services: {str(e)}")
        print(traceback.format_exc())
        return jsonify([]), 500
    

@autocomplete_bp.route('/autocomplete_managers', methods=['GET'])
@login_required
def autocomplete_managers():
    search_term = request.args.get('term', '')
    # Récupérer la source LDAP
    ldap_source = request.args.get('source', 'meta')
    
    try:
        # Créer une instance du modèle LDAP avec la source spécifiée
        ldap_model = EDIRModel(source=ldap_source)
        result = ldap_model.autocomplete('managers', search_term)
        return jsonify(result)
    except Exception as e:
        print(f"Erreur d'autocomplétion des managers: {str(e)}")
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
    - source: Source LDAP (meta, idme)
    
    Exemple: /autocomplete?type=fullName&term=dupont&source=meta
    """
    search_type = request.args.get('type', '')
    search_term = request.args.get('term', '')
    # Récupérer la source LDAP
    ldap_source = request.args.get('source', 'meta')
    
    # Validation des paramètres
    if not search_type or not search_term:
        return jsonify({"error": "Les paramètres 'type' et 'term' sont requis"}), 400
        
    # Vérification spécifique pour fullName
    if search_type == 'fullName' and len(search_term) < 3:
        return jsonify([])
    
    try:
        # Vérifier si le résultat existe dans le cache
        cached_result = get_cached_result(ldap_source, search_type, search_term)
        if cached_result:
            return jsonify(cached_result)
            
        # Créer une instance du modèle LDAP avec la source spécifiée
        ldap_model = EDIRModel(source=ldap_source)
        result = ldap_model.autocomplete(search_type, search_term)
        
        # Mettre en cache le résultat
        set_cached_result(ldap_source, search_type, search_term, result)
        
        return jsonify(result)
    except Exception as e:
        print(f"Erreur d'autocomplétion ({search_type}): {str(e)}")
        return jsonify([]), 500