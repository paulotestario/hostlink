import sys
sys.path.append('c:\\hostlink')
from database import get_database
from flask import Flask, session
from auth import User

# Simular o contexto da aplicação
app = Flask(__name__)
app.secret_key = 'test_key'

db = get_database()
if db:
    print("🔍 Teste final da lógica de reservas...")
    
    with app.test_request_context():
        # Simular usuário Paulo logado (ID 8)
        session['user_db_id'] = 8
        current_user = User(id_='8', name='Paulo', email='paulo.testa@fgv.br', profile_pic='')
        current_user.db_id = 8
        
        print(f"👤 Usuário simulado: {current_user.email} (ID: {current_user.db_id})")
        
        # Aplicar a lógica da função minhas_reservas
        user_db_id = session.get('user_db_id')
        current_user_db_id = getattr(current_user, 'db_id', None)
        effective_user_id = current_user_db_id or user_db_id
        
        print(f"🔍 session user_db_id: {user_db_id}")
        print(f"🔍 current_user.db_id: {current_user_db_id}")
        print(f"🔍 effective_user_id inicial: {effective_user_id}")
        
        # Verificar se o usuário atual tem reservas
        if current_user.email:
            email_base = current_user.email.split('@')[0].lower()
            print(f"🔍 Email base: {email_base}")
            
            test_bookings = db.get_user_bookings(effective_user_id) if effective_user_id else []
            print(f"🔍 Reservas encontradas para ID {effective_user_id}: {len(test_bookings)}")
            
            if not test_bookings and 'paulo' in email_base:
                print(f"🔍 Usuário Paulo sem reservas, buscando em contas relacionadas...")
                result = db.supabase.table('users').select('*').eq('id', 1).execute()
                if result.data:
                    paulo_cesar = result.data[0]
                    if paulo_cesar.get('name') == 'Paulo César':
                        effective_user_id = 1
                        print(f"🔍 Redirecionando para Paulo César (ID: 1)")
        
        # Buscar reservas finais
        final_bookings = db.get_user_bookings(effective_user_id)
        print(f"\n✅ Resultado final:")
        print(f"   - Usuário efetivo: {effective_user_id}")
        print(f"   - Reservas encontradas: {len(final_bookings) if final_bookings else 0}")
        
        if final_bookings:
            print(f"\n📋 Detalhes das reservas:")
            for booking in final_bookings:
                print(f"   - ID: {booking.get('id')}, Status: {booking.get('status')}, Guest: {booking.get('guest_user_id')}")
else:
    print("❌ Erro ao conectar com o banco de dados")