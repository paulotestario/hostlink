#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar as tabelas de agenda no Supabase
"""

from database import get_database

def create_agenda_tables():
    """Cria as tabelas de agenda no banco de dados"""
    db = get_database()
    if not db:
        print("❌ Erro ao conectar com o banco de dados")
        return False
    
    try:
        # SQL para criar tabelas de agenda
        sql_commands = [
            """
            CREATE TABLE IF NOT EXISTS listing_availability (
                id SERIAL PRIMARY KEY,
                listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                price_per_night DECIMAL(10,2) NOT NULL,
                is_available BOOLEAN DEFAULT TRUE,
                minimum_nights INTEGER DEFAULT 1,
                maximum_nights INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS listing_bookings (
                id SERIAL PRIMARY KEY,
                listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
                guest_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                checkin_date DATE NOT NULL,
                checkout_date DATE NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                guest_count INTEGER DEFAULT 1,
                status VARCHAR(20) DEFAULT 'pending',
                payment_status VARCHAR(20) DEFAULT 'pending',
                guest_name VARCHAR(255),
                guest_email VARCHAR(255),
                guest_phone VARCHAR(20),
                booking_notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_listing_availability_listing_id 
            ON listing_availability(listing_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_listing_availability_dates 
            ON listing_availability(start_date, end_date)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_listing_bookings_listing_id 
            ON listing_bookings(listing_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_listing_bookings_dates 
            ON listing_bookings(checkin_date, checkout_date)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_listing_bookings_guest 
            ON listing_bookings(guest_user_id)
            """
        ]
        
        # Verificar se as tabelas já existem
        try:
            # Tentar acessar as tabelas para ver se existem
            db.supabase.table('listing_availability').select('id').limit(1).execute()
            db.supabase.table('listing_bookings').select('id').limit(1).execute()
            print("✅ Tabelas de agenda já existem!")
            return True
        except Exception:
            # Tabelas não existem, mostrar SQL para execução manual
            print("📝 As tabelas não existem. Execute o SQL abaixo no Supabase SQL Editor:")
            print("=" * 80)
            
            full_sql = """
-- Criar tabelas de agenda
CREATE TABLE IF NOT EXISTS listing_availability (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    price_per_night DECIMAL(10,2) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    minimum_nights INTEGER DEFAULT 1,
    maximum_nights INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS listing_bookings (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
    guest_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    checkin_date DATE NOT NULL,
    checkout_date DATE NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    guest_count INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',
    payment_status VARCHAR(20) DEFAULT 'pending',
    guest_name VARCHAR(255),
    guest_email VARCHAR(255),
    guest_phone VARCHAR(20),
    booking_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_listing_availability_listing_id ON listing_availability(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_availability_dates ON listing_availability(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_listing_id ON listing_bookings(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_dates ON listing_bookings(checkin_date, checkout_date);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_guest ON listing_bookings(guest_user_id);
            """
            
            print(full_sql)
            print("=" * 80)
            print("\n📋 Instruções:")
            print("1. Copie o SQL acima")
            print("2. Acesse seu projeto no Supabase")
            print("3. Vá em 'SQL Editor'")
            print("4. Cole e execute o SQL")
            print("5. Execute este script novamente para verificar")
            
            return False
        
        print("\n✅ Todas as tabelas de agenda foram criadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        print("\n📝 Execute manualmente no SQL Editor do Supabase:")
        print("https://supabase.com/dashboard/project/[SEU_PROJECT_ID]/sql")
        return False

if __name__ == '__main__':
    print("🚀 Criando tabelas de agenda...\n")
    success = create_agenda_tables()
    
    if success:
        print("\n🎉 Configuração concluída!")
        print("📊 As tabelas de agenda estão prontas para uso")
    else:
        print("\n❌ Falha na configuração")
        print("🔍 Verifique a conexão com o Supabase")