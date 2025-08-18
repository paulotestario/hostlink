import sqlite3
from datetime import datetime

def create_test_notifications():
    conn = sqlite3.connect('hostlink.db')
    cursor = conn.cursor()
    
    # Verificar se existem usuários
    cursor.execute('SELECT id FROM users LIMIT 1')
    user = cursor.fetchone()
    
    if not user:
        print('❌ Nenhum usuário encontrado. Criando usuário de teste...')
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, created_at)
            VALUES ('Usuário Teste', 'teste@hostlink.com', 'hash_teste', ?)
        ''', (datetime.now(),))
        conn.commit()
        user_id = cursor.lastrowid
        print(f'✅ Usuário de teste criado com ID: {user_id}')
    else:
        user_id = user[0]
        print(f'✅ Usando usuário existente com ID: {user_id}')
    
    # Criar notificações de teste
    test_notifications = [
        {
            'title': 'Nova Reserva Recebida',
            'message': 'Você recebeu uma nova reserva para sua propriedade "Casa na Praia".',
            'type': 'booking'
        },
        {
            'title': 'Pagamento Confirmado',
            'message': 'O pagamento da reserva #123 foi confirmado com sucesso.',
            'type': 'payment'
        },
        {
            'title': 'Avaliação Recebida',
            'message': 'Você recebeu uma nova avaliação de 5 estrelas!',
            'type': 'review'
        }
    ]
    
    for notification in test_notifications:
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, type, is_read, created_at)
            VALUES (?, ?, ?, ?, FALSE, ?)
        ''', (user_id, notification['title'], notification['message'], notification['type'], datetime.now()))
    
    conn.commit()
    
    # Verificar notificações criadas
    cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    print(f'✅ {count} notificações criadas para o usuário {user_id}')
    
    # Mostrar as notificações
    cursor.execute('''
        SELECT id, title, message, type, is_read, created_at 
        FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    
    notifications = cursor.fetchall()
    print('\nNotificações criadas:')
    for n in notifications:
        print(f'ID: {n[0]}, Título: {n[1]}, Tipo: {n[3]}, Lida: {n[4]}')
    
    conn.close()

if __name__ == '__main__':
    create_test_notifications()