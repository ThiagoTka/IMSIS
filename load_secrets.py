"""
Script para carregar secrets do Google Secret Manager como variáveis de ambiente
Necessário porque Cloud Run com --set-secrets frequentemente nao funciona corretamente
"""

import os
import sys


def load_secret(secret_id):
    """Carrega um secret do Google Secret Manager API"""
    try:
        from google.cloud import secretmanager
        
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT", "imsis-486003")
        
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        print(f"[DEBUG load_secret] Tentando ler {secret_id} de {name}")
        response = client.access_secret_version(request={"name": name})
        secret_string = response.payload.data.decode("UTF-8")
        
        if secret_string:
            print(f"[OK] Secret '{secret_id}' carregado com sucesso ({len(secret_string)} chars)")
            return secret_string
        else:
            print(f"[WARN] Secret '{secret_id}' está vazio")
            return None
            
    except Exception as e:
        print(f"[WARN] Erro ao carregar secret {secret_id} da API: {type(e).__name__}: {e}")
        return None


def load_secrets():
    """Carrega todos os secrets necessários"""
    
    print("[DEBUG load_secrets] Iniciando carregamento de secrets")
    
    # Check 1: Se ao menos DB_PASS ja esta em os.environ LIMPO (sem BOM)
    # isso significa que o --set-secrets do Cloud Run funcionou
    # Mas os SMTP secrets nao estao, entao vamos carregar via API
    
    db_pass = os.environ.get("DB_PASS", "").strip()
    
    if db_pass and not db_pass.startswith("ï»¿"):  # Nao tem BOM
        print("[INFO] DB_PASS ja esta em os.environ (Cloud Run --set-secrets)")
        # Mas ainda tentar carregar SMTP secrets se nao estiverem setados
        if not os.environ.get("SMTP_HOST"):
            print("[WARN] SMTP_HOST nao encontrado em os.environ, tentando carregar da API...")
            load_secrets_from_api()
        return
    
    # Se DB_PASS tiver BOM ou estiver vazio, precisa recarregar TUDO da API
    if db_pass.startswith("ï»¿"):
        print("[WARN] DB_PASS tem BOM (corrupao), recarregando todos os secrets da API")
    else:
        print("[INFO] DB_PASS nao encontrado em os.environ, carregando da API")
    
    # Check 2: Se .env existe (desenvolvimento local)
    if os.path.exists(".env"):
        print("[INFO] Arquivo .env encontrado, carregando variaveis locais...")
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
        print("[OK] Variaveis carregadas do .env")
        return
    
    # Check 3: Carregar todos os secrets da API (Cloud Run production)
    print("[INFO] Carregando secrets do Google Secret Manager API...")
    load_secrets_from_api()


def load_secrets_from_api():
    """Carrega todos os secrets diretamente da Google Secret Manager API"""
    
    secrets_to_load = {
        "DB_PASS": "db-pass",
        "SECRET_KEY": "secret-key",
        "SMTP_HOST": "smtp-host",
        "SMTP_PORT": "smtp-port",
        "SMTP_USER": "smtp-user",
        "SMTP_PASS": "smtp-pass",
        "SMTP_FROM": "smtp-from",
    }
    
    loaded_count = 0
    for env_var, secret_id in secrets_to_load.items():
        if os.environ.get(env_var) and not os.environ.get(env_var).startswith("ï»¿"):
            print(f"[DEBUG] {env_var} ja esta em os.environ (saltando)")
            loaded_count += 1
            continue
        
        secret_value = load_secret(secret_id)
        if secret_value:
            secret_value = secret_value.strip()  # Remove whitespace/BOM
            os.environ[env_var] = secret_value
            print(f"[OK] {env_var} atribuido de {secret_id}")
            loaded_count += 1
        else:
            print(f"[ERROR] Falha ao carregar {env_var} de {secret_id}")
    
    if loaded_count == len(secrets_to_load):
        print(f"[OK] Todos os {loaded_count} secrets carregados com sucesso da API")
    else:
        print(f"[WARN] Apenas {loaded_count}/{len(secrets_to_load)} secrets carregados da API")
        print(f"[ERROR] Faltam {len(secrets_to_load) - loaded_count} secrets!")


if __name__ == "__main__":
    load_secrets()

