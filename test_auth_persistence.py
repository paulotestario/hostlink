#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Autenticação e Persistência
Verifica se o user_db_id está sendo definido corretamente na sessão
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database
from auth import User

def test_user_creation():
    """
    Testa a criação de usuário e verificação do user_db_id
    """
    print("🧪 TESTE: Criação de Usuário e Persistência")
    print("=" * 50)
    
    # Conectar ao banco
    print("🔍 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    # Dados de teste do usuário
    test_google_id = "test_user_123456789"
    test_email = "teste@hostlink.com"
    test_name = "Usuário de Teste"
    test_profile_pic = "https://example.com/profile.jpg"
    
    print(f"📝 Dados de teste:")
    print(f"   Google ID: {test_google_id}")
    print(f"   Email: {test_email}")
    print(f"   Nome: {test_name}")
    
    try:
        # Limpar usuário de teste se existir
        print("\n🧹 Limpando dados de teste anteriores...")
        existing_user = db.get_user_by_google_id(test_google_id)
        if existing_user:
            print(f"   Usuário existente encontrado com ID: {existing_user['id']}")
        
        # Testar save_user diretamente
        print("\n🚀 Testando save_user diretamente...")
        user_db_id = db.save_user(test_google_id, test_email, test_name, test_profile_pic)
        
        if user_db_id:
            print(f"✅ SUCESSO! Usuário salvo com ID: {user_db_id}")
            
            # Verificar se foi realmente salvo
            print("\n🔍 Verificando se foi salvo corretamente...")
            saved_user = db.get_user_by_google_id(test_google_id)
            
            if saved_user:
                print("✅ Usuário encontrado na base de dados:")
                print(f"   ID: {saved_user['id']}")
                print(f"   Google ID: {saved_user['google_id']}")
                print(f"   Email: {saved_user['email']}")
                print(f"   Nome: {saved_user['name']}")
                print(f"   Criado em: {saved_user.get('created_at', 'N/A')}")
                
                # Testar criação via User.create
                print("\n🧪 Testando User.create...")
                
                # Simular sessão vazia
                from flask import Flask
                app = Flask(__name__)
                app.secret_key = 'test_key'
                
                with app.test_request_context():
                    from flask import session
                    session.clear()
                    
                    # Criar usuário
                    user = User.create(test_google_id, test_name, test_email, test_profile_pic)
                    
                    if user:
                        print(f"✅ User.create executado com sucesso")
                        print(f"   user_db_id na sessão: {session.get('user_db_id', 'NÃO DEFINIDO')}")
                        
                        if 'user_db_id' in session:
                            print("✅ user_db_id definido corretamente na sessão!")
                            return True
                        else:
                            print("❌ user_db_id NÃO foi definido na sessão")
                            return False
                    else:
                        print("❌ Erro ao criar usuário via User.create")
                        return False
            else:
                print("❌ Usuário não encontrado após salvamento")
                return False
        else:
            print("❌ Erro: save_user retornou None")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Limpar dados de teste
        print("\n🧹 Limpando dados de teste...")
        try:
            # Note: Em produção, você pode querer manter os dados de teste
            # ou usar uma base de dados separada para testes
            pass
        except Exception as e:
            print(f"⚠️ Erro ao limpar dados de teste: {e}")

def main():
    """
    Função principal do teste
    """
    print("🏁 Iniciando testes de autenticação e persistência...\n")
    
    success = test_user_creation()
    
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES:")
    print(f"   🔐 Autenticação e persistência: {'✅ OK' if success else '❌ FALHOU'}")
    
    if success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A persistência do user_db_id está funcionando")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("⚠️ Verifique os logs acima para mais detalhes")
    
    print("\n🏁 Testes concluídos!")
    return success

if __name__ == "__main__":
    main()