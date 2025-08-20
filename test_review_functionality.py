#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database
import requests
import json

def test_review_functionality():
    """Testar funcionalidade de avaliação"""
    db = get_database()
    
    # Dados da reserva que queremos testar
    booking_id = 3
    user_id = 1  # Paulo César
    
    print(f"🔍 Testando funcionalidade de avaliação para booking_id={booking_id}, user_id={user_id}")
    
    # 1. Verificar se a reserva existe
    print("\n1. Verificando reserva...")
    booking_result = db.supabase.table('listing_bookings').select('*').eq('id', booking_id).execute()
    if booking_result.data:
        booking = booking_result.data[0]
        print(f"✅ Reserva encontrada:")
        print(f"   - Listing ID: {booking['listing_id']}")
        print(f"   - Guest User ID: {booking['guest_user_id']}")
        print(f"   - Status: {booking['status']}")
        print(f"   - Check-in: {booking['checkin_date']}")
        print(f"   - Check-out: {booking['checkout_date']}")
    else:
        print("❌ Reserva não encontrada")
        return
    
    # 2. Verificar se o usuário pode avaliar
    print("\n2. Verificando permissão de avaliação...")
    can_review = db.can_user_review_booking(user_id, booking_id)
    print(f"✅ Pode avaliar: {can_review}")
    
    # 3. Verificar se já existe avaliação
    print("\n3. Verificando avaliação existente...")
    existing_review = db.get_booking_review(booking_id)
    if existing_review:
        print(f"⚠️ Já existe avaliação: ID {existing_review['id']}")
        print(f"   - Avaliação geral: {existing_review['overall_rating']} estrelas")
        print(f"   - Título: {existing_review.get('review_title', 'Sem título')}")
    else:
        print("✅ Nenhuma avaliação existente")
    
    # 4. Testar criação de avaliação (se permitido)
    if can_review and not existing_review:
        print("\n4. Testando criação de avaliação...")
        
        review_data = {
            'booking_id': booking_id,
            'overall_rating': 5,
            'cleanliness_rating': 5,
            'communication_rating': 4,
            'checkin_rating': 5,
            'accuracy_rating': 4,
            'location_rating': 5,
            'value_rating': 4,
            'review_title': 'Hospedagem excelente!',
            'review_comment': 'Tudo perfeito, recomendo muito!',
            'would_recommend': True
        }
        
        review_id = db.create_review(**review_data)
        if review_id:
            print(f"✅ Avaliação criada com sucesso! ID: {review_id}")
        else:
            print("❌ Erro ao criar avaliação")
    else:
        if not can_review:
            print("\n4. ❌ Usuário não pode avaliar esta reserva")
        if existing_review:
            print("\n4. ⚠️ Avaliação já existe, não é possível criar outra")
    
    print("\n🏁 Teste concluído!")

if __name__ == '__main__':
    test_review_functionality()