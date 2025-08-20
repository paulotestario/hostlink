import sys
sys.path.append('c:\\hostlink')
from database import get_database
from flask import Flask, session
from auth import User

app = Flask(__name__)
app.secret_key = 'test_key'

with app.app_context():
    with app.test_request_context():
        # Simular login do usuário
        user = User.authenticate_email('paulo.cesar@example.com', 'senha123')
        if user:
            print(f'✅ Usuário autenticado: {user.name}')
            print(f'🔍 user.db_id: {user.db_id}')
            print(f'🔍 session user_db_id: {session.get("user_db_id")}')
            
            # Testar busca de reservas
            db = get_database()
            if db and user.db_id:
                bookings = db.get_user_bookings(user.db_id)
                print(f'🔍 Reservas encontradas: {len(bookings) if bookings else 0}')
                if bookings:
                    for booking in bookings[:3]:
                        print(f'  - Booking ID: {booking.get("id")}, Status: {booking.get("status")}')
            else:
                print('❌ Erro: db ou user.db_id não disponível')
        else:
            print('❌ Falha na autenticação')