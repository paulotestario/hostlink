-- ==========================================
-- SCRIPT PARA CRIAR TABELA DE AVALIACOES
-- Execute este SQL no painel do Supabase
-- ==========================================

-- Criar tabela de avaliacoes de hospedagem
CREATE TABLE IF NOT EXISTS accommodation_reviews (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    guest_user_id INTEGER NOT NULL,
    host_user_id INTEGER,
    
    -- Avaliacoes por categoria (1-5 estrelas)
    overall_rating INTEGER NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
    cleanliness_rating INTEGER NOT NULL CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
    communication_rating INTEGER NOT NULL CHECK (communication_rating >= 1 AND communication_rating <= 5),
    checkin_rating INTEGER NOT NULL CHECK (checkin_rating >= 1 AND checkin_rating <= 5),
    accuracy_rating INTEGER NOT NULL CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    location_rating INTEGER NOT NULL CHECK (location_rating >= 1 AND location_rating <= 5),
    value_rating INTEGER NOT NULL CHECK (value_rating >= 1 AND value_rating <= 5),
    
    -- Conteudo da avaliacao
    review_title VARCHAR(255),
    review_comment TEXT,
    
    -- Flags
    would_recommend BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT true,
    is_approved BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint para garantir uma avaliacao por reserva
    UNIQUE(booking_id)
);

-- Criar indices para performance
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_listing_id ON accommodation_reviews(listing_id);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_guest_user_id ON accommodation_reviews(guest_user_id);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_host_user_id ON accommodation_reviews(host_user_id);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_created_at ON accommodation_reviews(created_at);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_is_public ON accommodation_reviews(is_public);
CREATE INDEX IF NOT EXISTS idx_accommodation_reviews_is_approved ON accommodation_reviews(is_approved);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_accommodation_reviews_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_accommodation_reviews_updated_at
    BEFORE UPDATE ON accommodation_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_accommodation_reviews_updated_at();

-- Comentarios para documentacao
COMMENT ON TABLE accommodation_reviews IS 'Tabela para armazenar avaliacoes de hospedagens feitas pelos hospedes';
COMMENT ON COLUMN accommodation_reviews.booking_id IS 'ID da reserva sendo avaliada';
COMMENT ON COLUMN accommodation_reviews.listing_id IS 'ID do anuncio/hospedagem';
COMMENT ON COLUMN accommodation_reviews.guest_user_id IS 'ID do usuario hospede que fez a avaliacao';
COMMENT ON COLUMN accommodation_reviews.host_user_id IS 'ID do usuario anfitriao';
COMMENT ON COLUMN accommodation_reviews.overall_rating IS 'Avaliacao geral (1-5 estrelas)';
COMMENT ON COLUMN accommodation_reviews.cleanliness_rating IS 'Avaliacao de limpeza (1-5 estrelas)';
COMMENT ON COLUMN accommodation_reviews.communication_rating IS 'Avaliacao de comunicacao (1-5 estrelas)';
COMMENT ON COLUMN accommodation_reviews.checkin_rating IS 'Avaliacao do check-in (1-5 estrelas)';
COMMENT ON COLUMN accommodation_reviews.accuracy_rating IS 'Avaliacao da precisao do anuncio (1-5 estrelas)';
COMMENT ON COLUMN accommodation_reviews.location_rating IS 'Avaliacao da localizacao (1-5 estrelas)';
COMMENT ON COLUMN accommodation_reviews.value_rating IS 'Avaliacao do custo-beneficio (1-5 estrelas)';
COMMENT ON COLUMN accommodation_reviews.would_recommend IS 'Se o hospede recomendaria a hospedagem';
COMMENT ON COLUMN accommodation_reviews.is_public IS 'Se a avaliacao e publica';
COMMENT ON COLUMN accommodation_reviews.is_approved IS 'Se a avaliacao foi aprovada pelo moderador';

-- Verificar se a tabela foi criada com sucesso
SELECT 'Tabela accommodation_reviews criada com sucesso!' as status;

-- Mostrar estrutura da tabela
\d accommodation_reviews;