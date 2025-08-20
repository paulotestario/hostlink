#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from database import get_database

def test_login_and_review():
    """Testar login e funcionalidade de avaliação via web"""
    base_url = "http://localhost:5000"
    
    # Criar uma sessão para manter cookies
    session = requests.Session()
    
    print("🔍 Testando login e avaliação via web...")
    
    # 1. Tentar acessar a página de avaliação sem login
    print("\n1. Testando acesso sem login...")
    response = session.get(f"{base_url}/avaliar-hospedagem?booking_id=3")
    print(f"Status: {response.status_code}")
    if "login" in response.url.lower():
        print("✅ Redirecionado para login (comportamento esperado)")
    else:
        print(f"⚠️ Resposta inesperada: {response.url}")
    
    # 2. Verificar se existe uma forma de fazer login programático
    print("\n2. Verificando rotas de autenticação...")
    
    # Tentar acessar API sem autenticação
    api_response = session.get(f"{base_url}/api/reviews/can-review/3")
    print(f"API can-review status: {api_response.status_code}")
    
    if api_response.status_code == 401:
        print("✅ API protegida corretamente")
    elif api_response.status_code == 200:
        try:
            print(f"⚠️ API respondeu: {api_response.json()}")
        except:
            print(f"⚠️ API respondeu com status 200, mas conteúdo não é JSON: {api_response.text[:100]}")
    else:
        print(f"❌ Resposta inesperada da API: {api_response.status_code}")
    
    # 3. Verificar dados da reserva diretamente
    print("\n3. Verificando dados da reserva no banco...")
    db = get_database()
    
    booking_result = db.supabase.table('listing_bookings').select('*').eq('id', 3).execute()
    if booking_result.data:
        booking = booking_result.data[0]
        print(f"✅ Reserva encontrada:")
        print(f"   - ID: {booking['id']}")
        print(f"   - Guest User ID: {booking['guest_user_id']}")
        print(f"   - Status: {booking['status']}")
        print(f"   - Listing ID: {booking['listing_id']}")
        
        # Verificar se pode avaliar
        can_review = db.can_user_review_booking(booking['guest_user_id'], 3)
        print(f"   - Pode avaliar: {can_review}")
        
        # Verificar se já existe avaliação
        existing_review = db.get_booking_review(3)
        if existing_review:
            print(f"   - Avaliação existente: ID {existing_review['id']}")
        else:
            print(f"   - Nenhuma avaliação existente")
    else:
        print("❌ Reserva não encontrada")
    
    print("\n🏁 Teste concluído!")
    print("\n💡 Para testar a interface web:")
    print("   1. Acesse http://localhost:5000/login")
    print("   2. Configure o Google OAuth ou implemente login de teste")
    print("   3. Após login, acesse http://localhost:5000/avaliar-hospedagem?booking_id=3")

if __name__ == '__main__':
    test_login_and_review()