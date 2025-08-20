#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database

def check_bookings_and_reviews():
    """Verificar reservas e avaliações"""
    db = get_database()
    
    print("🔍 Verificando reservas e avaliações...")
    
    # 1. Buscar todas as reservas do usuário 1
    print("\n1. Reservas do usuário 1 (Paulo César):")
    bookings = db.supabase.table('listing_bookings').select('id, guest_user_id, status, listing_id, checkin_date, checkout_date').eq('guest_user_id', 1).execute()
    
    if bookings.data:
        for booking in bookings.data:
            print(f"   - ID: {booking['id']}, Status: {booking['status']}, Listing: {booking['listing_id']}")
            print(f"     Check-in: {booking['checkin_date']}, Check-out: {booking['checkout_date']}")
    else:
        print("   Nenhuma reserva encontrada")
    
    # 2. Buscar todas as avaliações
    print("\n2. Avaliações existentes:")
    reviews = db.supabase.table('accommodation_reviews').select('id, booking_id, overall_rating, review_title').execute()
    
    reviewed_booking_ids = []
    if reviews.data:
        for review in reviews.data:
            reviewed_booking_ids.append(review['booking_id'])
            print(f"   - Review ID: {review['id']}, Booking ID: {review['booking_id']}, Rating: {review['overall_rating']}")
            print(f"     Título: {review.get('review_title', 'Sem título')}")
    else:
        print("   Nenhuma avaliação encontrada")
    
    # 3. Identificar reservas sem avaliação
    print("\n3. Reservas sem avaliação:")
    unreviewed_bookings = []
    if bookings.data:
        for booking in bookings.data:
            if booking['id'] not in reviewed_booking_ids:
                unreviewed_bookings.append(booking)
                print(f"   - Booking ID: {booking['id']}, Status: {booking['status']}")
                
                # Verificar se pode avaliar
                can_review = db.can_user_review_booking(1, booking['id'])
                print(f"     Pode avaliar: {can_review}")
    
    if not unreviewed_bookings:
        print("   Todas as reservas já foram avaliadas")
    
    # 4. Criar uma nova reserva de teste se necessário
    if not unreviewed_bookings:
        print("\n4. Criando reserva de teste...")
        
        # Buscar um listing disponível
        listings = db.supabase.table('user_listings').select('id, title').limit(1).execute()
        if listings.data:
            listing_id = listings.data[0]['id']
            
            # Criar reserva de teste
            booking_id = db.create_authenticated_booking(
                listing_id=listing_id,
                guest_user_id=1,
                start_date='2025-01-20',
                end_date='2025-01-22',
                guest_name='Paulo César',
                guest_email='paulotestario@gmail.com',
                guests_count=2
            )
            
            if booking_id:
                print(f"✅ Reserva de teste criada: ID {booking_id}")
                
                # Marcar como completed para poder avaliar
                update_result = db.supabase.table('listing_bookings').update({
                    'status': 'completed'
                }).eq('id', booking_id).execute()
                
                if update_result.data:
                    print(f"✅ Status atualizado para 'completed'")
                    
                    # Verificar se pode avaliar
                    can_review = db.can_user_review_booking(1, booking_id)
                    print(f"✅ Pode avaliar a nova reserva: {can_review}")
                    
                    return booking_id
            else:
                print("❌ Erro ao criar reserva de teste")
        else:
            print("❌ Nenhum listing encontrado para criar reserva de teste")
    
    return unreviewed_bookings[0]['id'] if unreviewed_bookings else None

if __name__ == '__main__':
    booking_id = check_bookings_and_reviews()
    if booking_id:
        print(f"\n💡 Use booking_id={booking_id} para testar a avaliação")
        print(f"   URL: http://localhost:5000/avaliar-hospedagem?booking_id={booking_id}")