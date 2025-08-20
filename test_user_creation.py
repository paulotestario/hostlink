#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database
from werkzeug.security import generate_password_hash
import secrets

def test_user_creation():
    """Testa a criação de usuário por email"""
    print("🧪 Testando criação de usuário por email...")
    
    db = get_database()
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco")
        return False
    
    # Email de teste
    test_email = "teste_fix@exemplo.com"
    
    try:
        # Verificar se usuário já existe e remover
        existing = db.get_user_by_email(test_email)
        if existing:
            print(f"Removendo usuário existente: {test_email}")
            db.supabase.table('users').delete().eq('email', test_email).execute()
        
        # Criar hash da senha
        password_hash = generate_password_hash('senha123')
        token = secrets.token_urlsafe(32)
        
        # Tentar criar usuário
        user_id = db.create_email_user(test_email, 'Teste Fix', password_hash, token)
        
        if user_id:
            print(f"✅ Usuário criado com sucesso! ID: {user_id}")
            
            # Limpar teste
            db.supabase.table('users').delete().eq('email', test_email).execute()
            print("✅ Teste concluído com sucesso")
            return True
        else:
            print("❌ Falha ao criar usuário")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == '__main__':
    test_user_creation()