-- Script para criar tabela de agendas de disponibilidade
-- Execute este script no editor SQL do Supabase

-- Tabela de agendas de disponibilidade
CREATE TABLE IF NOT EXISTS listing_availability (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    price_per_night DECIMAL(10,2),
    minimum_nights INTEGER DEFAULT 1,
    maximum_nights INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraint para evitar duplicatas de data por anúncio
    UNIQUE(listing_id, date)
);

-- Tabela de reservas (para controlar datas ocupadas)
CREATE TABLE IF NOT EXISTS listing_bookings (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
    guest_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    host_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    checkin_date DATE NOT NULL,
    checkout_date DATE NOT NULL,
    total_nights INTEGER NOT NULL,
    price_per_night DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    guest_name VARCHAR(255) NOT NULL,
    guest_email VARCHAR(255) NOT NULL,
    guest_phone VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending', -- pending, confirmed, cancelled, completed
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, paid, refunded
    booking_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_listing_availability_listing_id ON listing_availability(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_availability_date ON listing_availability(date);
CREATE INDEX IF NOT EXISTS idx_listing_availability_available ON listing_availability(is_available) WHERE is_available = TRUE;
CREATE INDEX IF NOT EXISTS idx_listing_availability_listing_date ON listing_availability(listing_id, date);

CREATE INDEX IF NOT EXISTS idx_listing_bookings_listing_id ON listing_bookings(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_guest_user_id ON listing_bookings(guest_user_id);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_host_user_id ON listing_bookings(host_user_id);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_checkin ON listing_bookings(checkin_date);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_checkout ON listing_bookings(checkout_date);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_status ON listing_bookings(status);
CREATE INDEX IF NOT EXISTS idx_listing_bookings_dates ON listing_bookings(listing_id, checkin_date, checkout_date);

-- Comentários para documentação
COMMENT ON TABLE listing_availability IS 'Tabela para controlar disponibilidade de datas por anúncio';
COMMENT ON TABLE listing_bookings IS 'Tabela para armazenar reservas feitas por hóspedes';

COMMENT ON COLUMN listing_availability.is_available IS 'TRUE = disponível para reserva, FALSE = bloqueado';
COMMENT ON COLUMN listing_availability.price_per_night IS 'Preço específico para esta data (sobrescreve preço padrão do anúncio)';
COMMENT ON COLUMN listing_bookings.status IS 'Status da reserva: pending, confirmed, cancelled, completed';
COMMENT ON COLUMN listing_bookings.payment_status IS 'Status do pagamento: pending, paid, refunded';

-- Mensagem de confirmação
SELECT 'Tabelas de agenda criadas com sucesso!' as message;