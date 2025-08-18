#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das notificações no Supabase
"""

import os
from datetime import datetime
from database import get_database
from dotenv import load_dotenv

load_dotenv()

def test_notifications():
    """Testa o sistema de notificações"""
    try:
        db = get_database()
        print("✅ Conexão com Supabase estabelecida")
        
        # Verificar se há usuários
        print("\n🔍 Verificando usuários...")
        # Como não temos acesso direto ao método, vamos tentar criar uma notificação de teste
        
        # Tentar buscar notificações de um usuário (ID 1 como teste)
        print("\n📋 Testando busca de notificações...")
        notifications = db.get_user_notifications(1, limit=5)
        print(f"Notificações encontradas: {len(notifications)}")
        
        if notifications:
            print("\nÚltimas notificações:")
            for notif in notifications:
                print(f"- ID: {notif.get('id')}, Título: {notif.get('title')}, Lida: {notif.get('is_read')}")
        else:
            print("\n📝 Criando notificação de teste...")
            # Tentar criar uma notificação de teste
            notification_id = db.create_notification(
                user_id=1,
                notification_type='test',
                title='Teste de Notificação',
                message='Esta é uma notificação de teste para verificar o sistema.'
            )
            print(f"✅ Notificação criada com ID: {notification_id}")
            
            # Buscar novamente
            notifications = db.get_user_notifications(1, limit=5)
            print(f"Notificações após criação: {len(notifications)}")
        
        # Testar contagem de não lidas
        print("\n🔢 Testando contagem de não lidas...")
        unread_count = db.get_unread_notifications_count(1)
        print(f"Notificações não lidas: {unread_count}")
        
        print("\n✅ Teste de notificações concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste de notificações: {e}")
        import traceback
        traceback.print_exc()

def test_notification_creation():
    """Testa a criação de notificações para diferentes cenários"""
    try:
        db = get_database()
        
        # Criar diferentes tipos de notificações
        notification_types = [
            {
                'type': 'booking',
                'title': 'Nova Reserva',
                'message': 'Você recebeu uma nova reserva para sua propriedade.'
            },
            {
                'type': 'payment',
                'title': 'Pagamento Confirmado',
                'message': 'O pagamento da sua reserva foi confirmado.'
            },
            {
                'type': 'review',
                'title': 'Nova Avaliação',
                'message': 'Você recebeu uma nova avaliação de 5 estrelas!'
            }
        ]
        
        print("\n📝 Criando notificações de teste...")
        for notif_data in notification_types:
            try:
                notification_id = db.create_notification(
                    user_id=1,
                    notification_type=notif_data['type'],
                    title=notif_data['title'],
                    message=notif_data['message']
                )
                print(f"✅ Notificação '{notif_data['title']}' criada com ID: {notification_id}")
            except Exception as e:
                print(f"❌ Erro ao criar notificação '{notif_data['title']}': {e}")
        
        # Verificar notificações criadas
        notifications = db.get_user_notifications(1, limit=10)
        print(f"\n📋 Total de notificações: {len(notifications)}")
        
        for notif in notifications:
            print(f"- {notif.get('title')} ({notif.get('type')}) - Lida: {notif.get('is_read')}")
            
    except Exception as e:
        print(f"❌ Erro na criação de notificações: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🧪 Iniciando teste do sistema de notificações...")
    test_notifications()
    print("\n" + "="*50)
    test_notification_creation()