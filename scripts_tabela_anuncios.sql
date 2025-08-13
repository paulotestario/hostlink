-- =====================================================
-- SCRIPTS PARA TABELA DE ANÚNCIOS (user_listings)
-- =====================================================

-- =====================================================
-- 1. SCRIPTS DE DELETE (ORDEM CORRETA DEVIDO ÀS FOREIGN KEYS)
-- =====================================================

-- Primeiro: Deletar tabelas que referenciam user_listings
DROP TABLE IF EXISTS analyses CASCADE;
DROP TABLE IF EXISTS weather_data CASCADE;
DROP TABLE IF EXISTS competitors CASCADE;

-- Segundo: Deletar a tabela principal de anúncios
DROP TABLE IF EXISTS user_listings CASCADE;

-- Terceiro: Deletar tabelas relacionadas (se necessário)
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS municipios CASCADE;
DROP TABLE IF EXISTS pricing_history CASCADE;

-- =====================================================
-- 2. SCRIPTS DE CREATE (ORDEM CORRETA DEVIDO ÀS DEPENDÊNCIAS)
-- =====================================================

-- Primeiro: Criar tabelas base (sem dependências)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    profile_pic TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    estado VARCHAR(2) NOT NULL,
    regiao VARCHAR(20) NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    populacao INTEGER,
    codigo_ibge VARCHAR(7) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Segundo: Criar tabela de anúncios (depende de users e municipios)
CREATE TABLE IF NOT EXISTS user_listings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    platform VARCHAR(50) DEFAULT 'airbnb',
    municipio_id INTEGER REFERENCES municipios(id),
    property_type VARCHAR(100),
    max_guests INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Terceiro: Criar tabelas que dependem de user_listings
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    listing_id INTEGER REFERENCES user_listings(id),
    municipio_id INTEGER REFERENCES municipios(id),
    checkin DATE NOT NULL,
    checkout DATE NOT NULL,
    adults INTEGER DEFAULT 2,
    beachfront BOOLEAN DEFAULT FALSE,
    suggested_price DECIMAL(10,2),
    price_multiplier DECIMAL(3,2),
    justification TEXT,
    discount_percentage DECIMAL(5,2),
    average_competitor_price DECIMAL(10,2),
    period_type VARCHAR(50),
    is_weekend BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    rain_probability INTEGER,
    weather_condition VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    title VARCHAR(255),
    price DECIMAL(10,2),
    rating DECIMAL(3,2),
    reviews INTEGER,
    distance VARCHAR(50),
    url TEXT,
    is_beachfront BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pricing_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    suggested_price DECIMAL(10,2),
    market_average DECIMAL(10,2),
    weather_factor DECIMAL(3,2),
    weekend_factor DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 3. ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices para users
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Índices para user_listings (TABELA PRINCIPAL DE ANÚNCIOS)
CREATE INDEX IF NOT EXISTS idx_user_listings_user_id ON user_listings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_listings_municipio_id ON user_listings(municipio_id);
CREATE INDEX IF NOT EXISTS idx_user_listings_is_active ON user_listings(is_active);
CREATE INDEX IF NOT EXISTS idx_user_listings_platform ON user_listings(platform);
CREATE INDEX IF NOT EXISTS idx_user_listings_created_at ON user_listings(created_at);

-- Índices para municipios
CREATE INDEX IF NOT EXISTS idx_municipios_nome ON municipios(nome);
CREATE INDEX IF NOT EXISTS idx_municipios_estado ON municipios(estado);
CREATE INDEX IF NOT EXISTS idx_municipios_codigo_ibge ON municipios(codigo_ibge);

-- Índices para analyses
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_listing_id ON analyses(listing_id);
CREATE INDEX IF NOT EXISTS idx_analyses_municipio_id ON analyses(municipio_id);
CREATE INDEX IF NOT EXISTS idx_analyses_checkin ON analyses(checkin);
CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses(timestamp);

-- Índices para weather_data
CREATE INDEX IF NOT EXISTS idx_weather_analysis_id ON weather_data(analysis_id);

-- Índices para competitors
CREATE INDEX IF NOT EXISTS idx_competitors_analysis_id ON competitors(analysis_id);

-- Índices para pricing_history
CREATE INDEX IF NOT EXISTS idx_pricing_history_date ON pricing_history(date);

-- =====================================================
-- 4. COMENTÁRIOS SOBRE AS RELAÇÕES
-- =====================================================

/*
RELAÇÕES DA TABELA user_listings:

1. user_listings.user_id → users.id
   - Cada anúncio pertence a um usuário
   - ON DELETE CASCADE: Se o usuário for deletado, seus anúncios também são deletados

2. user_listings.municipio_id → municipios.id
   - Cada anúncio está localizado em um município
   - Relação opcional (pode ser NULL)

3. analyses.listing_id → user_listings.id
   - Cada análise pode estar associada a um anúncio específico do usuário
   - Relação opcional (pode ser NULL para análises gerais)

ORDEM DE EXCLUSÃO (para evitar erros de foreign key):
1. weather_data (depende de analyses)
2. competitors (depende de analyses)
3. analyses (depende de user_listings)
4. user_listings (depende de users e municipios)
5. users, municipios, pricing_history (tabelas base)

ORDEM DE CRIAÇÃO:
1. users, municipios, pricing_history (tabelas base)
2. user_listings (depende de users e municipios)
3. analyses (depende de user_listings)
4. weather_data, competitors (dependem de analyses)
*/