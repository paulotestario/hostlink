import sqlite3

def check_notifications():
    try:
        conn = sqlite3.connect('hostlink.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'")
        if not cursor.fetchone():
            print("❌ Tabela 'notifications' não existe")
            return
        
        # Contar notificações
        cursor.execute('SELECT COUNT(*) FROM notifications')
        total = cursor.fetchone()[0]
        print(f"📊 Total de notificações: {total}")
        
        if total > 0:
            # Mostrar algumas notificações
            cursor.execute('SELECT id, title, message, is_read FROM notifications LIMIT 5')
            print("\n📋 Notificações de exemplo:")
            for row in cursor.fetchall():
                status = "✅ Lida" if row[3] else "🔔 Não lida"
                print(f"ID: {row[0]}, Título: {row[1]}, Status: {status}")
                print(f"   Mensagem: {row[2][:80]}...")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    check_notifications()