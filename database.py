#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Banco de Dados - Integração com Supabase
Gerencia todas as operações de banco de dados do HostLink
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class HostLinkDatabase:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Credenciais do Supabase não configuradas. Verifique o arquivo .env")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def create_tables(self):
        """
        Cria as tabelas necessárias no Supabase (via SQL)
        Execute este SQL no editor do Supabase:
        """
        sql_script = """
        -- Tabela de usuários
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            google_id VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            profile_pic TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Tabela de links de anúncios do usuário
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
        
        -- Tabela de municípios
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
        
        -- Tabela principal de análises
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
        
        -- Tabela de dados climáticos
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            rain_probability INTEGER,
            weather_condition VARCHAR(100),
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Tabela de concorrentes
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
        
        -- Tabela de histórico de preços
        CREATE TABLE IF NOT EXISTS pricing_history (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            suggested_price DECIMAL(10,2),
            market_average DECIMAL(10,2),
            weather_factor DECIMAL(3,2),
            weekend_factor DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Índices para performance
        CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_user_listings_user_id ON user_listings(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_listings_municipio_id ON user_listings(municipio_id);
        CREATE INDEX IF NOT EXISTS idx_user_listings_is_active ON user_listings(is_active);
        CREATE INDEX IF NOT EXISTS idx_municipios_nome ON municipios(nome);
        CREATE INDEX IF NOT EXISTS idx_municipios_estado ON municipios(estado);
        CREATE INDEX IF NOT EXISTS idx_municipios_codigo_ibge ON municipios(codigo_ibge);
        CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
        CREATE INDEX IF NOT EXISTS idx_analyses_listing_id ON analyses(listing_id);
        CREATE INDEX IF NOT EXISTS idx_analyses_municipio_id ON analyses(municipio_id);
        CREATE INDEX IF NOT EXISTS idx_analyses_checkin ON analyses(checkin);
        CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses(timestamp);
        CREATE INDEX IF NOT EXISTS idx_weather_analysis_id ON weather_data(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_competitors_analysis_id ON competitors(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_pricing_history_date ON pricing_history(date);
        """
        return sql_script
    
    def save_analysis(self, analysis_data: Dict, user_id: int = None, listing_id: int = None) -> int:
        """
        Salva uma análise completa no banco de dados
        """
        try:
            # Inserir análise principal
            pricing = analysis_data.get('pricing_suggestion', {})
            
            analysis_record = {
                'user_id': user_id,
                'listing_id': listing_id,
                'municipio_id': analysis_data.get('municipio_id'),
                'checkin': analysis_data.get('checkin'),
                'checkout': analysis_data.get('checkout'),
                'adults': analysis_data.get('adults', 2),
                'beachfront': analysis_data.get('beachfront', False),
                'suggested_price': pricing.get('suggested_price'),
                'price_multiplier': pricing.get('price_multiplier'),
                'justification': pricing.get('justification'),
                'discount_percentage': pricing.get('discount_percentage'),
                'average_competitor_price': pricing.get('average_competitor_price'),
                'period_type': analysis_data.get('period_type'),
                'is_weekend': analysis_data.get('is_weekend'),
                'timestamp': analysis_data.get('timestamp', datetime.now().isoformat())
            }
            
            result = self.supabase.table('analyses').insert(analysis_record).execute()
            analysis_id = result.data[0]['id']
            
            # Salvar dados climáticos
            weather_data = analysis_data.get('weather_data', [])
            for weather in weather_data:
                weather_record = {
                    'analysis_id': analysis_id,
                    'date': weather.get('date'),
                    'rain_probability': weather.get('rain_probability'),
                    'weather_condition': weather.get('weather_condition'),
                    'description': weather.get('description')
                }
                self.supabase.table('weather_data').insert(weather_record).execute()
            
            # Salvar dados de concorrentes
            competitive_data = analysis_data.get('competitive_data', [])
            for competitor in competitive_data:
                competitor_record = {
                    'analysis_id': analysis_id,
                    'title': competitor.get('title'),
                    'price': competitor.get('price'),
                    'rating': competitor.get('rating'),
                    'reviews': competitor.get('reviews'),
                    'distance': competitor.get('distance'),
                    'url': competitor.get('url'),
                    'is_beachfront': competitor.get('is_beachfront', False)
                }
                self.supabase.table('competitors').insert(competitor_record).execute()
            
            return analysis_id
            
        except Exception as e:
            print(f"Erro ao salvar análise: {e}")
            return None
    
    def get_latest_analysis(self) -> Optional[Dict]:
        """
        Recupera a análise mais recente
        """
        try:
            result = self.supabase.table('analyses').select('*').order('timestamp', desc=True).limit(1).execute()
            
            if not result.data:
                return None
            
            analysis = result.data[0]
            analysis_id = analysis['id']
            
            # Buscar dados climáticos
            weather_result = self.supabase.table('weather_data').select('*').eq('analysis_id', analysis_id).execute()
            
            # Buscar dados de concorrentes
            competitors_result = self.supabase.table('competitors').select('*').eq('analysis_id', analysis_id).execute()
            
            # Montar objeto completo
            complete_analysis = {
                'id': analysis['id'],
                'checkin': analysis['checkin'],
                'checkout': analysis['checkout'],
                'adults': analysis['adults'],
                'beachfront': analysis['beachfront'],
                'period_type': analysis['period_type'],
                'is_weekend': analysis['is_weekend'],
                'timestamp': analysis['timestamp'],
                'pricing_suggestion': {
                    'suggested_price': float(analysis['suggested_price']) if analysis['suggested_price'] else 0,
                    'price_multiplier': float(analysis['price_multiplier']) if analysis['price_multiplier'] else 1.0,
                    'justification': analysis['justification'] or '',
                    'discount_percentage': analysis['discount_percentage'] or 0,
                    'average_competitor_price': float(analysis['average_competitor_price']) if analysis['average_competitor_price'] else 0
                },
                'weather_data': weather_result.data,
                'competitive_data': competitors_result.data
            }
            
            return complete_analysis
            
        except Exception as e:
            print(f"Erro ao recuperar análise: {e}")
            return None
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict]:
        """
        Recupera o histórico de análises
        """
        try:
            result = self.supabase.table('analyses').select('*').order('timestamp', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"Erro ao recuperar histórico: {e}")
            return []
    
    def get_last_pricing_history(self) -> Optional[Dict]:
        """
        Recupera o último registro de histórico de preços
        """
        try:
            result = self.supabase.table('pricing_history').select('*').order('created_at', desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erro ao recuperar último histórico de preços: {e}")
            return None
    
    def save_pricing_history(self, date: str, suggested_price: float, market_average: float, 
                           weather_factor: float = 1.0, weekend_factor: float = 1.0):
        """
        Salva histórico de preços para análise de tendências
        Só salva se o preço for diferente do último preço salvo
        """
        try:
            # Verificar último preço salvo
            last_record = self.get_last_pricing_history()
            
            # Se existe um registro anterior, verificar se o preço é diferente
            if last_record:
                last_price = last_record.get('suggested_price', 0)
                # Comparar preços com tolerância de R$ 0.01
                if abs(suggested_price - last_price) < 0.01:
                    print(f"💡 Preço R$ {suggested_price:.2f} igual ao último salvo (R$ {last_price:.2f}), não salvando duplicata")
                    return
            
            record = {
                'date': date,
                'suggested_price': suggested_price,
                'market_average': market_average,
                'weather_factor': weather_factor,
                'weekend_factor': weekend_factor
            }
            self.supabase.table('pricing_history').insert(record).execute()
            print(f"💾 Histórico de preços salvo: R$ {suggested_price:.2f} para {date}")
        except Exception as e:
            print(f"Erro ao salvar histórico de preços: {e}")
    
    def get_pricing_trends(self, days: int = 30) -> List[Dict]:
        """
        Recupera tendências de preços dos últimos N dias
        """
        try:
            result = self.supabase.table('pricing_history').select('*').order('date', desc=True).limit(days).execute()
            return result.data
        except Exception as e:
            print(f"Erro ao recuperar tendências: {e}")
            return []
    
    def save_municipio(self, nome: str, estado: str, regiao: str, 
                      latitude: float = None, longitude: float = None, 
                      populacao: int = None, codigo_ibge: str = None) -> int:
        """
        Salva um novo município no banco de dados
        """
        try:
            municipio_record = {
                'nome': nome,
                'estado': estado,
                'regiao': regiao,
                'latitude': latitude,
                'longitude': longitude,
                'populacao': populacao,
                'codigo_ibge': codigo_ibge
            }
            
            result = self.supabase.table('municipios').insert(municipio_record).execute()
            return result.data[0]['id']
        except Exception as e:
            print(f"Erro ao salvar município: {e}")
            return None
    
    def get_municipio_by_nome(self, nome: str, estado: str = None) -> Optional[Dict]:
        """
        Busca um município pelo nome e opcionalmente pelo estado
        """
        try:
            query = self.supabase.table('municipios').select('*').eq('nome', nome)
            if estado:
                query = query.eq('estado', estado)
            
            result = query.execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erro ao buscar município: {e}")
            return None
    
    def get_municipios_by_estado(self, estado: str) -> List[Dict]:
        """
        Lista todos os municípios de um estado
        """
        try:
            result = self.supabase.table('municipios').select('*').eq('estado', estado).order('nome').execute()
            return result.data
        except Exception as e:
            print(f"Erro ao buscar municípios do estado: {e}")
            return []
    
    def get_all_municipios(self) -> List[Dict]:
        """
        Lista todos os municípios cadastrados
        """
        try:
            result = self.supabase.table('municipios').select('*').order('estado').order('nome').execute()
            return result.data
        except Exception as e:
            print(f"Erro ao buscar todos os municípios: {e}")
            return []
    
    def save_user(self, google_id: str, email: str, name: str, profile_pic: str = None) -> int:
        """
        Salva ou atualiza um usuário no banco de dados
        """
        try:
            # Verifica se o usuário já existe
            existing_user = self.supabase.table('users').select('*').eq('google_id', google_id).execute()
            
            if existing_user.data:
                # Atualiza usuário existente
                result = self.supabase.table('users').update({
                    'email': email,
                    'name': name,
                    'profile_pic': profile_pic,
                    'updated_at': datetime.now().isoformat()
                }).eq('google_id', google_id).execute()
                return existing_user.data[0]['id']
            else:
                # Cria novo usuário
                result = self.supabase.table('users').insert({
                    'google_id': google_id,
                    'email': email,
                    'name': name,
                    'profile_pic': profile_pic
                }).execute()
                return result.data[0]['id']
        except Exception as e:
            print(f"❌ Erro ao salvar usuário: {e}")
            return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict]:
        """
        Busca usuário pelo Google ID
        """
        try:
            result = self.supabase.table('users').select('*').eq('google_id', google_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Erro ao buscar usuário: {e}")
            return None
    
    def save_user_listing(self, user_id: int, title: str, url: str, municipio_id: int = None,
                         platform: str = 'airbnb', property_type: str = None, 
                         max_guests: int = None, bedrooms: int = None, bathrooms: int = None,
                         # Parâmetros extras para compatibilidade (serão ignorados se a coluna não existir)
                         price_per_night: float = None, rating: float = None, reviews: int = None,
                         address: str = None, latitude: float = None, longitude: float = None,
                         description: str = None, amenities: list = None, image_url: str = None,
                         is_beachfront: bool = False, beach_confidence: float = 0,
                         instant_book: bool = False, superhost: bool = False,
                         cleaning_fee: float = None, service_fee: float = None, total_price: float = None,
                         minimum_nights: int = 1, maximum_nights: int = None, availability_365: int = None,
                         host_name: str = None, host_id: str = None, 
                         host_response_rate: int = None, host_response_time: str = None,
                         extraction_method: str = None, data_quality_score: float = None,
                         last_scraped: str = None) -> int:
        """
        Salva um link de anúncio do usuário usando apenas campos que existem na tabela
        """
        try:
            # Usar apenas campos que existem na estrutura básica da tabela
            listing_data = {
                'user_id': user_id,
                'title': title,
                'url': url,
                'platform': platform,
                'municipio_id': municipio_id,
                'property_type': property_type,
                'max_guests': max_guests,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms
            }
            
            # Remover campos None para não sobrescrever valores padrão
            listing_data = {k: v for k, v in listing_data.items() if v is not None}
            
            print(f"🔍 Dados que serão inseridos na tabela user_listings: {listing_data}")
            
            result = self.supabase.table('user_listings').insert(listing_data).execute()
            
            print(f"📊 Resultado da inserção: {result.data}")
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            else:
                print("⚠️ Nenhum dado retornado na inserção")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao salvar link de anúncio: {e}")
            print(f"🔍 Dados que causaram o erro: user_id={user_id}, title={title}, url={url}")
            # Não fazer raise para não quebrar o fluxo da análise
            return None
    
    def extract_and_save_listing(self, user_id: int, url: str, scraper_data: dict = None) -> int:
        """
        Extrai dados completos de um anúncio e salva no banco
        """
        try:
            # Se não tiver dados do scraper, usar valores básicos
            if not scraper_data:
                scraper_data = {}
            
            # Mapear dados do scraper para os parâmetros da função
            listing_params = {
                'user_id': user_id,
                'title': scraper_data.get('title', 'Anúncio sem título'),
                'url': url,
                'platform': 'airbnb' if 'airbnb.com' in url else 'outro',
                
                # Dados básicos
                'property_type': scraper_data.get('property_type'),
                'max_guests': scraper_data.get('max_guests'),
                'bedrooms': scraper_data.get('bedrooms'),
                'bathrooms': scraper_data.get('bathrooms'),
                
                # Preço e avaliação
                'price_per_night': scraper_data.get('price_per_night'),
                'rating': scraper_data.get('rating'),
                'reviews': scraper_data.get('reviews'),
                
                # Localização
                'address': scraper_data.get('address'),
                'latitude': scraper_data.get('latitude'),
                'longitude': scraper_data.get('longitude'),
                
                # Descrição e imagens
                'description': scraper_data.get('description'),
                'amenities': scraper_data.get('amenities'),
                'image_url': scraper_data.get('image_url'),
                
                # Características específicas
                'is_beachfront': scraper_data.get('is_beachfront', False),
                'beach_confidence': scraper_data.get('beach_confidence', 0),
                'instant_book': scraper_data.get('instant_book', False),
                'superhost': scraper_data.get('superhost', False),
                
                # Preços detalhados
                'cleaning_fee': scraper_data.get('cleaning_fee'),
                'service_fee': scraper_data.get('service_fee'),
                'total_price': scraper_data.get('total_price'),
                
                # Disponibilidade
                'minimum_nights': scraper_data.get('minimum_nights', 1),
                'maximum_nights': scraper_data.get('maximum_nights'),
                'availability_365': scraper_data.get('availability_365'),
                
                # Informações do host
                'host_name': scraper_data.get('host_name'),
                'host_id': scraper_data.get('host_id'),
                'host_response_rate': scraper_data.get('host_response_rate'),
                'host_response_time': scraper_data.get('host_response_time'),
                
                # Metadados
                'extraction_method': 'airbnb_scraper' if 'airbnb.com' in url else 'manual',
                'data_quality_score': 0.9 if scraper_data.get('price_per_night') else 0.5
            }
            
            # Buscar município se fornecido
            if scraper_data.get('municipality'):
                municipio = self.get_municipio_by_nome(scraper_data['municipality'], 'RJ')
                if municipio:
                    listing_params['municipio_id'] = municipio['id']
            
            return self.save_user_listing(**listing_params)
            
        except Exception as e:
            print(f"❌ Erro ao extrair e salvar anúncio: {e}")
            raise
    
    def get_user_listings(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """
        Busca todos os links de anúncios de um usuário
        """
        try:
            query = self.supabase.table('user_listings').select('*, municipios(nome, estado)').eq('user_id', user_id)
            if active_only:
                query = query.eq('is_active', True)
            result = query.order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"❌ Erro ao buscar links de anúncios: {e}")
            return []
    
    def update_user_listing(self, listing_id: int, **kwargs) -> bool:
        """
        Atualiza um link de anúncio
        """
        try:
            kwargs['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('user_listings').update(kwargs).eq('id', listing_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao atualizar link de anúncio: {e}")
            return False
    
    def delete_user_listing(self, listing_id: int, user_id: int) -> bool:
        """
        Remove um link de anúncio (soft delete)
        """
        try:
            result = self.supabase.table('user_listings').update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq('id', listing_id).eq('user_id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao remover link de anúncio: {e}")
            return False
    
    def get_user_analyses(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Busca análises de um usuário específico
        """
        try:
            result = self.supabase.table('analyses').select(
                '*, municipios(nome, estado), user_listings(title, url)'
            ).eq('user_id', user_id).order('timestamp', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"❌ Erro ao buscar análises do usuário: {e}")
            return []

    def test_connection(self) -> bool:
        """
        Testa a conexão com o Supabase
        """
        try:
            # Tentar fazer uma consulta simples na API do Supabase
            # Usar uma consulta que não depende de tabelas específicas
            response = self.supabase.auth.get_session()
            print("✅ Conexão com Supabase estabelecida com sucesso!")
            return True
        except Exception as e:
            # Se falhar, tentar uma consulta básica
            try:
                # Tentar acessar informações do projeto
                result = self.supabase.rpc('version').execute()
                print("✅ Conexão com Supabase estabelecida com sucesso!")
                return True
            except Exception as e2:
                print(f"❌ Erro na conexão com Supabase: {e2}")
                return False

# Instância global do banco
db = None

def get_database():
    """
    Retorna a instância do banco de dados
    """
    global db
    if db is None:
        try:
            db = HostLinkDatabase()
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
            return None
    return db