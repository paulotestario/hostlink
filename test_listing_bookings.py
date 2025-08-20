import sys
sys.path.append('c:\\hostlink')
from database import get_database

db = get_database()
if db:
    print("🔍 Testando tabela listing_bookings diretamente...")
    
    try:
        # Buscar todas as reservas na tabela listing_bookings
        result = db.supabase.table('listing_bookings').select('*').execute()
        bookings = result.data
        
        print(f"📊 Total de reservas na tabela listing_bookings: {len(bookings)}")
        
        if bookings:
            print("\n📋 Primeiras 10 reservas:")
            for booking in bookings[:10]:
                print(f"  - ID: {booking.get('id')}, Guest: {booking.get('guest_user_id')}, Status: {booking.get('status')}, Listing: {booking.get('listing_id')}")
            
            # Verificar se existem reservas para os usuários Paulo
            paulo_bookings_1 = [b for b in bookings if b.get('guest_user_id') == 1]
            paulo_bookings_8 = [b for b in bookings if b.get('guest_user_id') == 8]
            
            print(f"\n✅ Reservas para Paulo ID 1: {len(paulo_bookings_1)}")
            print(f"✅ Reservas para Paulo ID 8: {len(paulo_bookings_8)}")
            
            # Testar a função get_user_bookings diretamente
            print("\n🔍 Testando função get_user_bookings:")
            bookings_1 = db.get_user_bookings(1)
            bookings_8 = db.get_user_bookings(8)
            
            print(f"  - get_user_bookings(1): {len(bookings_1) if bookings_1 else 0} reservas")
            print(f"  - get_user_bookings(8): {len(bookings_8) if bookings_8 else 0} reservas")
            
        else:
            print("❌ Nenhuma reserva encontrada na tabela listing_bookings")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
else:
    print("❌ Erro ao conectar com o banco de dados")