#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database

def check_users():
    """Verificar usuários no banco de dados"""
    db = get_database()
    
    try:
        users = db.supabase.table('users').select('*').limit(5).execute()
        print(f'Usuários encontrados: {len(users.data)}')
        
        for user in users.data:
            print(f'ID: {user["id"]}, Nome: {user["name"]}, Email: {user["email"]}')
            
    except Exception as e:
        print(f'Erro ao buscar usuários: {e}')

if __name__ == '__main__':
    check_users()