import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-dev'

# --- CORREÇÃO 1: Banco de dados na pasta temporária (/tmp) ---
# O Cloud Run só permite escrita na pasta /tmp.
# Se estiver no Cloud Run (variável K_SERVICE existe), usa /tmp. Se for local, usa pasta atual.
if os.environ.get('K_SERVICE'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/tarefas.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tarefas.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelo de Dados ---
class Atividade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_sequencial = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    data_liberacao = db.Column(db.DateTime, nullable=True)
    data_conclusao = db.Column(db.DateTime, nullable=True)

# --- Função de Inicialização ---
def criar_tabelas_e_dados():
    # Cria as tabelas se não existirem
    db.create_all()
    
    # Cria dados fictícios apenas se o banco estiver vazio
    if not Atividade.query.first():
        dados = [
            (1, "Levantamento de Requisitos", "Alice", True),
            (2, "Desenvolvimento Backend", "Bob", False),
            (3, "Desenvolvimento Frontend", "Carlos", False),
            (4, "Deploy em Produção", "Alice", False)
        ]
        for seq, desc, resp, liberado in dados:
            nova = Atividade(
                numero_sequencial=seq,
                descricao=desc,
                responsavel=resp,
                data_liberacao=datetime.now() if liberado else None
            )
            db.session.add(nova)
        db.session.commit()

# --- CORREÇÃO 2: Executar a criação fora do __main__ ---
# Isso garante que o Gunicorn execute isso ao iniciar o container
with app.app_context():
    criar_tabelas_e_dados()

# --- Rotas ---
@app.route('/')
def index():
    usuario_atual = request.args.get('user', 'Alice')
    atividades = Atividade.query.order_by(Atividade.numero_sequencial).all()
    return render_template('index.html', atividades=atividades, usuario_atual=usuario_atual)

@app.route('/concluir/<int:id>', methods=['POST'])
def concluir_atividade(id):
    usuario_atual = request.form.get('usuario_atual')
    atividade = Atividade.query.get_or_404(id)

    if atividade.responsavel != usuario_atual:
        flash(f'Erro: Apenas {atividade.responsavel} pode concluir esta tarefa.')
        return redirect(url_for('index', user=usuario_atual))

    if not atividade.data_liberacao:
        flash('Erro: Esta atividade ainda não foi liberada pela anterior.')
        return redirect(url_for('index', user=usuario_atual))

    atividade.data_conclusao = datetime.now()
    
    proxima = Atividade.query.filter_by(numero_sequencial=atividade.numero_sequencial + 1).first()
    if proxima:
        proxima.data_liberacao = datetime.now()
    
    db.session.commit()
    return redirect(url_for('index', user=usuario_atual))

@app.route('/reset')
def reset():
    db.drop_all()
    criar_tabelas_e_dados()
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)