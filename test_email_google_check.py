#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da funcionalidade de verificação de email já usado com Google
"""

from database import get_database
from auth import User
import secrets
from werkzeug.security import generate_password_hash

def test_email_google_check():
    """
    Testa a verificação de email já usado com autenticação Google
    """
    print("🧪 Testando verificação de email já usado com Google...")
    
    db = get_database()
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return
    
    # Email de teste
    test_email = "teste.google@example.com"
    
    print(f"\n1. Verificando email '{test_email}' (deve retornar None se não existir)")
    auth_type = db.check_email_auth_type(test_email)
    print(f"   Resultado: {auth_type}")
    
    # Simular criação de usuário Google (apenas para teste)
    print(f"\n2. Simulando usuário Google existente...")
    try:
        # Criar usuário com Google ID (simulando login Google)
        google_user_id = db.save_user(
            google_id="123456789",
            email=test_email,
            name="Usuário Teste Google",
            profile_pic=""
        )
        
        if google_user_id:
            print(f"   ✅ Usuário Google criado com ID: {google_user_id}")
            
            # Verificar tipo de autenticação
            auth_type = db.check_email_auth_type(test_email)
            print(f"   Tipo de autenticação detectado: {auth_type}")
            
            if auth_type == 'google':
                print("   ✅ Verificação funcionando: Email detectado como Google")
            else:
                print(f"   ❌ Erro: Esperado 'google', obtido '{auth_type}'")
        else:
            print("   ❌ Erro ao criar usuário Google")
            
    except Exception as e:
        print(f"   ❌ Erro ao testar usuário Google: {e}")
    
    # Testar email não existente
    print(f"\n3. Testando email não existente...")
    non_existent_email = "naoexiste@example.com"
    auth_type = db.check_email_auth_type(non_existent_email)
    print(f"   Email '{non_existent_email}' - Tipo: {auth_type}")
    
    if auth_type is None:
        print("   ✅ Verificação funcionando: Email não encontrado")
    else:
        print(f"   ❌ Erro: Esperado None, obtido '{auth_type}'")
    
    # Testar email com autenticação por senha
    print(f"\n4. Testando email com autenticação por senha...")
    email_auth_email = "teste.email@example.com"
    
    try:
        # Criar usuário com autenticação por email
        password_hash = generate_password_hash("senha123")
        verification_token = secrets.token_urlsafe(32)
        
        email_user_id = db.create_email_user(
            email=email_auth_email,
            name="Usuário Teste Email",
            password_hash=password_hash,
            verification_token=verification_token
        )
        
        if email_user_id:
            print(f"   ✅ Usuário email criado com ID: {email_user_id}")
            
            # Verificar tipo de autenticação
            auth_type = db.check_email_auth_type(email_auth_email)
            print(f"   Tipo de autenticação detectado: {auth_type}")
            
            if auth_type == 'email':
                print("   ✅ Verificação funcionando: Email detectado como autenticação por senha")
            else:
                print(f"   ❌ Erro: Esperado 'email', obtido '{auth_type}'")
        else:
            print("   ❌ Erro ao criar usuário com autenticação por email")
            
    except Exception as e:
        print(f"   ❌ Erro ao testar usuário email: {e}")
    
    print("\n🎯 Cenários de uso:")
    print("   - Se usuário tentar registrar com email já usado no Google: Aviso para usar Google")
    print("   - Se usuário tentar login por email/senha com email do Google: Aviso para usar Google")
    print("   - Se usuário tentar registrar com email já usado por senha: Aviso de email já cadastrado")
    print("   - Se usuário tentar login com email não existente: Aviso de email não encontrado")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    test_email_google_check()