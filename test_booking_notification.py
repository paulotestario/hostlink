#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database
from datetime import datetime, timedelta

def test_booking_notification():
    """Testa se as notificações são criadas automaticamente ao fazer uma reserva"""
    try:
        db = get_database()
        
        print("🧪 Testando criação automática de notificações...\n")
        
        # Verificar se existem anúncios disponíveis
        listings = db.get_all_public_listings()
        if not listings:
            print("❌ Nenhum anúncio encontrado para teste")
            return
        
        listing = listings[0]
        listing_id = listing['id']
        host_user_id = listing['user_id']
        
        print(f"📋 Usando anúncio ID: {listing_id}")
        print(f"🏠 Título: {listing.get('title', 'N/A')}")
        print(f"👤 Host ID: {host_user_id}")
        
        # Contar notificações antes
        notifications_before = db.get_user_notifications(host_user_id)
        unread_before = db.get_unread_notifications_count(host_user_id)
        print(f"\n📊 Notificações antes: {len(notifications_before)} (não lidas: {unread_before})")
        
        # Criar uma reserva de teste
        start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        print(f"\n🗓️ Criando reserva de {start_date} até {end_date}...")
        
        booking_id = db.create_public_booking(
            listing_id=listing_id,
            start_date=start_date,
            end_date=end_date,
            guest_name="João Teste",
            guest_email="joao.teste@email.com",
            guest_phone="(11) 99999-9999"
        )
        
        if booking_id:
            print(f"✅ Reserva criada com ID: {booking_id}")
            
            # Contar notificações depois
            notifications_after = db.get_user_notifications(host_user_id)
            unread_after = db.get_unread_notifications_count(host_user_id)
            print(f"\n📊 Notificações depois: {len(notifications_after)} (não lidas: {unread_after})")
            
            # Verificar se uma nova notificação foi criada
            if len(notifications_after) > len(notifications_before):
                print("✅ Nova notificação criada automaticamente!")
                
                # Mostrar a notificação mais recente
                latest_notification = notifications_after[0]  # Assumindo que está ordenada por data
                print(f"\n🔔 Última notificação:")
                print(f"   Título: {latest_notification['title']}")
                print(f"   Mensagem: {latest_notification['message']}")
                print(f"   Tipo: {latest_notification['type']}")
                print(f"   Lida: {'Sim' if latest_notification['is_read'] else 'Não'}")
                print(f"   Data: {latest_notification['created_at']}")
                
                if latest_notification['related_booking_id'] == booking_id:
                    print("✅ Notificação corretamente vinculada à reserva!")
                else:
                    print("⚠️ Notificação não está vinculada à reserva criada")
            else:
                print("❌ Nenhuma nova notificação foi criada")
                
        else:
            print("❌ Erro ao criar reserva")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

def test_authenticated_booking_notification():
    """Testa notificação para reserva autenticada"""
    try:
        db = get_database()
        
        print("\n🧪 Testando reserva autenticada...\n")
        
        # Buscar um usuário para usar como guest
        users_result = db.supabase.table('users').select('id, name, email').limit(1).execute()
        if not users_result.data:
            print("❌ Nenhum usuário encontrado para teste")
            return
            
        guest_user = users_result.data[0]
        guest_user_id = guest_user['id']
        
        # Buscar anúncios
        listings = db.get_all_public_listings()
        if not listings:
            print("❌ Nenhum anúncio encontrado")
            return
            
        listing = listings[0]
        listing_id = listing['id']
        host_user_id = listing['user_id']
        
        # Verificar se guest e host são diferentes
        if guest_user_id == host_user_id:
            print("⚠️ Guest e host são o mesmo usuário, pulando teste")
            return
            
        print(f"👤 Guest: {guest_user['name']} (ID: {guest_user_id})")
        print(f"🏠 Host: ID {host_user_id}")
        
        # Contar notificações antes
        notifications_before = db.get_user_notifications(host_user_id)
        print(f"📊 Notificações do host antes: {len(notifications_before)}")
        
        # Criar reserva autenticada
        start_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=17)).strftime('%Y-%m-%d')
        
        booking_id = db.create_authenticated_booking(
            listing_id=listing_id,
            guest_user_id=guest_user_id,
            start_date=start_date,
            end_date=end_date,
            guest_name=guest_user['name'],
            guest_email=guest_user['email']
        )
        
        if booking_id:
            print(f"✅ Reserva autenticada criada com ID: {booking_id}")
            
            # Verificar notificações
            notifications_after = db.get_user_notifications(host_user_id)
            print(f"📊 Notificações do host depois: {len(notifications_after)}")
            
            if len(notifications_after) > len(notifications_before):
                print("✅ Notificação criada para reserva autenticada!")
            else:
                print("❌ Notificação não foi criada")
        else:
            print("❌ Erro ao criar reserva autenticada")
            
    except Exception as e:
        print(f"❌ Erro no teste autenticado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔍 Testando sistema de notificações automáticas...\n")
    test_booking_notification()
    test_authenticated_booking_notification()
    print("\n✅ Testes concluídos!")