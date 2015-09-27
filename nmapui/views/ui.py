from nmapui import login_manager, login_serializer, app
from nmapui.models import Users
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, login_required
from itsdangerous import BadSignature
import bcrypt

appmodule = Blueprint('ui', __name__)

@appmodule.route('/', methods=['GET'])
def index():
    return redirect(url_for('ui.login'))


@login_manager.token_loader
def load_token(token):
    """
    Flask-Login token_loader callback.
    The token_loader function asks this function to take the token that was
    stored on the users computer process it to check if its valid and then
    return a User Object if its valid or None if its not valid.
    """

    #The Token itself was generated by User.get_auth_token.  So it is up to
    #us to known the format of the token data itself.

    #The Token was encrypted using itsdangerous.URLSafeTimedSerializer which
    #allows us to have a max_age on the token itself.  When the cookie is stored
    #on the users computer it also has a exipry date, but could be changed by
    #the user, so this feature allows us to enforce the exipry date of the token
    #server side and not rely on the users cookie to exipre.
    max_age = app.config["REMEMBER_COOKIE_DURATION"].total_seconds()

    #Decrypt the Security Token, data = [username, hashpass]
    try:
        data = login_serializer.loads(token, max_age=max_age)
        # This payload is decoded and safe
    except BadSignature, e:
        print("Cookie has been tampered: " + str(e))
        return None

    #Find the User
    user = Users.get(data[0])

    #Check Password and return user or None
    if user and data[1] == user.password:
        return user
    return None

@login_manager.user_loader
def load_user(user_id):
    return Users.get(user_id)

@appmodule.route("/login", methods=["GET", "POST"])
def login():
    if (request.method == 'POST' and 'username' in request.form and
       'password' in request.form):
        app_user = None
        username = request.form['username']
        password = request.form['password']
        if 'username' in request.form and len(request.form['username']):
            app_users = Users.find(username=username)

            if len(app_users) != 1:
                # this should make time based user enumeration difficult
                bcrypt.hashpw("faked calculation", bcrypt.gensalt())
                flash("Login failed: Check Username and Password", "danger")
                return render_template("login.html")
            else:
                app_user = app_users[0]

        if app_user and app_user.credentials_valid(password):
            if request.form.getlist("remember-me"):
                login_user(app_user, remember=True)
            else:
                login_user(app_user)
            return redirect(url_for("nmap.nmap_index"))
        else:
            flash("Login failed: Check Username and Password", "danger")

    return render_template("login.html")


@appmodule.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@appmodule.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('ui.index'))
