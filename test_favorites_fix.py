#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a correção do erro 'User' object has no attribute 'db_id' funcionou
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database
from auth import User
from flask import Flask, session

def test_user_db_id_fix():
    """
    Testa se o User agora tem o atributo db_id corretamente
    """
    print("🧪 TESTE: Correção do atributo db_id no User")
    print("=" * 50)
    
    # Conectar ao banco
    print("🔍 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    # Dados de teste do usuário
    test_google_id = "test_user_db_id_fix_123"
    test_email = "teste_fix@hostlink.com"
    test_name = "Usuário Teste Fix"
    test_profile_pic = "https://example.com/profile.jpg"
    
    print(f"📝 Dados de teste:")
    print(f"   Google ID: {test_google_id}")
    print(f"   Email: {test_email}")
    print(f"   Nome: {test_name}")
    
    try:
        # Criar usuário no banco
        print("\n🚀 Criando usuário no banco...")
        user_db_id = db.save_user(test_google_id, test_email, test_name, test_profile_pic)
        
        if not user_db_id:
            print("❌ Erro ao criar usuário no banco")
            return False
        
        print(f"✅ Usuário criado com ID: {user_db_id}")
        
        # Testar criação via User.create com Flask context
        print("\n🧪 Testando User.create com Flask context...")
        
        app = Flask(__name__)
        app.secret_key = 'test_key_fix'
        
        with app.test_request_context():
            session.clear()
            
            # Criar usuário
            user = User.create(test_google_id, test_name, test_email, test_profile_pic)
            
            if user:
                print(f"✅ User.create executado com sucesso")
                print(f"   user.id: {user.id}")
                print(f"   user.name: {user.name}")
                print(f"   user.email: {user.email}")
                
                # Verificar se db_id está definido
                if hasattr(user, 'db_id'):
                    print(f"✅ user.db_id existe: {user.db_id}")
                    
                    if user.db_id:
                        print("✅ user.db_id tem valor válido!")
                        
                        # Testar User.get
                        print("\n🔍 Testando User.get...")
                        retrieved_user = User.get(user.id)
                        
                        if retrieved_user and hasattr(retrieved_user, 'db_id'):
                            print(f"✅ User.get funcionou, db_id: {retrieved_user.db_id}")
                            
                            # Simular uso em API de favoritos
                            print("\n🎯 Simulando uso em API de favoritos...")
                            try:
                                # Isso deveria funcionar agora
                                user_id_for_api = retrieved_user.db_id
                                print(f"✅ current_user.db_id funcionaria: {user_id_for_api}")
                                return True
                            except AttributeError as e:
                                print(f"❌ Ainda há erro de atributo: {e}")
                                return False
                        else:
                            print("❌ User.get não funcionou corretamente")
                            return False
                    else:
                        print("❌ user.db_id é None")
                        return False
                else:
                    print("❌ user.db_id não existe")
                    return False
            else:
                print("❌ Erro ao criar usuário via User.create")
                return False
                
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_user_db_id_fix()
    if success:
        print("\n🎉 TESTE PASSOU! A correção funcionou.")
    else:
        print("\n💥 TESTE FALHOU! Ainda há problemas.")
    
    sys.exit(0 if success else 1)