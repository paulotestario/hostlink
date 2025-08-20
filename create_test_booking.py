#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database
from datetime import datetime, timedelta

def create_test_booking():
    """Criar uma reserva de teste para avaliação"""
    db = get_database()
    
    print("🔍 Criando reserva de teste para avaliação...")
    
    # 1. Buscar um listing disponível
    print("\n1. Buscando listing disponível...")
    listings = db.supabase.table('user_listings').select('id, title, user_id').limit(5).execute()
    
    if not listings.data:
        print("❌ Nenhum listing encontrado")
        return None
    
    # Escolher um listing que não seja do próprio usuário 1
    target_listing = None
    for listing in listings.data:
        if listing['user_id'] != 1:  # Não pode ser do próprio usuário
            target_listing = listing
            break
    
    if not target_listing:
        # Se todos os listings são do usuário 1, usar o primeiro mesmo
        target_listing = listings.data[0]
    
    print(f"✅ Listing selecionado: ID {target_listing['id']} - {target_listing['title']}")
    
    # 2. Criar reserva diretamente no banco
    print("\n2. Criando reserva...")
    
    # Datas no passado para simular uma estadia concluída
    checkin_date = '2025-01-10'
    checkout_date = '2025-01-12'
    
    booking_data = {
        'listing_id': target_listing['id'],
        'guest_user_id': 1,  # Paulo César
        'host_user_id': target_listing['user_id'],  # Dono do anúncio
        'guest_name': 'Paulo César',
        'guest_email': 'paulotestario@gmail.com',
        'guest_phone': '+55 11 99999-9999',
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
        'total_nights': 2,
        'price_per_night': 100.00,
        'total_price': 200.00,
        'status': 'completed',  # Já marcado como concluído
        'payment_status': 'paid',
        'created_at': datetime.now().isoformat()
    }
    
    result = db.supabase.table('listing_bookings').insert(booking_data).execute()
    
    if result.data:
        booking_id = result.data[0]['id']
        print(f"✅ Reserva criada com sucesso: ID {booking_id}")
        
        # 3. Verificar se pode avaliar
        print("\n3. Verificando permissão de avaliação...")
        can_review = db.can_user_review_booking(1, booking_id)
        print(f"✅ Pode avaliar: {can_review}")
        
        if can_review:
            print(f"\n🎉 Sucesso! Use booking_id={booking_id} para testar a avaliação")
            print(f"   URL: http://localhost:5000/avaliar-hospedagem?booking_id={booking_id}")
            return booking_id
        else:
            print("❌ Ainda não pode avaliar. Verificando motivo...")
            
            # Verificar se já existe avaliação
            existing_review = db.get_booking_review(booking_id)
            if existing_review:
                print(f"   Motivo: Já existe avaliação (ID: {existing_review['id']})")
            else:
                print("   Motivo: Condições de avaliação não atendidas")
    else:
        print("❌ Erro ao criar reserva")
        return None

if __name__ == '__main__':
    create_test_booking()