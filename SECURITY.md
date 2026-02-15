# 🔐 Diretrizes de Segurança - IMSIS

## ⚠️ IMPORTANTE: Antes do Deploy no GCP

### 1. Verificação de Secrets

**NUNCA** faça commit de:
- Senhas do banco de dados
- Chaves secretas da aplicação
- Tokens de API
- Credenciais de serviços

### 2. Arquivos que NÃO devem estar no Git

✅ Verifique se estes arquivos estão no `.gitignore`:
- `.env` - Variáveis de ambiente locais
- `*.db` - Bancos de dados SQLite
- `instance/` - Diretório de instância do Flask
- `cloud_sql_proxy` - Binário do proxy do Cloud SQL
- `__pycache__/` - Cache do Python

### 3. Configuração de Secrets no GCP

Use **Google Cloud Secret Manager** para armazenar credenciais:

```bash
# Nunca faça isso com senhas reais expostas!
# Use o arquivo .env local e o script setup_gcp_secrets.sh

# 1. Crie um arquivo .env LOCAL (não commitado)
echo "DB_PASS=sua_senha_forte_aqui" >> .env
echo "SECRET_KEY=sua_chave_secreta_aqui" >> .env

# 2. Execute o script de configuração
bash setup_gcp_secrets.sh
```

### 4. Permissões IAM Necessárias

Certifique-se de que a service account do Cloud Run tem:
- `roles/secretmanager.secretAccessor` - Para acessar secrets
- `roles/cloudsql.client` - Para conectar ao Cloud SQL

### 5. Checklist Antes do Deploy

- [ ] Arquivo `.env` NÃO está no git
- [ ] Secrets configurados no GCP Secret Manager
- [ ] Variáveis de ambiente configuradas no `cloudbuild.yaml`
- [ ] Permissões IAM configuradas
- [ ] Cloud SQL instance criada e configurada
- [ ] Firewall rules configuradas (se necessário)

### 6. Rotação de Secrets

Recomendação: Altere senhas periodicamente

```bash
# Atualizar secret no GCP
echo -n "nova_senha_forte" | gcloud secrets versions add db-pass --data-file=-

# Reinicie o serviço Cloud Run
gcloud run services update imsis --region us-central1
```

### 7. Auditoria de Segurança

Periodicamente execute:

```bash
# Verificar se há arquivos sensíveis no repositório
git log --all --full-history -- .env

# Se encontrar, remova do histórico!
# git filter-branch --force --index-filter \
#   'git rm --cached --ignore-unmatch .env' \
#   --prune-empty --tag-name-filter cat -- --all
```

## 🚨 Em Caso de Vazamento de Credenciais

1. **Imediatamente** altere todas as senhas comprometidas
2. Revogue as credenciais antigas no GCP
3. Atualize os secrets no Secret Manager
4. Force reinicialização do Cloud Run
5. Audite logs de acesso

## 📞 Contatos de Emergência

- Administrador GCP: [adicionar contato]
- Equipe de Segurança: [adicionar contato]

---

**Última atualização**: 15 de fevereiro de 2026
