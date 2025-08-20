import sys
sys.path.append('c:\\hostlink')
from database import get_database

db = get_database()
if db:
    # Verificar dados do usuário
    user_data = db.get_user_by_email('paulo.cesar@example.com')
    if user_data:
        print(f'✅ Usuário encontrado:')
        print(f'  - ID: {user_data.get("id")}')
        print(f'  - Nome: {user_data.get("name")}')
        print(f'  - Email: {user_data.get("email")}')
        print(f'  - Auth Type: {user_data.get("auth_type")}')
        print(f'  - Password Hash: {user_data.get("password_hash", "N/A")[:20]}...')
    else:
        print('❌ Usuário não encontrado')
        
    # Listar todos os usuários
    print('\n📋 Todos os usuários:')
    try:
        cursor = db.connection.cursor()
        cursor.execute('SELECT id, name, email, auth_type FROM users')
        users = cursor.fetchall()
        for user in users:
            print(f'  - ID: {user[0]}, Nome: {user[1]}, Email: {user[2]}, Auth: {user[3]}')
        cursor.close()
    except Exception as e:
        print(f'❌ Erro ao listar usuários: {e}')
else:
    print('❌ Erro ao conectar com o banco de dados')