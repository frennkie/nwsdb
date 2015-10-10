from nwscandb import app
from nwscandb import db
from nwscandb.models import User, Users, UserGroup
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

    print(request.endpoint)

    _query = User.query
    _items_per_page = app.config["ITEMS_PER_PAGE"]
    _items_paged = _query.paginate(page, _items_per_page)

    return render_template('admin_users.html',
                           items_paged=_items_paged,
                           endpoint=request.endpoint)


@appmodule.route("/add_user", methods=["GET", "POST"])
@login_required
def add_user():
    """add user"""
    if not current_user.has_permission("admin"):
        abort(403)

    if request.method == 'POST':
        # validate data
        if ('username' in request.form and len(request.form['username']) and
            'password' in request.form and len(request.form['password']) and
            'email' in request.form and len(request.form['email'])):

            # TODO is das hier fies?! hart nach str konvertieren?
            _username = str(request.form['username'])
            _password = str(request.form['password'])
            _email = str(request.form['email'])

            if 'inactive' in request.form:
                inactive = 1
            else:
                inactive = 0

            try:
                new_user = Users.add(username=_username,
                                     email=_email,
                                     clear_pw=_password,
                                     inactive=inactive)

                flash("Successfully created " + _username + " with ID " +
                      str(new_user.id), 'success')
                return redirect(url_for("admin.users", page=1))
            except ValueError as ve:
                flash("Failed to add User: Username already in use.", "danger")
                return redirect(url_for("admin.users", page=1))
            except Exception as e:
                flash("Something went wrong.", "danger")
                return redirect(url_for("admin.users", page=1))

    else:
        return render_template("admin_add_user.html")


@appmodule.route("/user/<int:user_id>/change_password", methods=["GET", "POST"])
@login_required
def change_user_password(user_id):
    """change user password"""
    if not current_user.has_permission("admin"):
        abort(403)

    _user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # validate data
        if not ('password' in request.form
                and len(request.form['password'])
                and 'password2' in request.form
                and len(request.form['password2'])):
            flash("Something went wrong.", "danger")
            return redirect(url_for("admin.users", page=1))

        _password = str(request.form['password'])
        _password2 = str(request.form['password2'])

        if _password != _password2:
            flash("Entered Passwords do not match.", "danger")
            return redirect(url_for("admin.users", page=1))

        try:
            _user.change_password(clear_pw=_password)
            flash("Successfully changed password for: " + _user.username,
                  "success")
            return redirect(url_for("admin.users", page=1))
        except Exception as e:
            flash("Something went wrong.", "danger")
            return redirect(url_for("admin.users", page=1))

    return render_template("admin_change_user_pw.html", user=_user)


@appmodule.route("/user/<int:user_id>/delete")
@login_required
def delete_user(user_id):
    """delete user"""
    if not current_user.has_permission("admin"):
        abort(403)

    _user = User.query.get_or_404(user_id)
    _u_username = _user.username

    try:
        db.session.delete(_user)
        db.session.commit()
        flash("Deleted User (" + str(user_id) + "): " + _u_username, "success")
        return redirect("/admin/users/1")

    except:
        flash("Something went wrong.", "danger")
        return redirect(url_for("admin.users", page=1))

"""start"""


@appmodule.route('/user_groups/')
@login_required
def read_user_groups():
    return redirect(url_for("admin.read_user_groups_paged", page=1))


@appmodule.route('/user_groups/<int:page>')
@login_required
def read_user_groups_paged(page=1):
    """user_groups_paged view """

    print(request.endpoint)

    _query = UserGroup.query
    _items_per_page = app.config["ITEMS_PER_PAGE"]
    _items_paged = _query.paginate(page, _items_per_page)

    return render_template('admin_user_groups.html',
                           items_paged=_items_paged,
                           endpoint=request.endpoint)


@appmodule.route("/user_group/<int:user_group_id>/create")
@login_required
def create_user_group(user_group_id):
    pass


@appmodule.route("/user_group/<int:user_group_id>")
@appmodule.route("/user_group/<int:user_group_id>/read")
@login_required
def read_user_group(user_group_id):
    return redirect(url_for("admin.user_groups_paged", page=1))


@appmodule.route("/user_group/<int:user_group_id>/update", methods=['GET', 'POST'])
@login_required
def update_user_group(user_group_id):
    pass


@appmodule.route("/user_group/<int:user_group_id>/delete")
@login_required
def delete_user_group(user_group_id):
    pass


"""end"""

"""
@appmodule.route("/permissions")
@appmodule.route("/permissions/")
@login_required
def permissions_redirect():
    return redirect("/admin/permissions/1")


@appmodule.route("/permissions/<int:page>")
@login_required
def permissions(page=1):
    """ """ admin page - used to manage user accounts and permissions """ """
    if not current_user.has_permission("admin"):
        abort(403)
    _permissions = Permission.query.paginate(page, app.config["ITEMS_PER_PAGE"])
    _users = User.query.all()
    return render_template("admin_permissions.html",
                           permissions=_permissions,
                           users=_users)


@appmodule.route("/add_permission", methods=["GET", "POST"])
@login_required
def add_permission():
    """ """add permission """ """
    if not current_user.has_permission("admin"):
        abort(403)

    if request.method == 'POST':
        # validate data
        if 'name' in request.form and len(request.form['name']):
            # TODO is das hier fies?! hart nach str konvertieren?
            _name = str(request.form['name'])
            if 'comment' in request.form and len(request.form['comment']):
                _comment = str(request.form['comment'])
            else:
                _comment = None

            try:
                new_permission = Permission.add(name=_name,
                                                comment=_comment)

                flash("Successfully created " + _name + " with ID " +
                      str(new_permission.id), "success")
                return redirect("/admin/permissions/1")
            except Exception as e:
                flash("Something went wrong.", "danger")
                return redirect("/admin/permissions/1")

    else:
        return render_template("admin_add_permission.html")


@appmodule.route("/permission/<int:permission_id>/delete")
@login_required
def delete_permission(permission_id):
    """ """ delete permission """ """
    if not current_user.has_permission("admin"):
        abort(403)

    _permission = Permission.query.get_or_404(permission_id)
    _p_name = _permission.name
    if _permission.name == "admin" or _permission.id == 1:
        flash("Admin permission can not be deleted.", "warning")
        return redirect("/admin/permissions/1")

    try:
        db.session.delete(_permission)
        db.session.commit()
        flash("Deleted Permission (" + str(permission_id) + "): " + _p_name, "success")
        return redirect("/admin/permissions/1")

    except:
        flash("Something went wrong.", "danger")
        return redirect("/admin/permissions/1")

"""
