import os
from datetime import datetime
from urllib.parse import quote_plus

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

# ------------------------------------------------------------------------------
# APP
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chave-secreta-dev")

# DATABASE CONFIG
if os.environ.get("DATABASE_URL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
elif (
    os.environ.get("DB_USER")
    and os.environ.get("DB_PASS")
    and os.environ.get("DB_NAME")
    and os.environ.get("CLOUD_SQL_CONNECTION_NAME")
):
    db_user = os.environ.get("DB_USER")
    db_pass = quote_plus(os.environ.get("DB_PASS"))  # URL-encode the password
    db_name = os.environ.get("DB_NAME")
    cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{cloud_sql_connection_name}"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ------------------------------------------------------------------------------
# EXTENSIONS
# ------------------------------------------------------------------------------
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ------------------------------------------------------------------------------
# MODELS
# ------------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Atividade(db.Model):
    __tablename__ = "atividades"

    id = db.Column(db.Integer, primary_key=True)
    numero_sequencial = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    data_liberacao = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime)


class TesteTabela1(db.Model):
    __tablename__ = "teste_tabela_1"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)


# ------------------------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------------------------------------------------------------------
# DB INIT
# ------------------------------------------------------------------------------
def criar_tabelas_e_dados():
    try:
        db.create_all()

        if not User.query.first():
            usuarios = [
                ("Alice", "alice@example.com"),
                ("Bob", "bob@example.com"),
                ("Carlos", "carlos@example.com"),
            ]

            for nome, email in usuarios:
                db.session.add(
                    User(
                        username=nome,
                        email=email,
                        password=generate_password_hash("123"),
                    )
                )

            db.session.commit()

        if not Atividade.query.first():
            atividades = [
                (1, "Levantamento de Requisitos", "Alice", True),
                (2, "Desenvolvimento Backend", "Bob", False),
                (3, "Desenvolvimento Frontend", "Carlos", False),
                (4, "Deploy em Produção", "Alice", False),
            ]

            for seq, desc, resp, liberado in atividades:
                db.session.add(
                    Atividade(
                        numero_sequencial=seq,
                        descricao=desc,
                        responsavel=resp,
                        data_liberacao=datetime.now() if liberado else None,
                    )
                )

            db.session.commit()

    except Exception as e:
        print("ERRO AO INICIALIZAR DB:", e)


# 🔥 Executa sempre que o container sobe
with app.app_context():
    criar_tabelas_e_dados()


# ------------------------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------------------------

@app.route("/db-check")
def db_check():
    result = db.session.execute(text("SELECT current_database(), current_user"))
    row = result.fetchone()
    return f"DB={row[0]} | USER={row[1]}"


@app.route("/where-db")
def where_db():
    return app.config["SQLALCHEMY_DATABASE_URI"]

@app.route("/test-db")
def test_db():
    try:
        registro = TesteTabela1(nome="Cloud Run OK")
        db.session.add(registro)
        db.session.commit()
        return "INSERT OK - gravou no Cloud SQL"
    except Exception as e:
        return f"ERRO DB: {e}", 500


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("E-mail já cadastrado")
            return redirect(url_for("register"))

        user = User(
            username=email.split("@")[0],
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Usuário ou senha inválidos")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    atividades = Atividade.query.order_by(Atividade.numero_sequencial).all()
    return render_template(
        "index.html",
        atividades=atividades,
        usuario_atual=current_user.username,
    )


@app.route("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return "OK"


# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
