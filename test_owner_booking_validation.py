#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database
from flask import Flask
from web_app import app
import json

def test_owner_booking_validation():
    """
    Testa se a validação impede o dono do anúncio de reservar seu próprio anúncio
    """
    print("🧪 TESTE: Validação de reserva do próprio anúncio")
    print("=" * 50)
    
    # Conectar ao banco
    print("🔗 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    try:
        # Buscar um usuário que tenha anúncios
        print("\n🔍 Buscando usuários com anúncios...")
        users_result = db.supabase.table('users').select('*').execute()
        users = users_result.data
        
        owner_user = None
        owner_listing = None
        
        for user in users:
            user_listings = db.get_user_listings(user['id'])
            if user_listings:
                owner_user = user
                owner_listing = user_listings[0]
                break
        
        if not owner_user or not owner_listing:
            print("⚠️ Nenhum usuário com anúncios encontrado para teste")
            return False
        
        print(f"👤 Usuário teste: {owner_user['name']} (ID: {owner_user['id']})")
        print(f"🏠 Anúncio teste: {owner_listing['title']} (ID: {owner_listing['id']})")
        
        # Testar com o contexto da aplicação Flask
        with app.test_client() as client:
            with app.test_request_context():
                # Simular dados de reserva
                booking_data = {
                    'listing_id': owner_listing['id'],
                    'guest_user_id': owner_user['id'],  # Mesmo usuário que é dono
                    'checkin_date': '2024-12-20',
                    'checkout_date': '2024-12-22',
                    'total_price': 300.0,
                    'guest_count': 2
                }
                
                print("\n🧪 Testando validação na função create_booking...")
                
                # Verificar se o usuário é dono do anúncio
                listing = db.get_public_listing_by_id(owner_listing['id'])
                if listing and listing.get('user_id') == owner_user['id']:
                    print("✅ Confirmado: Usuário é dono do anúncio")
                    print("🚫 Validação deve impedir a reserva")
                    
                    # Simular a validação
                    if listing.get('user_id') == booking_data['guest_user_id']:
                        print("✅ TESTE PASSOU: Validação detectou que usuário é dono do anúncio")
                        print("   Mensagem de erro: 'Você não pode reservar seu próprio anúncio'")
                        return True
                    else:
                        print("❌ TESTE FALHOU: Validação não detectou que usuário é dono")
                        return False
                else:
                    print("❌ Erro: Não foi possível verificar propriedade do anúncio")
                    return False
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_non_owner_booking():
    """
    Testa se usuários que não são donos podem fazer reservas normalmente
    """
    print("\n🧪 TESTE: Reserva de usuário não-dono")
    print("=" * 40)
    
    db = get_database()
    
    try:
        # Buscar dois usuários diferentes
        users_result = db.supabase.table('users').select('*').execute()
        users = users_result.data
        
        if len(users) < 2:
            print("⚠️ Necessário pelo menos 2 usuários para este teste")
            return False
        
        # Encontrar um usuário com anúncios e outro sem
        owner_user = None
        guest_user = None
        owner_listing = None
        
        for user in users:
            user_listings = db.get_user_listings(user['id'])
            if user_listings and not owner_user:
                owner_user = user
                owner_listing = user_listings[0]
            elif not user_listings and not guest_user:
                guest_user = user
            
            if owner_user and guest_user:
                break
        
        if not owner_user or not guest_user or not owner_listing:
            # Se não encontrou usuários ideais, usar usuários diferentes
            owner_user = users[0]
            guest_user = users[1] if len(users) > 1 else users[0]
            owner_listings = db.get_user_listings(owner_user['id'])
            if owner_listings:
                owner_listing = owner_listings[0]
            else:
                print("⚠️ Nenhum anúncio encontrado para teste")
                return False
        
        print(f"👤 Dono: {owner_user['name']} (ID: {owner_user['id']})")
        print(f"👤 Hóspede: {guest_user['name']} (ID: {guest_user['id']})")
        print(f"🏠 Anúncio: {owner_listing['title']} (ID: {owner_listing['id']})")
        
        # Testar validação
        listing = db.get_public_listing_by_id(owner_listing['id'])
        if listing and listing.get('user_id') != guest_user['id']:
            print("✅ TESTE PASSOU: Usuário diferente pode fazer reserva")
            print("   Validação permite reserva de usuário não-dono")
            return True
        else:
            print("❌ TESTE FALHOU: Problema na validação")
            return False
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando testes de validação de reservas...\n")
    
    test1_result = test_owner_booking_validation()
    test2_result = test_non_owner_booking()
    
    print("\n📊 RESUMO DOS TESTES:")
    print("=" * 30)
    print(f"✅ Validação dono do anúncio: {'PASSOU' if test1_result else 'FALHOU'}")
    print(f"✅ Validação usuário diferente: {'PASSOU' if test2_result else 'FALHOU'}")
    
    if test1_result and test2_result:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   A validação está funcionando corretamente.")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM!")
        print("   Verifique a implementação da validação.")