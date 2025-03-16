# Guide d'intégration du système de menu dynamique

Ce guide explique comment intégrer le nouveau système de menu dynamique qui prend en compte à la fois le rôle de l'utilisateur (admin/reader) et la source LDAP (meta/idme).

## 1. Installer le nouveau service de menu

Commencez par copier le fichier `enhanced_menu_service.py` dans le répertoire `flask_app/services/`.

## 2. Modifier l'initialisation de l'application

Mettez à jour votre fichier `flask_app/__init__.py` pour initialiser le nouveau service de menu :

```python
from flask_app.services.enhanced_menu_service import EnhancedMenuService

# Créer une instance du service de menu
enhanced_menu_service = EnhancedMenuService()

def create_app():
    app = Flask(__name__, static_folder='static')
    app.secret_key = 'eyqscmnc'  # À remplacer par une clé secrète sécurisée en production
    
    # Initialize LDAP config manager
    ldap_config_manager.init_app(app)
    app.ldap_config_manager = ldap_config_manager
    
    # Initialize login manager
    init_login_manager(app)
    
    # Initialize enhanced menu service
    enhanced_menu_service.init_app(app)
    app.enhanced_menu_service = enhanced_menu_service
    
    # ...
```

## 3. Modifier le template de base

Mettez à jour le fichier `flask_app/templates/base.html` pour utiliser le nouveau service de menu. Remplacez la ligne :

```html
{{ menu_config.render_menu()|safe }}
```

par :

```html
{{ enhanced_menu_service.render_menu()|safe }}
```

## 4. Mettre à jour les handlers avant requête

Assurez-vous que le handler `before_request` passe la source LDAP au nouveau service de menu. Modifiez votre fichier :

```python
@app.before_request
def before_request():
    g.user = current_user
    # Ajout de la source LDAP à g
    g.ldap_source = session.get('ldap_source', 'meta')
    
    # Si l'utilisateur est connecté, s'assurer que la config LDAP est définie pour l'utilisateur actuel
    if current_user.is_authenticated:
        g.user_roles = current_user.roles
        
        # Définir le nom LDAP pour l'affichage
        ldap_source = current_user.ldap_source
        g.ldap_name = app.ldap_config_manager.get_config(ldap_source).get('LDAP_name', 'LDAP')
        
        # Mettre à jour la source LDAP dans l'utilisateur actuel si elle a changé
        if ldap_source != session.get('ldap_source'):
            current_user.ldap_source = session.get('ldap_source')
```

## 5. Gérer le changement de source LDAP

Assurez-vous que votre code JavaScript pour le sélecteur de source LDAP recharge la page après le changement :

```javascript
// Dans static/js/main.js ou un fichier similaire
$(document).ready(function() {
    // Gestionnaire pour le changement de source LDAP
    $('#ldap_source_selector').change(function() {
        var selected_source = $(this).val();
        
        // Appel AJAX pour changer la source en session
        $.ajax({
            url: '/change_ldap_source',
            method: 'POST',
            data: {
                'source': selected_source
            },
            success: function(response) {
                if (response.success) {
                    // Recharger la page pour mettre à jour le menu
                    location.reload();
                }
            }
        });
    });
});
```

## 6. Créer la route pour changer de source LDAP

Si ce n'est pas déjà fait, assurez-vous d'avoir une route pour changer la source LDAP :

```python
@app.route('/change_ldap_source', methods=['POST'])
@login_required
def change_ldap_source():
    source = request.form.get('source')
    if source in app.ldap_config_manager.get_available_configs():
        session['ldap_source'] = source
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Source LDAP invalide'})
```

## 7. Tester le nouveau système

1. Connectez-vous avec un utilisateur ayant le rôle admin
2. Vérifiez que le menu affiche les éléments corrects pour votre source LDAP actuelle
3. Changez de source LDAP et vérifiez que le menu est mis à jour correctement
4. Déconnectez-vous et reconnectez-vous avec un utilisateur reader
5. Répétez les tests avec différentes sources LDAP

## Notes importantes

- Le nouveau système utilise les fichiers de menu existants sans modification
- Les menus sont fusionnés intelligemment pour éviter les doublons
- Les permissions sont respectées dans les deux systèmes
- La source LDAP est automatiquement ajoutée aux URLs des liens du menu