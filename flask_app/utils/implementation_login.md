# Flask LDAP Manager - Role-Based Access Control Implementation Guide

This guide explains how to implement the role-based access control and dynamic menu system in your Flask LDAP Manager application.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Installation Requirements](#installation-requirements)
3. [Integration Steps](#integration-steps)
4. [Configuration & Customization](#configuration--customization)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)

## Project Structure

The enhanced LDAP Manager includes the following new components:

```
flask_app/
├── __init__.py                 # Updated application factory
├── config/
│   ├── menu_base.json          # Base menu configuration
│   ├── menu_role_admin.json    # Admin-specific menu
│   └── menu_role_reader.json   # Reader-specific menu
├── models/
│   └── user_model.py           # Enhanced User model with roles
├── services/
│   ├── login_manager.py        # Flask-Login integration
│   └── menu_config.py          # Dynamic menu service
├── routes/
│   └── auth.py                 # Updated authentication routes
└── templates/
    ├── base.html               # Updated base template
    ├── login.html              # Updated login page
    ├── user_profile.html       # New user profile page
    ├── access_denied.html      # Access denied page
    └── errors/                 # Error pages
        ├── 403.html            # Forbidden error page
        ├── 404.html            # Not found error page
        └── 500.html            # Server error page
```

## Installation Requirements

Add the following packages to your requirements.txt:

```
flask>=2.0.0
flask-login>=0.6.2
ldap3>=2.9.0
```

Install with:

```bash
pip install -r requirements.txt
```

## Integration Steps

### 1. Copy the New Files

First, copy all the new files into your project structure, maintaining the directory organization.

### 2. Update Existing Files

Update the following existing files:

- `flask_app/__init__.py`: Replace with the new version to initialize login manager
- `flask_app/routes/auth.py`: Replace with the enhanced version for role-based login
- `flask_app/templates/base.html`: Replace with the version supporting dynamic menus
- `flask_app/templates/login.html`: Replace with the updated login template

### 3. Configure Menu JSON Files

Customize the menu configuration files in the `config/` directory to match your application's needs:

- `menu_base.json`: Base menu for all users
- `menu_role_admin.json`: Admin-specific menu items
- `menu_role_reader.json`: Reader-specific menu items

You can add more role-specific menu files by following the naming convention `menu_role_ROLENAME.json`.

### 4. Update Route Decorators

Update your route functions to use the appropriate access control decorators:

```python
from flask_app.models.user_model import role_required, permission_required, admin_required

# Role-based access
@app.route('/admin_only')
@role_required('admin')
def admin_only_route():
    # Only users with 'admin' role can access
    return render_template('admin_page.html')

# Permission-based access
@app.route('/manage_users')
@permission_required('edit_users')
def manage_users_route():
    # Only users with 'edit_users' permission can access
    return render_template('manage_users.html')

# Admin-only access
@app.route('/system_settings')
@admin_required
def system_settings_route():
    # Only admins can access
    return render_template('system_settings.html')
```

## Configuration & Customization

### User Roles & Permissions

Roles and permissions are derived from LDAP group memberships. The default roles are:

- `admin`: Members of the admin group specified in LDAP config
- `reader`: Members of the reader group specified in LDAP config

You can customize how roles and permissions are assigned by modifying the `User.from_ldap_data()` method in `user_model.py`.

### Menu Configuration

Menu items are defined in JSON files with the following structure:

```json
{
  "menu_items": [
    {
      "label": "Dashboard",
      "url": "/dashboard",
      "icon": "bi bi-speedometer2",
      "active_pattern": "^/dashboard"
    },
    {
      "is_section": true,
      "label": "SECTION TITLE",
      "items": [
        {
          "label": "Menu Item",
          "url": "/some/path",
          "icon": "bi bi-icon-name",
          "active_pattern": "^/some/path",
          "required_permission": "permission_name"
        }
      ]
    }
  ]
}
```

Each menu item can have the following properties:

- `label`: Display text for the menu item
- `url`: Target URL for the menu item
- `icon`: Bootstrap icon class (using Bootstrap Icons)
- `active_pattern`: Regex pattern to determine if menu item is active
- `required_permission`: Optional permission required to see this item
- `admin_only`: Set to `true` to make this item admin-only
- `is_section`: Set to `true` for section headers with sub-items

### Adding New Roles

To add a new role:

1. Create a new menu configuration file `flask_app/config/menu_role_newrole.json`
2. Update the logic in `User.from_ldap_data()` to assign the new role
3. Assign permissions for the new role in the same method

## Usage Examples

### Accessing Current User in Templates

The current user is available in templates via `current_user`:

```html
{% if current_user.is_authenticated %}
  <p>Welcome, {{ current_user.name }}!</p>
  
  {% if current_user.is_admin %}
    <p>You have admin privileges.</p>
  {% endif %}
  
  {% if current_user.has_permission('edit_users') %}
    <a href="{{ url_for('user.edit') }}">Edit Users</a>
  {% endif %}
{% endif %}
```

### Checking Permissions in Views

You can check permissions in your views:

```python
from flask import g

@app.route('/some_route')
@login_required
def some_route():
    if g.user.has_permission('view_reports'):
        # Show reports
        reports = get_reports()
        return render_template('reports.html', reports=reports)
    else:
        # Show limited information
        return render_template('limited_view.html')
```

### Dynamic Form Elements Based on Roles

You can dynamically show/hide form elements based on roles:

```html
<form method="post">
  <!-- Fields visible to all -->
  <input type="text" name="name" value="{{ user.name }}" required>
  
  <!-- Admin-only fields -->
  {% if current_user.is_admin %}
    <div class="admin-section">
      <h3>Advanced Settings</h3>
      <select name="permission_level">
        <option value="1">Standard</option>
        <option value="2">Power User</option>
        <option value="3">Administrator</option>
      </select>
    </div>
  {% endif %}
  
  <button type="submit">Save</button>
</form>
```

## Troubleshooting

### User Not Getting Correct Roles

If a user is not getting the correct roles:

1. Check the LDAP group memberships in the LDAP directory
2. Verify the `admin_group_dn` and `reader_group_dn` in your LDAP config
3. Debug by printing the LDAP search results in `authenticate_user()`

### Menu Items Not Showing

If menu items are not showing correctly:

1. Check the user's roles and permissions in the profile page
2. Verify that menu items have the correct `required_permission` values
3. Check for typos in role names or permission names

### Access Denied Errors

If you're getting unexpected access denied errors:

1. Verify the user is authenticated (check session data)
2. Check that the user has the required roles/permissions
3. Review the route decorators to ensure they match the user's roles

### LDAP Authentication Issues

For LDAP authentication problems:

1. Check the LDAP server connection settings
2. Verify the bind DN and password
3. Check that the user DN is correctly formatted
4. Enable LDAP debugging for more detailed error messages

For more assistance, refer to the Flask-Login and LDAP3 documentation.