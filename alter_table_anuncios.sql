-- =====================================================
-- ALTER TABLE para adicionar colunas faltantes na tabela user_listings
-- =====================================================

-- Adicionar colunas de preço e avaliação
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS price_per_night DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS rating DECIMAL(3,2);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS reviews INTEGER DEFAULT 0;

-- Adicionar colunas de localização
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,8);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS longitude DECIMAL(11,8);

-- Adicionar colunas de descrição e características
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS amenities TEXT; -- JSON ou lista de comodidades
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Adicionar colunas de características específicas
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS is_beachfront BOOLEAN DEFAULT FALSE;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS beach_confidence DECIMAL(3,2) DEFAULT 0;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS instant_book BOOLEAN DEFAULT FALSE;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS superhost BOOLEAN DEFAULT FALSE;

-- Adicionar colunas de preços e taxas
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS cleaning_fee DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS service_fee DECIMAL(10,2);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS total_price DECIMAL(10,2);

-- Adicionar colunas de disponibilidade
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS minimum_nights INTEGER DEFAULT 1;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS maximum_nights INTEGER;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS availability_365 INTEGER;

-- Adicionar colunas de host
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS host_name VARCHAR(255);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS host_id VARCHAR(50);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS host_response_rate INTEGER;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS host_response_time VARCHAR(50);

-- Adicionar colunas de metadados
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS last_scraped TIMESTAMP;
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(100);
ALTER TABLE user_listings ADD COLUMN IF NOT EXISTS data_quality_score DECIMAL(3,2);

-- Adicionar índices para as novas colunas mais consultadas
CREATE INDEX IF NOT EXISTS idx_user_listings_price ON user_listings(price_per_night);
CREATE INDEX IF NOT EXISTS idx_user_listings_rating ON user_listings(rating);
CREATE INDEX IF NOT EXISTS idx_user_listings_beachfront ON user_listings(is_beachfront);
CREATE INDEX IF NOT EXISTS idx_user_listings_location ON user_listings(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_user_listings_last_scraped ON user_listings(last_scraped);

-- =====================================================
-- COMENTÁRIOS SOBRE AS NOVAS COLUNAS
-- =====================================================

/*
NOVAS COLUNAS ADICIONADAS:

1. PREÇO E AVALIAÇÃO:
   - price_per_night: Preço por noite extraído do Airbnb
   - rating: Avaliação média do anúncio
   - reviews: Número de avaliações

2. LOCALIZAÇÃO:
   - address: Endereço completo do anúncio
   - latitude/longitude: Coordenadas geográficas

3. DESCRIÇÃO E CARACTERÍSTICAS:
   - description: Descrição completa do anúncio
   - amenities: Lista de comodidades (JSON)
   - image_url: URL da imagem principal

4. CARACTERÍSTICAS ESPECÍFICAS:
   - is_beachfront: Se é frente à praia
   - beach_confidence: Confiança na detecção de praia (0-1)
   - instant_book: Se permite reserva instantânea
   - superhost: Se o host é superhost

5. PREÇOS E TAXAS:
   - cleaning_fee: Taxa de limpeza
   - service_fee: Taxa de serviço
   - total_price: Preço total calculado

6. DISPONIBILIDADE:
   - minimum_nights: Mínimo de noites
   - maximum_nights: Máximo de noites
   - availability_365: Dias disponíveis no ano

7. INFORMAÇÕES DO HOST:
   - host_name: Nome do anfitrião
   - host_id: ID do anfitrião
   - host_response_rate: Taxa de resposta (%)
   - host_response_time: Tempo de resposta

8. METADADOS:
   - last_scraped: Última vez que os dados foram extraídos
   - extraction_method: Método usado para extrair os dados
   - data_quality_score: Pontuação da qualidade dos dados (0-1)

ESSAS COLUNAS PERMITEM:
- Armazenar todos os dados extraídos pelo scraper
- Fazer análises mais detalhadas de preços e localização
- Implementar filtros avançados por características
- Monitorar a qualidade e atualização dos dados
- Análises de mercado mais precisas
*/