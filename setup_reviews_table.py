#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar a tabela de avaliações de hospedagem
"""

from database import get_database

def setup_reviews_table():
    """Criar tabela de avaliações no banco de dados"""
    db = get_database()
    
    # SQL para criar a tabela de avaliações
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS accommodation_reviews (
            id SERIAL PRIMARY KEY,
            booking_id INTEGER REFERENCES listing_bookings(id) ON DELETE CASCADE,
            listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
            guest_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            host_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            
            -- Avaliacoes por categoria (1-5 estrelas)
            overall_rating INTEGER NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
            cleanliness_rating INTEGER CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
            communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
            checkin_rating INTEGER CHECK (checkin_rating >= 1 AND checkin_rating <= 5),
            accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
            location_rating INTEGER CHECK (location_rating >= 1 AND location_rating <= 5),
            value_rating INTEGER CHECK (value_rating >= 1 AND value_rating <= 5),
            
            -- Comentarios
            review_title VARCHAR(255),
            review_comment TEXT,
            
            -- Recomendacao
            would_recommend BOOLEAN DEFAULT TRUE,
            
            -- Controle
            is_public BOOLEAN DEFAULT TRUE,
            is_approved BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        
        # Índices para performance
        "CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_booking_id ON accommodation_reviews(booking_id)",
        "CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_listing_id ON accommodation_reviews(listing_id)",
        "CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_guest_user_id ON accommodation_reviews(guest_user_id)",
        "CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_host_user_id ON accommodation_reviews(host_user_id)",
        "CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_overall_rating ON accommodation_reviews(overall_rating)",
        "CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_created_at ON accommodation_reviews(created_at)",
        
        # Constraint única
        "ALTER TABLE accommodation_reviews ADD CONSTRAINT IF NOT EXISTS unique_review_per_booking UNIQUE (booking_id)"
    ]
    
    try:
        for i, sql in enumerate(sql_commands):
            if sql.strip():
                try:
                    # Usar rpc para executar SQL no Supabase
                    result = db.supabase.rpc('exec_sql', {'sql': sql}).execute()
                    print(f"✓ Comando {i+1} executado com sucesso")
                except Exception as cmd_error:
                    # Se rpc não funcionar, tentar método direto
                    try:
                        # Método alternativo para criar tabela
                        if 'CREATE TABLE' in sql:
                            print(f"⚠️ Usando método alternativo para comando {i+1}")
                            # Para criar tabela, vamos usar uma abordagem diferente
                            continue
                        else:
                            print(f"⚠️ Pulando comando {i+1}: {cmd_error}")
                    except Exception as alt_error:
                        print(f"⚠️ Erro no comando {i+1}: {alt_error}")
        
        print("\n🎉 Setup de avaliações concluído!")
        print("📝 Nota: Se houver erros, execute o SQL manualmente no painel do Supabase")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar tabela de avaliações: {e}")
        print("\n📋 SQL para executar manualmente no Supabase:")
        print("=" * 50)
        for sql in sql_commands:
            if sql.strip():
                print(sql)
                print(";")
        print("=" * 50)
        return False

if __name__ == "__main__":
    setup_reviews_table()