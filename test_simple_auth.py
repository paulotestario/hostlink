#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples da funcionalidade de autenticação por email
"""

import sys
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import HostLinkDatabase
from auth import User

def test_basic_functionality():
    """Testa funcionalidades básicas sem depender da estrutura do banco"""
    print("=== Teste de Funcionalidades Básicas ===")
    
    # Teste 1: Conexão com banco
    try:
        db = HostLinkDatabase()
        if db.test_connection():
            print("✅ Conexão com banco de dados: OK")
        else:
            print("❌ Conexão com banco de dados: FALHA")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
    
    # Teste 2: Hash de senha
    try:
        password = "senha123"
        hashed = generate_password_hash(password)
        if check_password_hash(hashed, password):
            print("✅ Hash de senha: OK")
        else:
            print("❌ Hash de senha: FALHA")
            return False
    except Exception as e:
        print(f"❌ Erro no hash: {e}")
        return False
    
    # Teste 3: Geração de token
    try:
        token = secrets.token_urlsafe(32)
        if len(token) > 20:
            print("✅ Geração de token: OK")
        else:
            print("❌ Geração de token: FALHA")
            return False
    except Exception as e:
        print(f"❌ Erro no token: {e}")
        return False
    
    # Teste 4: Verificar estrutura da tabela users
    try:
        result = db.supabase.table('users').select('*').limit(1).execute()
        print("✅ Acesso à tabela users: OK")
        
        if result.data:
            user_columns = list(result.data[0].keys())
            print(f"📋 Colunas disponíveis: {user_columns}")
            
            required_columns = ['email', 'name']
            missing_columns = [col for col in required_columns if col not in user_columns]
            
            if missing_columns:
                print(f"⚠ Colunas obrigatórias faltando: {missing_columns}")
            else:
                print("✅ Colunas básicas presentes")
        else:
            print("📋 Tabela users está vazia")
            
    except Exception as e:
        print(f"❌ Erro ao acessar tabela users: {e}")
        return False
    
    return True

def test_user_creation_simple():
    """Testa criação de usuário usando apenas colunas existentes"""
    print("\n=== Teste de Criação de Usuário Simples ===")
    
    try:
        db = HostLinkDatabase()
        
        # Tentar criar usuário apenas com campos básicos
        test_email = "teste_simples@exemplo.com"
        
        # Verificar se usuário já existe
        existing = db.get_user_by_email(test_email)
        if existing:
            print(f"Usuário {test_email} já existe, removendo...")
            db.supabase.table('users').delete().eq('email', test_email).execute()
        
        # Criar usuário básico
        user_data = {
            'email': test_email,
            'name': 'Usuário Teste Simples'
        }
        
        result = db.supabase.table('users').insert(user_data).execute()
        
        if result.data:
            user_id = result.data[0]['id']
            print(f"✅ Usuário criado com ID: {user_id}")
            
            # Verificar se consegue recuperar
            retrieved = db.get_user_by_email(test_email)
            if retrieved:
                print("✅ Usuário recuperado com sucesso")
                
                # Limpar
                db.supabase.table('users').delete().eq('email', test_email).execute()
                print("✅ Usuário de teste removido")
                return True
            else:
                print("❌ Falha ao recuperar usuário")
                return False
        else:
            print("❌ Falha ao criar usuário")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    print("🚀 Iniciando testes de autenticação...\n")
    
    # Teste básico
    if not test_basic_functionality():
        print("\n❌ Testes básicos falharam. Parando.")
        return
    
    # Teste de criação simples
    if test_user_creation_simple():
        print("\n✅ Todos os testes passaram!")
        print("\n📝 Próximos passos:")
        print("1. As funcionalidades básicas estão funcionando")
        print("2. A estrutura do banco precisa ser atualizada manualmente")
        print("3. Após atualização, a autenticação por email estará pronta")
    else:
        print("\n❌ Alguns testes falharam")

if __name__ == "__main__":
    main()