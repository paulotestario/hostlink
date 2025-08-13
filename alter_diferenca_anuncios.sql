-- =====================================================
-- SCRIPT ALTER TABLE - APENAS AS DIFERENÇAS
-- Colunas que estão faltando na tabela user_listings atual
-- =====================================================

-- ESTRUTURA ATUAL DA TABELA user_listings:
/*
COLUNAS EXISTENTES:
- id SERIAL PRIMARY KEY
- user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
- title VARCHAR(255) NOT NULL
- url TEXT NOT NULL
- platform VARCHAR(50) DEFAULT 'airbnb'
- municipio_id INTEGER REFERENCES municipios(id)
- property_type VARCHAR(100)
- max_guests INTEGER
- bedrooms INTEGER
- bathrooms INTEGER
- is_active BOOLEAN DEFAULT TRUE
- created_at TIMESTAMP DEFAULT NOW()
- updated_at TIMESTAMP DEFAULT NOW()
*/

-- =====================================================
-- COLUNAS QUE PRECISAM SER ADICIONADAS:
-- =====================================================

-- 1. PREÇO E AVALIAÇÃO (extraídos do scraper)
ALTER TABLE user_listings ADD COLUMN price_per_night DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN rating DECIMAL(3,2);
ALTER TABLE user_listings ADD COLUMN reviews INTEGER DEFAULT 0;

-- 2. LOCALIZAÇÃO DETALHADA
ALTER TABLE user_listings ADD COLUMN address TEXT;
ALTER TABLE user_listings ADD COLUMN latitude DECIMAL(10,8);
ALTER TABLE user_listings ADD COLUMN longitude DECIMAL(11,8);

-- 3. CONTEÚDO E MÍDIA
ALTER TABLE user_listings ADD COLUMN description TEXT;
ALTER TABLE user_listings ADD COLUMN amenities JSONB; -- Lista de comodidades
ALTER TABLE user_listings ADD COLUMN image_url TEXT;

-- 4. CARACTERÍSTICAS ESPECÍFICAS DO AIRBNB
ALTER TABLE user_listings ADD COLUMN is_beachfront BOOLEAN DEFAULT FALSE;
ALTER TABLE user_listings ADD COLUMN beach_confidence DECIMAL(3,2) DEFAULT 0;
ALTER TABLE user_listings ADD COLUMN instant_book BOOLEAN DEFAULT FALSE;
ALTER TABLE user_listings ADD COLUMN superhost BOOLEAN DEFAULT FALSE;

-- 5. ESTRUTURA DE PREÇOS DETALHADA
ALTER TABLE user_listings ADD COLUMN cleaning_fee DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN service_fee DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN total_price DECIMAL(10,2);

-- 6. REGRAS DE HOSPEDAGEM
ALTER TABLE user_listings ADD COLUMN minimum_nights INTEGER DEFAULT 1;
ALTER TABLE user_listings ADD COLUMN maximum_nights INTEGER;
ALTER TABLE user_listings ADD COLUMN availability_365 INTEGER;

-- 7. DADOS DO ANFITRIÃO
ALTER TABLE user_listings ADD COLUMN host_name VARCHAR(255);
ALTER TABLE user_listings ADD COLUMN host_id VARCHAR(50);
ALTER TABLE user_listings ADD COLUMN host_response_rate INTEGER;
ALTER TABLE user_listings ADD COLUMN host_response_time VARCHAR(50);

-- 8. CONTROLE DE QUALIDADE E ATUALIZAÇÃO
ALTER TABLE user_listings ADD COLUMN last_scraped TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_listings ADD COLUMN extraction_method VARCHAR(100);
ALTER TABLE user_listings ADD COLUMN data_quality_score DECIMAL(3,2);

-- =====================================================
-- ÍNDICES PARA AS NOVAS COLUNAS
-- =====================================================

-- Índices para consultas de preço e avaliação
CREATE INDEX idx_user_listings_price_range ON user_listings(price_per_night) WHERE price_per_night IS NOT NULL;
CREATE INDEX idx_user_listings_rating_high ON user_listings(rating) WHERE rating >= 4.0;
CREATE INDEX idx_user_listings_reviews_count ON user_listings(reviews) WHERE reviews > 0;

-- Índices para localização
CREATE INDEX idx_user_listings_coordinates ON user_listings(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Índices para características especiais
CREATE INDEX idx_user_listings_beachfront_true ON user_listings(is_beachfront) WHERE is_beachfront = TRUE;
CREATE INDEX idx_user_listings_superhost_true ON user_listings(superhost) WHERE superhost = TRUE;
CREATE INDEX idx_user_listings_instant_book_true ON user_listings(instant_book) WHERE instant_book = TRUE;

-- Índice para controle de atualização
CREATE INDEX idx_user_listings_needs_update ON user_listings(last_scraped) WHERE last_scraped < NOW() - INTERVAL '7 days' OR last_scraped IS NULL;

-- Índice composto para análises de mercado
CREATE INDEX idx_user_listings_market_data ON user_listings(municipio_id, property_type, price_per_night, rating) WHERE is_active = TRUE AND price_per_night IS NOT NULL;

-- =====================================================
-- RESUMO DAS DIFERENÇAS
-- =====================================================

/*
TOTAL DE NOVAS COLUNAS: 21

CATEGORIAS:
✅ Preço e Avaliação (3): price_per_night, rating, reviews
✅ Localização (3): address, latitude, longitude  
✅ Conteúdo (3): description, amenities, image_url
✅ Características Airbnb (4): is_beachfront, beach_confidence, instant_book, superhost
✅ Preços Detalhados (3): cleaning_fee, service_fee, total_price
✅ Regras de Hospedagem (3): minimum_nights, maximum_nights, availability_365
✅ Dados do Host (4): host_name, host_id, host_response_rate, host_response_time
✅ Controle de Qualidade (3): last_scraped, extraction_method, data_quality_score

BENEFÍCIOS:
- Armazenar dados completos extraídos pelo scraper
- Análises de mercado mais precisas
- Filtros avançados por características
- Controle de qualidade dos dados
- Monitoramento de atualizações necessárias
*/

-- =====================================================
-- VERIFICAÇÃO APÓS EXECUÇÃO
-- =====================================================

-- Para verificar se todas as colunas foram adicionadas:
/*
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'user_listings' 
  AND column_name NOT IN (
    'id', 'user_id', 'title', 'url', 'platform', 'municipio_id', 
    'property_type', 'max_guests', 'bedrooms', 'bathrooms', 
    'is_active', 'created_at', 'updated_at'
  )
ORDER BY ordinal_position;
*/

-- Para contar o total de colunas:
/*
SELECT COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'user_listings';
-- Deve retornar 34 colunas (13 originais + 21 novas)
*/