import sys
sys.path.append('c:\\hostlink')
from database import get_database

db = get_database()
if db:
    print("🔍 Verificando reservas do usuário ID 8...")
    bookings = db.get_user_bookings(8)
    
    if bookings:
        print(f"✅ Usuário ID 8 tem {len(bookings)} reserva(s):")
        for booking in bookings:
            print(f"  - Reserva ID: {booking.get('id')}, Status: {booking.get('status')}, Guest: {booking.get('guest_user_id')}")
    else:
        print("❌ Usuário ID 8 não tem nenhuma reserva.")
else:
    print("❌ Erro ao conectar com o banco de dados")