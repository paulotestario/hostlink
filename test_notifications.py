#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database
import sqlite3

def test_notifications_table():
    """Testa se a tabela de notificações existe e funciona corretamente"""
    try:
        db = get_database()
        cursor = db.connection.cursor()
        
        # Verifica se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications';")
        result = cursor.fetchone()
        
        if result:
            print("✅ Tabela 'notifications' existe")
            
            # Verifica a estrutura da tabela
            cursor.execute("PRAGMA table_info(notifications);")
            columns = cursor.fetchall()
            print("\n📋 Estrutura da tabela:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Conta quantas notificações existem
            cursor.execute("SELECT COUNT(*) FROM notifications;")
            count = cursor.fetchone()[0]
            print(f"\n📊 Total de notificações: {count}")
            
            # Lista as notificações existentes
            if count > 0:
                cursor.execute("SELECT id, user_id, type, title, message, is_read, created_at FROM notifications ORDER BY created_at DESC LIMIT 5;")
                notifications = cursor.fetchall()
                print("\n📝 Últimas notificações:")
                for notif in notifications:
                    status = "✅ Lida" if notif[5] else "🔔 Não lida"
                    print(f"  ID: {notif[0]} | User: {notif[1]} | Tipo: {notif[2]} | {status}")
                    print(f"      Título: {notif[3]}")
                    print(f"      Mensagem: {notif[4]}")
                    print(f"      Data: {notif[6]}")
                    print()
        else:
            print("❌ Tabela 'notifications' NÃO existe")
            print("\n🔧 Executando script de criação...")
            
            # Lê e executa o script de criação
            with open('create_notifications_table.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            cursor.executescript(sql_script)
            db.connection.commit()
            print("✅ Tabela criada com sucesso")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Erro ao testar notificações: {e}")
        import traceback
        traceback.print_exc()

def test_notification_functions():
    """Testa as funções de notificação"""
    try:
        db = get_database()
        
        print("\n🧪 Testando funções de notificação...")
        
        # Testa criar notificação
        notification_id = db.create_notification(
            user_id=1,
            notification_type='booking',
            title='Teste de Notificação',
            message='Esta é uma notificação de teste para verificar o sistema.',
            related_booking_id=None
        )
        
        if notification_id:
            print(f"✅ Notificação criada com ID: {notification_id}")
            
            # Testa buscar notificações do usuário
            notifications = db.get_user_notifications(user_id=1)
            print(f"✅ Encontradas {len(notifications)} notificações para o usuário 1")
            
            # Testa contar não lidas
            unread_count = db.get_unread_notifications_count(user_id=1)
            print(f"✅ {unread_count} notificações não lidas")
            
            # Testa marcar como lida
            success = db.mark_notification_as_read(notification_id)
            if success:
                print("✅ Notificação marcada como lida")
                
                # Verifica se realmente foi marcada
                unread_count_after = db.get_unread_notifications_count(user_id=1)
                print(f"✅ Agora {unread_count_after} notificações não lidas")
            else:
                print("❌ Erro ao marcar notificação como lida")
        else:
            print("❌ Erro ao criar notificação")
            
    except Exception as e:
        print(f"❌ Erro ao testar funções: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔍 Testando sistema de notificações...\n")
    test_notifications_table()
    test_notification_functions()
    print("\n✅ Teste concluído!")