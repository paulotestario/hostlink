#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import database

def create_favorites_table():
    """Cria a tabela user_favorites no banco de dados"""
    try:
        db = database.get_database()
        
        # SQL para criar a tabela user_favorites
        sql_query = """
        CREATE TABLE IF NOT EXISTS user_favorites (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            listing_id INTEGER NOT NULL REFERENCES user_listings(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, listing_id)
        );
        
        -- Criar índices para melhor performance
        CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_favorites_listing_id ON user_favorites(listing_id);
        CREATE INDEX IF NOT EXISTS idx_user_favorites_created_at ON user_favorites(created_at);
        """
        
        # Executar o SQL usando rpc (remote procedure call)
        result = db.supabase.rpc('exec_sql', {'sql': sql_query}).execute()
        
        if result:
            print("✅ Tabela user_favorites criada com sucesso!")
            return True
        else:
            print("❌ Erro ao criar tabela user_favorites")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        
        # Tentar método alternativo usando insert direto
        try:
            # Verificar se a tabela já existe consultando o schema
            existing_tables = db.supabase.table('information_schema.tables').select('table_name').eq('table_schema', 'public').eq('table_name', 'user_favorites').execute()
            
            if existing_tables.data:
                print("✅ Tabela user_favorites já existe!")
                return True
            else:
                print("⚠️ Tabela user_favorites não existe. Será necessário criar manualmente no Supabase.")
                print("SQL para executar no Supabase:")
                print(sql_query)
                return False
                
        except Exception as e2:
            print(f"❌ Erro ao verificar tabela: {e2}")
            print("⚠️ Execute o seguinte SQL manualmente no Supabase:")
            print(sql_query)
            return False

if __name__ == '__main__':
    create_favorites_table()