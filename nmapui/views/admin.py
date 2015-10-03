from nmapui import app
from nmapui.models import User, Users, Permission
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask.ext.login import login_required, current_user

appmodule = Blueprint('admin', __name__, url_prefix='/admin')

@appmodule.route("/")
@login_required
def admin():
    """admin page - used to manage user accounts and permissions"""
    if not current_user.has_permission("admin"):
        abort(403)

    return render_template("admin_index.html")


@appmodule.route("/users")
@appmodule.route("/users/")
@login_required
def users_redirect():
    return redirect("/admin/users/1")

@appmodule.route("/users/<int:page>")
@login_required
def users(page=1):
    """admin page - used to manage user accounts and permissions"""
    if not current_user.has_permission("admin"):
        abort(403)

    _users = User.query.paginate(page,app.config["ITEMS_PER_PAGE"])
    return render_template("admin_users.html",
                           users=_users)

@appmodule.route("/add_user", methods=["GET", "POST"])
@login_required
def add_user():
    """add user"""
    if not current_user.has_permission("admin"):
        abort(403)

    if (request.method == 'POST'):
        # validate data
        if ('username' in request.form and len(request.form['username']) and \
            'password' in request.form and len(request.form['password']) and \
            'email' in request.form and len(request.form['email'])):

            # TODO is das hier fies?! hard nach str konvertieren?
            _username = str(request.form['username'])
            _password = str(request.form['password'])
            _email = str(request.form['email'])

            try:
                new_user = Users.add(username=_username,
                                     email=_email,
                                     clear_pw=_password)

                flash("Successfully created " + _username + " with ID " + \
                      str(new_user.id), 'success')
                return redirect("/admin/users/1")
            except ValueError as ve:
                flash("Failed to add User: Username already in use.", "danger")
                return redirect("/admin/users/1")
            except Exception as e:
                flash("Something went wrong.", "danger")
                return redirect("/admin/users/1")

    else:
        return render_template("admin_add_user.html")


@appmodule.route("/permissions")
@appmodule.route("/permissions/")
@login_required
def permissions_redirect():
    return redirect("/admin/permissions/1")

@appmodule.route("/permissions/<int:page>")
@login_required
def permissions(page=1):
    """admin page - used to manage user accounts and permissions"""
    if not current_user.has_permission("admin"):
        abort(403)
    _permissions = Permission.query.paginate(page,app.config["ITEMS_PER_PAGE"])
    _users = User.query.all()
    return render_template("admin_permissions.html",
                           permissions=_permissions,
                           users=_users)

@appmodule.route("/add_permission", methods=["GET", "POST"])
@login_required
def add_permission():
    """add permission"""
    if not current_user.has_permission("admin"):
        abort(403)

    if (request.method == 'POST'):
        # validate data
        if ('name' in request.form and len(request.form['name'])):
            # TODO is das hier fies?! hard nach str konvertieren?
            _name = str(request.form['name'])
            if ('comment' in request.form and len(request.form['comment'])):
                _comment = str(request.form['comment'])
            else:
                _comment = None

            try:
                new_permission = Permission.add(name=_name,
                                                comment=_comment)

                flash("Successfully created " + _name + " with ID " + \
                      str(new_permission.id), 'success')
                return redirect("/admin/permissions/1")
            except Exception as e:
                flash("Something went wrong.", "danger")
                return redirect("/admin/permissions/1")

    else:
        return render_template("admin_add_permission.html")


