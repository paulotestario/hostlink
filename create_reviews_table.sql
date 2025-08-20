-- =====================================================
-- TABELA DE AVALIACOES DE HOSPEDAGEM
-- =====================================================

-- Criar tabela de avaliacoes de hospedagem
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
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_booking_id ON accommodation_reviews(booking_id);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_listing_id ON accommodation_reviews(listing_id);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_guest_user_id ON accommodation_reviews(guest_user_id);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_host_user_id ON accommodation_reviews(host_user_id);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_overall_rating ON accommodation_reviews(overall_rating);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_public ON accommodation_reviews(is_public) WHERE is_public = TRUE;
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_approved ON accommodation_reviews(is_approved) WHERE is_approved = TRUE;
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_created_at ON accommodation_reviews(created_at);

-- Constraint para garantir que so existe uma avaliacao por reserva
ALTER TABLE accommodation_reviews ADD CONSTRAINT unique_review_per_booking UNIQUE (booking_id);

-- Comentarios para documentacao
COMMENT ON TABLE accommodation_reviews IS 'Tabela para armazenar avaliacoes de hospedagem feitas pelos hospedes';
COMMENT ON COLUMN accommodation_reviews.overall_rating IS 'Avaliacao geral de 1 a 5 estrelas';
COMMENT ON COLUMN accommodation_reviews.cleanliness_rating IS 'Avaliacao da limpeza de 1 a 5 estrelas';
COMMENT ON COLUMN accommodation_reviews.communication_rating IS 'Avaliacao da comunicacao de 1 a 5 estrelas';
COMMENT ON COLUMN accommodation_reviews.checkin_rating IS 'Avaliacao do check-in de 1 a 5 estrelas';
COMMENT ON COLUMN accommodation_reviews.accuracy_rating IS 'Avaliacao da precisao do anuncio de 1 a 5 estrelas';
COMMENT ON COLUMN accommodation_reviews.location_rating IS 'Avaliacao da localizacao de 1 a 5 estrelas';
COMMENT ON COLUMN accommodation_reviews.value_rating IS 'Avaliacao do custo-beneficio de 1 a 5 estrelas';
COMMENT ON COLUMN accommodation_reviews.would_recommend IS 'Se o hospede recomendaria a hospedagem';
COMMENT ON COLUMN accommodation_reviews.is_public IS 'Se a avaliacao e publica';
COMMENT ON COLUMN accommodation_reviews.is_approved IS 'Se a avaliacao foi aprovada pelo administrador';