import sys
sys.path.append('c:\\hostlink')
from database import get_database

db = get_database()
if db:
    try:
        # Listar todos os usuários
        result = db.supabase.table('users').select('*').execute()
        users = result.data
        
        print(f'📋 Total de usuários: {len(users)}')
        for user in users:
            print(f'  - ID: {user.get("id")}, Nome: {user.get("name")}, Email: {user.get("email")}, Auth: {user.get("auth_type", "google")}')
            
        # Verificar se existe o usuário Paulo César
        paulo_user = None
        for user in users:
            if 'paulo' in user.get('name', '').lower():
                paulo_user = user
                break
                
        if paulo_user:
            print(f'\n✅ Usuário Paulo encontrado:')
            print(f'  - ID: {paulo_user.get("id")}')
            print(f'  - Nome: {paulo_user.get("name")}')
            print(f'  - Email: {paulo_user.get("email")}')
            
            # Buscar reservas deste usuário
            bookings = db.get_user_bookings(paulo_user.get('id'))
            print(f'  - Reservas: {len(bookings) if bookings else 0}')
            if bookings:
                for booking in bookings[:3]:
                    print(f'    * Booking ID: {booking.get("id")}, Status: {booking.get("status")}')
        else:
            print('❌ Usuário Paulo não encontrado')
            
    except Exception as e:
        print(f'❌ Erro ao listar usuários: {e}')
else:
    print('❌ Erro ao conectar com o banco de dados')