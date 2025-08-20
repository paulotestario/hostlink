#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar a estrutura da tabela users no banco de dados
"""

import os
from database import HostLinkDatabase

def update_users_table():
    """Atualiza a tabela users com as novas colunas para autenticação por email"""
    try:
        db = HostLinkDatabase()
        
        print("Conectando ao banco de dados...")
        
        # Verificar se as colunas já existem
        try:
            # Tentar fazer uma consulta que usa as novas colunas
            result = db.supabase.table('users').select('password_hash').limit(1).execute()
            print("As colunas já existem na tabela users.")
            return True
        except Exception:
            print("Colunas não existem, criando...")
        
        # Executar as alterações usando RPC ou diretamente via SQL
        sql_commands = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_type VARCHAR(20) DEFAULT 'google';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();",
            "ALTER TABLE users ALTER COLUMN google_id DROP NOT NULL;"
        ]
        
        # Executar cada comando
        for sql in sql_commands:
            try:
                print(f"Executando: {sql}")
                # Usar rpc para executar SQL customizado
                result = db.supabase.rpc('exec_sql', {'sql_query': sql}).execute()
                print(f"✓ Comando executado com sucesso")
            except Exception as e:
                print(f"⚠ Erro ao executar comando (pode ser normal se coluna já existe): {e}")
                continue
        
        print("\n✅ Atualização da tabela users concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar tabela: {e}")
        return False

def test_new_columns():
    """Testa se as novas colunas estão funcionando"""
    try:
        db = HostLinkDatabase()
        
        # Tentar inserir um usuário de teste
        test_email = "teste@exemplo.com"
        
        # Verificar se usuário já existe
        existing = db.get_user_by_email(test_email)
        if existing:
            print(f"Usuário de teste {test_email} já existe.")
            return True
        
        # Criar usuário de teste
        print("Testando criação de usuário por email...")
        user_id = db.create_email_user(
            email=test_email,
            name="Usuário Teste",
            password_hash="hash_teste_123",
            verification_token="token_teste_123"
        )
        
        if user_id:
            print(f"✅ Usuário de teste criado com ID: {user_id}")
            
            # Limpar usuário de teste
            db.supabase.table('users').delete().eq('email', test_email).execute()
            print("✅ Usuário de teste removido")
            return True
        else:
            print("❌ Falha ao criar usuário de teste")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("=== Atualizando Estrutura do Banco de Dados ===")
    print()
    
    # Atualizar tabela
    if update_users_table():
        print()
        print("=== Testando Novas Funcionalidades ===")
        test_new_columns()
    
    print()
    print("=== Processo Concluído ===")