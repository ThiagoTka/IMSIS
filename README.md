# IMSIS - Sistema de Gestão de Projetos

Sistema web para gerenciamento de projetos, com suporte a cenários de teste, lições aprendidas, solicitações de mudança, gestão de incidentes e riscos.

## 📚 Documentação

- 🚀 **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Checklist rápido para deploy
- 📊 **[GCP_READINESS_REPORT.md](GCP_READINESS_REPORT.md)** - Relatório completo de prontidão
- ⚙️ **[GCP_SETUP.md](GCP_SETUP.md)** - Guia detalhado de configuração do GCP
- 🔐 **[SECURITY.md](SECURITY.md)** - Diretrizes de segurança

## 🚀 Deploy Rápido no GCP

### Pré-requisitos
1. Configurar secrets (ver [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md))
2. Criar Cloud SQL instance
3. Configurar permissões IAM

### Deploy
```bash
# 1. Configurar secrets
bash setup_gcp_secrets.sh

# 2. Push para GitHub (ou deploy manual)
git push origin main
```

Veja o guia completo em [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)

## Deployment no GCP

### Deploy automático via GitHub → GCP

1. **Push para GitHub** dispara automaticamente Cloud Build
2. **Cloud Build** executa `cloudbuild.yaml`:
   - Faz build da Docker image
   - Envia para Container Registry
   - Deploy no Cloud Run

### Inicialização automática do banco de dados

⚠️ **Importante**: As tabelas do banco de dados são criadas **automaticamente** quando a aplicação inicia.

Isso acontece em `app.py` com:
```python
with app.app_context():
    criar_tabelas()  # Executa db.create_all()
```

**Vantagens**:
- ✅ Funciona em qualquer ambiente (local, GCP, etc)
- ✅ Idempotente (seguro rodar múltiplas vezes)
- ✅ Não requer passos manuais
- ✅ Detecta automaticamente quando novas tabelas/colunas são necessárias

### Conexão com Cloud SQL

Configure as variáveis de ambiente:
- `DB_USER`: Usuário do PostgreSQL
- `DB_PASS`: Senha do PostgreSQL
- `DB_NAME`: Nome do banco de dados
- `CLOUD_SQL_CONNECTION_NAME`: `projeto:regiao:instancia`

Exemplo em `cloudbuild.yaml`:
```yaml
- --set-env-vars=CLOUD_SQL_CONNECTION_NAME=imsis-486003:us-central1:imsis-db
```

## Desenvolvimento Local

```bash
# Criar venv
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar
python app.py
```

Database local: `sqlite:///dev.db`

## Estrutura do Projeto

```
app.py                  # Aplicação principal (models + rotas)
templates/              # Templates HTML (Jinja2)
static/                 # CSS e JavaScript
cloudbuild.yaml         # Configuração do CI/CD (GCP)
Dockerfile              # Container image
requirements.txt        # Dependências Python
```

## Modelos de Dados

- **User**: Usuários do sistema
- **Projeto**: Projetos principais
- **ProjetoMembro**: Associação entre usuários e projetos
- **Perfil**: Perfis de acesso (permissões por projeto)
- **Fase/Cenario/Atividade**: Estrutura de testes
- **LicaoAprendida**: Registro de lições do projeto
- **SolicitacaoMudanca**: Solicitações de mudança

## Permissões por Perfil

Cada perfil pode ter permissões customizadas para:
- Atividades (criar, editar, excluir, concluir)
- Lições Aprendidas (criar, editar, excluir)
- Solicitações de Mudança (criar, editar, excluir)
- Gerenciar membros e perfis do projeto

---

## Deployment Manual (se necessário)

```bash
# Deploy direto no Cloud Run
gcloud run deploy imsis --source .
```

Cores do tema (CSS):
- Primary: #1F4E79 (azul)
- Success: #16A34A (verde)
- Warning: #F59E0B (amarelo)
- Danger: #DC2626 (vermelho)
