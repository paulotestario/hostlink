#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database

def create_reviews_table():
    """Cria a tabela accommodation_reviews manualmente"""
    db = get_database()
    
    # Como não podemos executar SQL diretamente, vamos inserir um registro dummy
    # para forçar a criação da tabela via Supabase
    try:
        # Primeiro, vamos tentar verificar se a tabela existe
        result = db.supabase.table('accommodation_reviews').select('id').limit(1).execute()
        print("✅ Tabela accommodation_reviews já existe!")
        return True
    except Exception as e:
        print(f"❌ Tabela não existe: {e}")
        print("📝 Por favor, execute o SQL manualmente no painel do Supabase:")
        print("")
        with open('create_reviews_table.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
            print(sql_content)
        return False

if __name__ == '__main__':
    create_reviews_table()