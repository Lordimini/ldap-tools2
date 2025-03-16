from flask import Blueprint, render_template, request,json
from flask_app.utils.token_utils import fetch_new_token
from flask_login import login_required  # Nouvel import depuis Flask-Login

token_bp = Blueprint('token', __name__)

@token_bp.route('/generate_token', methods=['GET', 'POST'])
@login_required
def generate_token():
    response_data = None
    if request.method == 'POST':
        try:
            fetch_new_token()
            response_data = json.dumps(TOKEN_INFO, indent=4)
        except Exception as e:
            response_data = f"Error: {str(e)}"
    return render_template('generate_token.html', response_data=response_data)