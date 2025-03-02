from flask import Blueprint, render_template, request, redirect, json
from flask_app.utils.file_utils import validate_entries, apply_changes
from flask_app.utils.ldap_utils import login_required

# Load group DN options from JSON file
with open('flask_app/utils/group_dn_options.json', 'r') as f:
    group_dn_options = json.load(f)

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file:
            # Save the uploaded file temporarily
            file_path = f"flask_app/uploads/{file.filename}"
            file.save(file_path)
            
            # Get the selected group DN structure from the form
            group_dn_structure = request.form['group_dn']
            
            # Validate the CSV entries
            valid_entries, invalid_entries = validate_entries(file_path, group_dn_structure)
            
            # Render the validation report
            return render_template('report.html', 
                                 valid_entries=valid_entries, 
                                 invalid_entries=invalid_entries,
                                 file_path=file_path,
                                 group_dn_structure=group_dn_structure)
    return render_template('upload.html', group_dn_options=group_dn_options)

@upload_bp.route('/apply', methods=['POST'])
@login_required
def apply():
    file_path = request.form['file_path']
    group_dn_structure = request.form['group_dn_structure']

    # Validate the CSV entries again (for safety)
    valid_entries, _ = validate_entries(file_path, group_dn_structure)

    # Apply the changes
    success_count, failure_count, failures = apply_changes(valid_entries, group_dn_structure)

    # Render the results
    return render_template('results.html',
                         success_count=success_count,
                         failure_count=failure_count,
                         failures=failures)