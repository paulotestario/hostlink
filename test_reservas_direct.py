import sys
sys.path.append('c:\\hostlink')
from database import get_database

db = get_database()
if db:
    print("🔍 Testando busca de reservas diretamente...")
    
    # Testar com todos os usuários Paulo
    try:
        result = db.supabase.table('users').select('*').ilike('name', '%paulo%').execute()
        paulo_users = result.data
        print(f"📋 Usuários Paulo encontrados: {len(paulo_users)}")
        
        all_bookings = []
        for paulo_user in paulo_users:
            paulo_id = paulo_user.get('id')
            paulo_name = paulo_user.get('name')
            paulo_email = paulo_user.get('email')
            print(f"\n👤 Testando usuário: {paulo_name} (ID: {paulo_id}, Email: {paulo_email})")
            
            # Buscar reservas
            bookings = db.get_user_bookings(paulo_id)
            print(f"   📊 Reservas encontradas: {len(bookings) if bookings else 0}")
            
            if bookings:
                for booking in bookings:
                    print(f"     - Booking ID: {booking.get('id')}, Status: {booking.get('status')}, Guest: {booking.get('guest_user_id')}")
                    all_bookings.append(booking)
        
        print(f"\n✅ Total de reservas encontradas: {len(all_bookings)}")
        
        # Testar também busca direta na tabela bookings
        print("\n🔍 Testando busca direta na tabela bookings...")
        direct_result = db.supabase.table('bookings').select('*').execute()
        all_direct_bookings = direct_result.data
        print(f"📊 Total de bookings na tabela: {len(all_direct_bookings)}")
        
        # Mostrar alguns exemplos
        for booking in all_direct_bookings[:5]:
            print(f"  - ID: {booking.get('id')}, Guest: {booking.get('guest_user_id')}, Status: {booking.get('status')}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
else:
    print("❌ Erro ao conectar com o banco de dados")