-- =====================================================
-- ALTER TABLE para Supabase/PostgreSQL - user_listings
-- Execute estes comandos no SQL Editor do Supabase
-- =====================================================

-- IMPORTANTE: Execute um comando por vez no Supabase

-- 1. Colunas de preço e avaliação
ALTER TABLE user_listings ADD COLUMN price_per_night DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN rating DECIMAL(3,2);
ALTER TABLE user_listings ADD COLUMN reviews INTEGER DEFAULT 0;

-- 2. Colunas de localização
ALTER TABLE user_listings ADD COLUMN address TEXT;
ALTER TABLE user_listings ADD COLUMN latitude DECIMAL(10,8);
ALTER TABLE user_listings ADD COLUMN longitude DECIMAL(11,8);

-- 3. Colunas de descrição e características
ALTER TABLE user_listings ADD COLUMN description TEXT;
ALTER TABLE user_listings ADD COLUMN amenities JSONB; -- Usar JSONB no PostgreSQL
ALTER TABLE user_listings ADD COLUMN image_url TEXT;

-- 4. Características específicas do Airbnb
ALTER TABLE user_listings ADD COLUMN is_beachfront BOOLEAN DEFAULT FALSE;
ALTER TABLE user_listings ADD COLUMN beach_confidence DECIMAL(3,2) DEFAULT 0;
ALTER TABLE user_listings ADD COLUMN instant_book BOOLEAN DEFAULT FALSE;
ALTER TABLE user_listings ADD COLUMN superhost BOOLEAN DEFAULT FALSE;

-- 5. Preços e taxas detalhados
ALTER TABLE user_listings ADD COLUMN cleaning_fee DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN service_fee DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN total_price DECIMAL(10,2);

-- 6. Regras de disponibilidade
ALTER TABLE user_listings ADD COLUMN minimum_nights INTEGER DEFAULT 1;
ALTER TABLE user_listings ADD COLUMN maximum_nights INTEGER;
ALTER TABLE user_listings ADD COLUMN availability_365 INTEGER;

-- 7. Informações do anfitrião
ALTER TABLE user_listings ADD COLUMN host_name VARCHAR(255);
ALTER TABLE user_listings ADD COLUMN host_id VARCHAR(50);
ALTER TABLE user_listings ADD COLUMN host_response_rate INTEGER;
ALTER TABLE user_listings ADD COLUMN host_response_time VARCHAR(50);

-- 8. Metadados de extração
ALTER TABLE user_listings ADD COLUMN last_scraped TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_listings ADD COLUMN extraction_method VARCHAR(100);
ALTER TABLE user_listings ADD COLUMN data_quality_score DECIMAL(3,2);

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices para consultas de preço
CREATE INDEX idx_user_listings_price ON user_listings(price_per_night) WHERE price_per_night IS NOT NULL;
CREATE INDEX idx_user_listings_rating ON user_listings(rating) WHERE rating IS NOT NULL;

-- Índices para localização (útil para buscas geográficas)
CREATE INDEX idx_user_listings_location ON user_listings(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Índices para características específicas
CREATE INDEX idx_user_listings_beachfront ON user_listings(is_beachfront) WHERE is_beachfront = TRUE;
CREATE INDEX idx_user_listings_superhost ON user_listings(superhost) WHERE superhost = TRUE;
CREATE INDEX idx_user_listings_instant_book ON user_listings(instant_book) WHERE instant_book = TRUE;

-- Índice para controle de atualização
CREATE INDEX idx_user_listings_last_scraped ON user_listings(last_scraped) WHERE last_scraped IS NOT NULL;

-- Índice composto para análises de mercado
CREATE INDEX idx_user_listings_market_analysis ON user_listings(municipio_id, property_type, price_per_night) WHERE is_active = TRUE;

-- =====================================================
-- VERIFICAÇÃO DAS ALTERAÇÕES
-- =====================================================

-- Para verificar se as colunas foram adicionadas corretamente:
/*
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'user_listings' 
ORDER BY ordinal_position;
*/

-- Para verificar os índices criados:
/*
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'user_listings'
ORDER BY indexname;
*/

-- =====================================================
-- EXEMPLO DE USO DAS NOVAS COLUNAS
-- =====================================================

/*
-- Buscar anúncios frente à praia com boa avaliação
SELECT title, price_per_night, rating, reviews
FROM user_listings 
WHERE is_beachfront = TRUE 
  AND rating >= 4.5 
  AND reviews >= 10
  AND is_active = TRUE
ORDER BY rating DESC, reviews DESC;

-- Buscar anúncios por faixa de preço em uma região
SELECT ul.title, ul.price_per_night, m.nome as municipio
FROM user_listings ul
JOIN municipios m ON ul.municipio_id = m.id
WHERE ul.price_per_night BETWEEN 200 AND 500
  AND m.estado = 'RJ'
  AND ul.is_active = TRUE
ORDER BY ul.price_per_night;

-- Anúncios que precisam de atualização de dados
SELECT title, url, last_scraped
FROM user_listings
WHERE last_scraped < NOW() - INTERVAL '7 days'
   OR last_scraped IS NULL
ORDER BY last_scraped NULLS FIRST;
*/