-- Script para recriar todas as tabelas do sistema HostLink
-- Execute este script no editor SQL do Supabase

-- Primeiro, remover todas as tabelas existentes (em ordem para respeitar as foreign keys)
DROP TABLE IF EXISTS pricing_history CASCADE;
DROP TABLE IF EXISTS competitors CASCADE;
DROP TABLE IF EXISTS weather_data CASCADE;
DROP TABLE IF EXISTS analyses CASCADE;
DROP TABLE IF EXISTS user_listings CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS municipios CASCADE;

-- Recriar todas as tabelas

-- Tabela de municípios (deve ser criada primeiro pois é referenciada por outras tabelas)
CREATE TABLE municipios (
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

-- Tabela de usuários
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    profile_pic TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de links de anúncios do usuário
CREATE TABLE user_listings (
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

-- Tabela principal de análises
CREATE TABLE analyses (
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

-- Tabela de dados climáticos
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    rain_probability INTEGER,
    weather_condition VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de concorrentes
CREATE TABLE competitors (
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

-- Tabela de histórico de preços
CREATE TABLE pricing_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    suggested_price DECIMAL(10,2),
    market_average DECIMAL(10,2),
    weather_factor DECIMAL(3,2),
    weekend_factor DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Criar todos os índices para performance
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_listings_user_id ON user_listings(user_id);
CREATE INDEX idx_user_listings_municipio_id ON user_listings(municipio_id);
CREATE INDEX idx_user_listings_is_active ON user_listings(is_active);
CREATE INDEX idx_municipios_nome ON municipios(nome);
CREATE INDEX idx_municipios_estado ON municipios(estado);
CREATE INDEX idx_municipios_codigo_ibge ON municipios(codigo_ibge);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_listing_id ON analyses(listing_id);
CREATE INDEX idx_analyses_municipio_id ON analyses(municipio_id);
CREATE INDEX idx_analyses_checkin ON analyses(checkin);
CREATE INDEX idx_analyses_timestamp ON analyses(timestamp);
CREATE INDEX idx_weather_analysis_id ON weather_data(analysis_id);
CREATE INDEX idx_competitors_analysis_id ON competitors(analysis_id);
CREATE INDEX idx_pricing_history_date ON pricing_history(date);

-- Mensagem de confirmação
SELECT 'Todas as tabelas foram recriadas com sucesso!' as status;