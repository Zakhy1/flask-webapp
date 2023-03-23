import os
import sqlite3

from FDataBase import FDataBase
from UserLogin import UserLogin
from forms import LoginForm

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, g, request, flash, abort, session, url_for, redirect, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

# Конфиги

DATABASE = "/tmp/flsite.db"
DEBUG = True

app = Flask(__name__)
app.config["SECRET_KEY"] = "78556c5e5fcd987f568843e2dce083efb173662c"
MAX_CONTENT_LENGTH = 1024 * 1024

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    print("Load user")
    return UserLogin().fromDB(user_id, dbase)


def connect_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource("sq_db.sql", mode="r") as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    if not hasattr(g, "link_db"):
        g.link_db = connect_db()
    return g.link_db


dbase = None


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "link_db"):
        g.link_db.close()


@app.route("/")
def index():
    return render_template("index.html", menu=dbase.getMenu(), posts=dbase.getPostsAnonce())


@app.route("/add_post", methods=["POST", "GET"])
def add_post():
    if request.method == "POST":
        if len(request.form["name"]) > 4 and len(request.form["text"]) > 10:
            res = dbase.addPost(request.form["name"], request.form["text"], request.form["url"])
            if not res:
                flash("Ошибка добавления статьи", category="error")
            else:
                flash("Статья добавлена успешно", category="success")
        else:
            flash("Ошибка добавления статьи", category="error")

    return render_template("add_post.html", menu=dbase.getMenu(), title="Добавление статьи")


@app.route("/posts/<alias>")
@login_required
def show_post(alias):
    session.permanent = True
    if "visits" in session:
        session["visits"] = session.get("visits") + 1
    else:
        session["visits"] = 1

    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template("post.html", menu=dbase.getMenu(), title=title, post=post)


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user["password"], form.password.data):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get("remainme") else False
            login_user(userlogin, remember=rm)
            return redirect(url_for("index"))
        flash("Неверная пара логин/пароль", "error")

    return render_template("login.html", menu=dbase.getMenu(), title="Авторизация", form=form)

    # if request.method == "POST":
    #     user = dbase.getUserByEmail(request.form["email"])
    #     if user and check_password_hash(user["password"], request.form["password"]):
    #         userlogin = UserLogin().create(user)
    #         rm = True if request.form.get("remainme") else False
    #         login_user(userlogin, remember=rm)
    #         return redirect(url_for("index"))
    #     flash("Неверная пара логин/пароль", "error")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        if len(request.form["name"]) > 4 and len(request.form["email"]) > 4 \
                and len(request.form["password"]) > 4 and request.form["password"] == request.form["password-repeat"]:
            hash = generate_password_hash(request.form["password"])
            res = dbase.addUser(request.form["name"], request.form["email"], hash)
            if res:
                flash("Вы успешно зарегистрированы", "success")
                return redirect(url_for("login"))
            else:
                flash("Произошла ошибка", "error")
                print("Ошибка при регистрации")
        else:
            flash("Неверно заполнены поля")

    return render_template("register.html", menu=dbase.getMenu(), title="Регистрация")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(request.args.get("next") or url_for("profile"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", menu=dbase.getMenu(), title="Профиль")


@app.route("/userava")
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    res = make_response(img)
    res.headers["Content-Type"] = "image/png"
    return res


@app.route("/upload", methods=["POST", "GET"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                    return redirect(url_for("profile"))
                flash("Аватар обновлен", "success")
            except FileNotFoundError:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True)
