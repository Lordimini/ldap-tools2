from flask import Blueprint, render_template, request, flash, session
from flask_app.models.ldap import LDAPModel
from flask_app.utils.ldap_utils import login_required

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_user():
    if request.method == 'POST':
        search_term = request.form['search_term']
        search_type = request.form['search_type'] # 'cn' or 'workforceID' or 'FavvNatNr'
        ldap_model = LDAPModel()
        result = ldap_model.search_user(search_term, search_type)
        if result:
            return render_template('search.html', result=result)
        else:
            flash('User not found.', 'danger')
    prefill_cn = request.args.get('cn', '')
    prefill_workforceID = request.args.get('workforceID', '')
    prefill_FavvNatNr = request.args.get('FavvNatNr', '')
    return render_template('search.html', result=None, prefill_cn=prefill_cn, prefill_workforceID=prefill_workforceID, prefill_FavvNatNr=prefill_FavvNatNr)
    #return render_template('search.html', result=None)