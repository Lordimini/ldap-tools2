from flask import Flask
from flask_app.routes.auth import auth_bp
from flask_app.routes.dashboard import dashboard_bp
from flask_app.routes.search import search_bp
from flask_app.routes.group import group_bp
from flask_app.routes.role import role_bp
from flask_app.routes.service import service_bp
from flask_app.routes.ldap import ldap_bp
from flask_app.routes.user import user_bp
from flask_app.routes.token import token_bp
from flask_app.routes.upload import upload_bp
from flask_app.routes.autocomplete import autocomplete_bp
from flask_app.routes.usercreation import usercreation_bp
from flask_app.routes.postcreation import postcreation_bp
from flask_app.routes.userupdate import userupdate_bp
from flask_app.services.menu_config import MenuConfig
from flask_app.services.login_manager import init_login_manager
from flask_app.models.ldap_config_manager import LDAPConfigManager

# Initialize services
menu_config = MenuConfig()
ldap_config_manager = LDAPConfigManager()

def create_app():
    """
    Application factory function to create and configure the Flask app
    """
    app = Flask(__name__, static_folder='static')
    app.secret_key = 'eyqscmnc'  # Replace with a secure secret key in production
    
    # Initialize LDAP config manager
    ldap_config_manager.init_app(app)
    app.ldap_config_manager = ldap_config_manager
    
    # Initialize login manager
    init_login_manager(app)
    
    # Initialize menu service
    menu_config.init_app(app)
    
    # Make menu service available in templates
    @app.context_processor
    def inject_menu_service():
        return dict(menu_config=menu_config)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """
    Register all blueprints with the Flask app
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(ldap_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(token_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(autocomplete_bp)
    app.register_blueprint(usercreation_bp)
    app.register_blueprint(postcreation_bp)
    app.register_blueprint(userupdate_bp)

def register_error_handlers(app):
    """
    Register error handlers for common HTTP errors
    """
    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("errors/403.html"), 403
    
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404
    
    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/500.html"), 500