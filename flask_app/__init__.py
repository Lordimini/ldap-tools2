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

def create_app():
    app = Flask(__name__,)
    app.secret_key = 'eyqscmnc'
    
    # Register blueprints
    #app.register_blueprint(auth_bp, url_prefix='/auth')
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

    return app