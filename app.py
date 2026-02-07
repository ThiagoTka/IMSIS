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
from sqlalchemy import text, inspect

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
    # Relacionamento com Cenario (opcional)
    cenario_id = db.Column(db.Integer, db.ForeignKey("cenarios.id"), nullable=True)
    cenario = db.relationship("Cenario", backref=db.backref("atividades", lazy=True))


class TesteTabela1(db.Model):
    __tablename__ = "teste_tabela_1"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)


class Cenario(db.Model):
    __tablename__ = "cenarios"

    id = db.Column(db.Integer, primary_key=True)
    cenario = db.Column(db.String(200), nullable=False)


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

        # Garantir que a coluna cenario_id exista em 'atividades' (adiciona se faltar)
        try:
            inspector = inspect(db.engine)
            if "atividades" in inspector.get_table_names():
                cols = [c["name"] for c in inspector.get_columns("atividades")]
                if "cenario_id" not in cols:
                    if db.engine.dialect.name == "sqlite":
                        db.session.execute(text("ALTER TABLE atividades ADD COLUMN cenario_id INTEGER"))
                    else:
                        db.session.execute(text("ALTER TABLE atividades ADD COLUMN cenario_id INTEGER REFERENCES cenarios(id)"))
                    db.session.commit()
        except Exception:
            # Se algo falhar aqui, ignoramos para não quebrar inicialização em ambientes restritos
            pass

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

        # Popular cenários iniciais
        if not Cenario.query.first():
            cenarios = [
                ("Cenário A",),
                ("Cenário B",),
                ("Cenário C",),
            ]
            for (nome,) in cenarios:
                db.session.add(Cenario(cenario=nome))
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
        return redirect(url_for("cenarios"))

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
        return redirect(url_for("cenarios"))

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


@app.route("/cenarios", methods=["GET", "POST"])
@login_required
def cenarios():
    if request.method == "POST":
        nome = request.form.get("cenario")
        if nome:
            db.session.add(Cenario(cenario=nome))
            db.session.commit()
            flash("Cenário criado com sucesso")
        return redirect(url_for("cenarios"))

    cenarios = Cenario.query.order_by(Cenario.id).all()
    return render_template("cenarios.html", cenarios=cenarios, usuario_atual=current_user.username)


@app.route("/cenarios/<int:cenario_id>/atividades", methods=["GET", "POST"])
@login_required
def atividades_por_cenario(cenario_id):
    cenario = Cenario.query.get_or_404(cenario_id)

    if request.method == "POST":
        try:
            numero = int(request.form.get("numero_sequencial") or 0)
        except ValueError:
            numero = 0
        descricao = request.form.get("descricao")
        responsavel = request.form.get("responsavel")

        if descricao and responsavel:
            nova = Atividade(
                numero_sequencial=numero,
                descricao=descricao,
                responsavel=responsavel,
                cenario_id=cenario_id,
            )
            db.session.add(nova)
            db.session.commit()

            # Se não houver nenhuma atividade liberada neste cenário, liberar a primeira (menor seq)
            any_liberada = (
                Atividade.query
                .filter_by(cenario_id=cenario_id)
                .filter(Atividade.data_liberacao != None)
                .first()
            )
            if not any_liberada:
                primeira = (
                    Atividade.query
                    .filter_by(cenario_id=cenario_id)
                    .order_by(Atividade.numero_sequencial)
                    .first()
                )
                if primeira and not primeira.data_liberacao:
                    primeira.data_liberacao = datetime.now()
                    db.session.commit()

            flash("Atividade criada com sucesso")

        return redirect(url_for("atividades_por_cenario", cenario_id=cenario_id))
    atividades = (
        Atividade.query.filter_by(cenario_id=cenario_id).order_by(Atividade.numero_sequencial).all()
    )
    usuarios = User.query.order_by(User.username).all()
    return render_template("atividades.html", cenario=cenario, atividades=atividades, usuario_atual=current_user.username, usuarios=usuarios)


@app.route("/atividades/<int:atividade_id>/delete", methods=["POST"])
@login_required
def delete_atividade(atividade_id):
    atv = Atividade.query.get_or_404(atividade_id)
    cenario_id = atv.cenario_id
    db.session.delete(atv)
    db.session.commit()
    flash("Atividade excluída")
    if cenario_id:
        return redirect(url_for("atividades_por_cenario", cenario_id=cenario_id))
    return redirect(url_for("index"))


@app.route("/atividades/<int:atividade_id>/liberar", methods=["POST"])
@login_required
def liberar_atividade(atividade_id):
    atv = Atividade.query.get_or_404(atividade_id)
    if not atv.data_liberacao:
        atv.data_liberacao = datetime.now()
        db.session.commit()
        flash("Atividade liberada")
    else:
        flash("Atividade já está liberada")
    if atv.cenario_id:
        return redirect(url_for("atividades_por_cenario", cenario_id=atv.cenario_id))
    return redirect(url_for("index"))


@app.route("/cenarios/<int:cenario_id>/delete", methods=["POST"])
@login_required
def delete_cenario(cenario_id):
    c = Cenario.query.get_or_404(cenario_id)
    # remover atividades vinculadas
    Atividade.query.filter_by(cenario_id=cenario_id).delete()
    db.session.delete(c)
    db.session.commit()
    flash("Cenário excluído")
    return redirect(url_for("cenarios"))


@app.route("/concluir/<int:atividade_id>", methods=["POST"])
@login_required
def concluir_atividade(atividade_id):
    atv = Atividade.query.get_or_404(atividade_id)
    # Segurança: apenas o responsável pode concluir
    if atv.responsavel != current_user.username:
        flash("Apenas o responsável pode concluir esta atividade")
        if atv.cenario_id:
            return redirect(url_for("atividades_por_cenario", cenario_id=atv.cenario_id))
        return redirect(url_for("index"))

    # Deve estar liberada
    if not atv.data_liberacao:
        flash("Atividade ainda não está liberada")
        if atv.cenario_id:
            return redirect(url_for("atividades_por_cenario", cenario_id=atv.cenario_id))
        return redirect(url_for("index"))

    atv.data_conclusao = datetime.now()
    db.session.commit()
    flash("Atividade concluída com sucesso")

    # Liberar automaticamente a próxima atividade (mesmo cenário, próximo número sequencial)
    if atv.cenario_id is not None:
        prox = (
            Atividade.query
            .filter(Atividade.cenario_id == atv.cenario_id)
            .filter(Atividade.numero_sequencial > atv.numero_sequencial)
            .order_by(Atividade.numero_sequencial)
            .first()
        )
        if prox and not prox.data_liberacao:
            prox.data_liberacao = datetime.now()
            db.session.commit()
            flash(f"Próxima atividade '{prox.descricao}' liberada")

        return redirect(url_for("atividades_por_cenario", cenario_id=atv.cenario_id))

    return redirect(url_for("index"))


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
