import sqlite3

def check_tables():
    conn = sqlite3.connect('hostlink.db')
    cursor = conn.cursor()
    
    # Verificar tabelas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print('Tabelas existentes:')
    for table in tables:
        print(f'- {table[0]}')
    
    # Verificar se a tabela notifications existe
    if 'notifications' not in [table[0] for table in tables]:
        print('\n❌ Tabela notifications não existe!')
        print('Criando tabela notifications...')
        
        # Criar tabela notifications
        cursor.execute('''
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                booking_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (booking_id) REFERENCES listing_bookings (id)
            )
        ''')
        
        conn.commit()
        print('✅ Tabela notifications criada com sucesso!')
    else:
        print('\n✅ Tabela notifications já existe!')
        
        # Verificar quantas notificações existem
        cursor.execute('SELECT COUNT(*) FROM notifications')
        count = cursor.fetchone()[0]
        print(f'Total de notificações: {count}')
        
        if count > 0:
            cursor.execute('SELECT id, title, message, is_read FROM notifications ORDER BY created_at DESC LIMIT 5')
            notifications = cursor.fetchall()
            print('\nÚltimas 5 notificações:')
            for n in notifications:
                print(f'ID: {n[0]}, Título: {n[1]}, Lida: {n[3]}')
    
    conn.close()

if __name__ == '__main__':
    check_tables()