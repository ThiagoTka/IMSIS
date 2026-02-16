#!/usr/bin/env python3
"""
Script para forçar migração de colunas no banco de dados em produção
Execute isto se receber erros de colunas ausentes
"""

import os
import sys
from app import app, db
from sqlalchemy import text, inspect

def migrate_columns():
    """Força a criação de todas as colunas necessárias"""
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        if "users" not in inspector.get_table_names():
            print("[ERROR] Tabela 'users' nao existe!")
            return False
        
        colunas_existentes = [c["name"] for c in inspector.get_columns("users")]
        print(f"[INFO] Colunas existentes em 'users': {colunas_existentes}")
        
        migrations = [
            ("email_verified", "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT false", "ALTER TABLE users ADD COLUMN email_verified SMALLINT DEFAULT 0"),
            ("email_verification_token_hash", "ALTER TABLE users ADD COLUMN email_verification_token_hash TEXT", "ALTER TABLE users ADD COLUMN email_verification_token_hash VARCHAR(255)"),
            ("email_verification_expires_at", "ALTER TABLE users ADD COLUMN email_verification_expires_at TIMESTAMP", "ALTER TABLE users ADD COLUMN email_verification_expires_at TIMESTAMP"),
            ("password_reset_token_hash", "ALTER TABLE users ADD COLUMN password_reset_token_hash TEXT", "ALTER TABLE users ADD COLUMN password_reset_token_hash VARCHAR(255)"),
            ("password_reset_expires_at", "ALTER TABLE users ADD COLUMN password_reset_expires_at TIMESTAMP", "ALTER TABLE users ADD COLUMN password_reset_expires_at TIMESTAMP"),
        ]
        
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "").lower()
        is_postgres = "postgresql" in db_uri
        
        for coluna, sql_sqlite, sql_pg in migrations:
            if coluna in colunas_existentes:
                print(f"[OK] Coluna {coluna} ja existe")
                continue
            
            sql = sql_pg if is_postgres else sql_sqlite
            print(f"[INFO] Tentando criar coluna {coluna}...")
            print(f"       SQL: {sql}")
            
            try:
                db.session.execute(text(sql))
                db.session.commit()
                print(f"[OK] Coluna {coluna} criada com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Falha ao criar {coluna}: {e}")
        
        # Marcar usuarios existentes como verificados
        try:
            db.session.execute(text("UPDATE users SET email_verified = true WHERE email_verified IS NULL OR email_verified = false"))
            db.session.commit()
            print("[OK] Usuarios existentes marcados como verificados")
        except Exception as e:
            db.session.rollback()
            print(f"[WARN] Erro ao atualizar email_verified: {e}")
        
        print("\n[OK] Migracao concluida!")
        return True

if __name__ == "__main__":
    migrate_columns()
