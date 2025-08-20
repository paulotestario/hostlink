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
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Busca usuário pelo email
        """
        try:
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Erro ao buscar usuário por email: {e}")
            return None
    
    def check_email_auth_type(self, email: str) -> Optional[str]:
        """
        Verifica o tipo de autenticação usado por um email
        Retorna 'google', 'email' ou None se não encontrado
        """
        try:
            result = self.supabase.table('users').select('auth_type, google_id').eq('email', email).execute()
            if result.data:
                user = result.data[0]
                # Se tem google_id preenchido, é autenticação Google
                if user.get('google_id'):
                    return 'google'
                # Se tem auth_type definido, usa esse valor
                elif user.get('auth_type'):
                    return user['auth_type']
                # Fallback: se não tem auth_type mas tem google_id, é Google
                else:
                    return 'google' if user.get('google_id') else 'email'
            return None
        except Exception as e:
            print(f"❌ Erro ao verificar tipo de autenticação: {e}")
            return None
    
    def create_email_user(self, email: str, name: str, password_hash: str, verification_token: str) -> int:
        """
        Cria usuário com autenticação por email
        """
        try:
            result = self.supabase.table('users').insert({
                'email': email,
                'name': name,
                'password_hash': password_hash,
                'auth_type': 'email',
                'profile_pic': ''
            }).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"❌ Erro ao criar usuário por email: {e}")
            return None
    
    def authenticate_email_user(self, email: str, password: str) -> Optional[Dict]:
        """
        Autentica usuário por email e senha
        """
        try:
            from werkzeug.security import check_password_hash
            
            # Buscar usuário por email
            result = self.supabase.table('users').select('*').eq('email', email).eq('auth_type', 'email').execute()
            
            if result.data:
                user = result.data[0]
                # Verificar senha
                if check_password_hash(user['password_hash'], password):
                    return user
            
            return None
        except Exception as e:
            print(f"❌ Erro na autenticação por email: {e}")
            return None
    
    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        """
        Atualiza senha do usuário
        """
        try:
            result = self.supabase.table('users').update({
                'password_hash': new_password_hash,
                'reset_token': None,
                'reset_token_expires': None,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Erro ao atualizar senha: {e}")
            return False
    
    def verify_email(self, verification_token: str) -> bool:
        """
        Verifica email do usuário
        """
        try:
            result = self.supabase.table('users').update({
                'email_verified': True,
                'verification_token': None,
                'updated_at': datetime.now().isoformat()
            }).eq('verification_token', verification_token).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Erro ao verificar email: {e}")
            return False
    
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
                         last_scraped: str = None, is_active: bool = True) -> int:
        """
        Salva um link de anúncio do usuário usando apenas campos que existem na tabela
        """
        try:
            # Usar todos os campos que existem na tabela user_listings
            listing_data = {
                'user_id': user_id,
                'title': title,
                'url': url,
                'platform': platform,
                'municipio_id': municipio_id,
                'property_type': property_type,
                'max_guests': max_guests,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'is_active': is_active,
                'price_per_night': price_per_night,
                'rating': rating,
                'reviews': reviews,
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'description': description,
                'amenities': amenities,
                'image_url': image_url,
                'is_beachfront': is_beachfront,
                'beach_confidence': beach_confidence,
                'instant_book': instant_book,
                'superhost': superhost,
                'cleaning_fee': cleaning_fee,
                'service_fee': service_fee,
                'total_price': total_price,
                'minimum_nights': minimum_nights,
                'maximum_nights': maximum_nights,
                'availability_365': availability_365,
                'host_name': host_name,
                'host_id': host_id,
                'host_response_rate': host_response_rate,
                'host_response_time': host_response_time,
                'extraction_method': extraction_method,
                'data_quality_score': data_quality_score,
                'last_scraped': last_scraped
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
    
    # ===== FUNÇÕES DE AGENDA E DISPONIBILIDADE =====
    
    def save_listing_availability(self, listing_id: int, user_id: int, date: str, 
                                is_available: bool = True, price_per_night: float = None,
                                minimum_nights: int = 1, maximum_nights: int = None,
                                notes: str = None) -> bool:
        """
        Salva ou atualiza disponibilidade de uma data específica para um anúncio
        """
        try:
            data = {
                'listing_id': listing_id,
                'user_id': user_id,
                'date': date,
                'is_available': is_available,
                'minimum_nights': minimum_nights,
                'updated_at': datetime.now().isoformat()
            }
            
            if price_per_night is not None:
                data['price_per_night'] = price_per_night
            if maximum_nights is not None:
                data['maximum_nights'] = maximum_nights
            if notes:
                data['notes'] = notes
            
            # Usar upsert para inserir ou atualizar
            result = self.supabase.table('listing_availability').upsert(
                data, on_conflict='listing_id,date'
            ).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao salvar disponibilidade: {e}")
            return False
    
    def get_listing_availability(self, listing_id: int, start_date: str = None, 
                               end_date: str = None) -> List[Dict]:
        """
        Busca disponibilidade de um anúncio em um período
        """
        try:
            query = self.supabase.table('listing_availability').select('*').eq('listing_id', listing_id)
            
            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)
                
            result = query.order('date').execute()
            return result.data
        except Exception as e:
            print(f"❌ Erro ao buscar disponibilidade: {e}")
            return []
    
    def save_booking(self, listing_id: int, guest_user_id: int, host_user_id: int,
                   checkin_date: str, checkout_date: str, total_nights: int,
                   price_per_night: float, total_price: float, guest_name: str,
                   guest_email: str, guest_phone: str = None, booking_notes: str = None) -> int:
        """
        Salva uma nova reserva
        """
        try:
            data = {
                'listing_id': listing_id,
                'guest_user_id': guest_user_id,
                'host_user_id': host_user_id,
                'checkin_date': checkin_date,
                'checkout_date': checkout_date,
                'total_nights': total_nights,
                'price_per_night': price_per_night,
                'total_price': total_price,
                'guest_name': guest_name,
                'guest_email': guest_email,
                'status': 'pending',
                'payment_status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            if guest_phone:
                data['guest_phone'] = guest_phone
            if booking_notes:
                data['booking_notes'] = booking_notes
            
            result = self.supabase.table('listing_bookings').insert(data).execute()
            booking_id = result.data[0]['id'] if result.data else None
            
            # Criar notificação para o host
            if booking_id:
                self.create_booking_notification(booking_id)
            
            return booking_id
        except Exception as e:
            print(f"❌ Erro ao salvar reserva: {e}")
            return None
    
    def get_listing_bookings(self, listing_id: int = None, user_id: int = None, 
                           status: str = None) -> List[Dict]:
        """
        Busca reservas por anúncio, usuário ou status
        """
        try:
            query = self.supabase.table('listing_bookings').select(
                '*, user_listings(title), users!guest_user_id(name, email)'
            )
            
            if listing_id:
                query = query.eq('listing_id', listing_id)
            if user_id:
                query = query.eq('host_user_id', user_id)
            if status:
                query = query.eq('status', status)
                
            result = query.order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"❌ Erro ao buscar reservas: {e}")
            return []
    
    def update_booking_status(self, booking_id: int, status: str, payment_status: str = None) -> bool:
        """
        Atualiza status de uma reserva
        """
        try:
            data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if payment_status:
                data['payment_status'] = payment_status
            
            result = self.supabase.table('listing_bookings').update(data).eq('id', booking_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao atualizar status da reserva: {e}")
            return False
    
    def save_listing_availability_period(self, listing_id: int, user_id: int, start_date: str, end_date: str, 
                                        price_per_night: float, minimum_nights: int = 1, 
                                        maximum_nights: int = None, notes: str = None) -> bool:
        """
        Salva disponibilidade para um período de datas
        """
        try:
            from datetime import datetime, timedelta
            
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            success_count = 0
            while current_date <= end_dt:
                date_str = current_date.strftime('%Y-%m-%d')
                
                if self.save_listing_availability(
                    listing_id=listing_id,
                    user_id=user_id,
                    date=date_str,
                    is_available=True,
                    price_per_night=price_per_night,
                    minimum_nights=minimum_nights,
                    maximum_nights=maximum_nights,
                    notes=notes
                ):
                    success_count += 1
                
                current_date += timedelta(days=1)
            
            return success_count > 0
        except Exception as e:
            print(f"❌ Erro ao salvar disponibilidade por período: {e}")
            return False

    def get_available_dates(self, listing_id: int, start_date: str, end_date: str) -> List[str]:
        """
        Retorna lista de datas disponíveis para reserva em um período
        """
        try:
            # Buscar disponibilidade configurada
            availability = self.get_listing_availability(listing_id, start_date, end_date)
            
            # Buscar reservas confirmadas no período
            bookings = self.supabase.table('listing_bookings').select(
                'checkin_date, checkout_date'
            ).eq('listing_id', listing_id).in_('status', ['confirmed', 'pending']).execute()
            
            available_dates = []
            
            # Se não há configuração de disponibilidade, assumir que todas as datas estão disponíveis
            if not availability:
                from datetime import datetime, timedelta
                current_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                
                while current_date <= end_dt:
                    date_str = current_date.strftime('%Y-%m-%d')
                    
                    # Verificar se não está ocupada por reserva
                    is_booked = False
                    for booking in bookings.data:
                        if booking['checkin_date'] <= date_str <= booking['checkout_date']:
                            is_booked = True
                            break
                    
                    if not is_booked:
                        available_dates.append(date_str)
                    
                    current_date += timedelta(days=1)
            else:
                # Usar configuração de disponibilidade
                for avail in availability:
                    if avail['is_available']:
                        date_str = avail['date']
                        
                        # Verificar se não está ocupada por reserva
                        is_booked = False
                        for booking in bookings.data:
                            if booking['checkin_date'] <= date_str <= booking['checkout_date']:
                                is_booked = True
                                break
                        
                        if not is_booked:
                            available_dates.append(date_str)
            
            return sorted(available_dates)
        except Exception as e:
            print(f"❌ Erro ao buscar datas disponíveis: {e}")
            return []

    def delete_listing_availability(self, listing_id: int, date: str, user_id: int = None) -> bool:
        """
        Remove disponibilidade de uma data específica para um anúncio
        """
        try:
            query = self.supabase.table('listing_availability').delete().eq('listing_id', listing_id).eq('date', date)
            
            # Se user_id for fornecido, adicionar à query para segurança
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao remover disponibilidade: {e}")
            return False

    def get_all_public_listings(self) -> List[Dict]:
        """Buscar todos os anúncios da tabela com informações de disponibilidade e reservas pendentes"""
        try:
            result = self.supabase.table('user_listings').select('*').eq('is_active', True).execute()
            
            if not result.data:
                return []
            
            # Adicionar informações de disponibilidade e reservas pendentes para cada anúncio
            listings_with_status = []
            for listing in result.data:
                # Buscar próximas datas disponíveis
                availability_result = self.supabase.table('listing_availability').select(
                    'date, is_available'
                ).eq('listing_id', listing['id']).eq('is_available', True).gte('date', datetime.now().strftime('%Y-%m-%d')).order('date').limit(5).execute()
                
                # Buscar reservas pendentes
                pending_bookings = self.supabase.table('listing_bookings').select(
                    'checkin_date, checkout_date'
                ).eq('listing_id', listing['id']).eq('status', 'pending').execute()
                
                # Adicionar informações ao anúncio
                listing['available_dates'] = [item['date'] for item in availability_result.data] if availability_result.data else []
                listing['has_pending_bookings'] = len(pending_bookings.data) > 0 if pending_bookings.data else False
                listing['pending_periods'] = []
                
                if pending_bookings.data:
                    for booking in pending_bookings.data:
                        listing['pending_periods'].append({
                            'start': booking['checkin_date'],
                            'end': booking['checkout_date']
                        })
                
                listings_with_status.append(listing)
            
            return listings_with_status
        except Exception as e:
            print(f"❌ Erro ao buscar anúncios públicos: {e}")
            return []
    
    def get_public_listing_by_id(self, listing_id: int) -> Optional[Dict]:
        """Buscar um anúncio específico por ID"""
        try:
            result = self.supabase.table('user_listings').select(
                '*, municipios(nome, estado), users(name, email)'
            ).eq('id', listing_id).eq('is_active', True).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Erro ao buscar anúncio por ID {listing_id}: {e}")
            return None
    
    def get_listings_available_on_date(self, date: str) -> List[Dict]:
        """Buscar anúncios disponíveis em uma data específica"""
        try:
            # Buscar anúncios que têm disponibilidade na data
            availability_result = self.supabase.table('listing_availability').select(
                'listing_id'
            ).eq('date', date).eq('is_available', True).execute()
            
            if not availability_result.data:
                return []
            
            # Extrair IDs dos anúncios disponíveis
            listing_ids = [item['listing_id'] for item in availability_result.data]
            
            # Buscar detalhes dos anúncios
            listings_result = self.supabase.table('user_listings').select(
                '*'
            ).in_('id', listing_ids).eq('is_active', True).execute()
            
            # Adicionar informações de preço da disponibilidade
            listings_with_price = []
            for listing in listings_result.data:
                # Buscar preço específico para a data
                price_result = self.supabase.table('listing_availability').select(
                    'price_per_night'
                ).eq('listing_id', listing['id']).eq('date', date).execute()
                
                if price_result.data:
                    listing['price_for_date'] = price_result.data[0]['price_per_night']
                else:
                    listing['price_for_date'] = listing.get('price_per_night', 0)
                
                listings_with_price.append(listing)
            
            return listings_with_price
        except Exception as e:
            print(f"❌ Erro ao buscar anúncios disponíveis na data {date}: {e}")
            return []
    
    def check_availability(self, listing_id: int, start_date: str, end_date: str) -> bool:
        """Verificar se um anúncio está disponível em um período"""
        try:
            from datetime import datetime, timedelta
            
            # Primeiro, verificar se não há reservas conflitantes
            bookings_result = self.supabase.table('listing_bookings').select(
                'checkin_date, checkout_date'
            ).eq('listing_id', listing_id).in_('status', ['confirmed', 'pending']).execute()
            
            for booking in bookings_result.data:
                booking_start = booking['checkin_date']
                booking_end = booking['checkout_date']
                
                # Verificar sobreposição de datas
                if (start_date <= booking_end and end_date >= booking_start):
                    return False
            
            # Buscar disponibilidade configurada no período
            result = self.supabase.table('listing_availability').select(
                'date, is_available'
            ).eq('listing_id', listing_id).gte('date', start_date).lte('date', end_date).execute()
            
            # Se não há configuração de disponibilidade, assumir que está disponível
            # (desde que não haja reservas conflitantes, já verificado acima)
            if not result.data:
                return True
            
            # Se há configuração, verificar se todas as datas do período estão marcadas como disponíveis
            # Criar lista de todas as datas no período solicitado
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            current_date = start_dt
            required_dates = set()
            while current_date <= end_dt:
                required_dates.add(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            # Verificar se todas as datas necessárias estão configuradas e disponíveis
            configured_dates = {item['date']: item['is_available'] for item in result.data}
            
            for date in required_dates:
                # Se a data está configurada, verificar se está disponível
                if date in configured_dates:
                    if not configured_dates[date]:
                        return False
                # Se a data não está configurada, assumir que está disponível
            
            return True
        except Exception as e:
            print(f"❌ Erro ao verificar disponibilidade: {e}")
            return False
    
    def create_public_booking(self, listing_id: int, start_date: str, end_date: str,
                            guest_name: str, guest_email: str, guest_phone: str = None) -> int:
        """Criar uma reserva pública"""
        try:
            # Calcular número de noites
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            total_nights = (end - start).days
            
            # Buscar preço do anúncio
            listing_result = self.supabase.table('user_listings').select(
                'price_per_night, user_id'
            ).eq('id', listing_id).execute()
            
            if not listing_result.data:
                return None
            
            listing = listing_result.data[0]
            price_per_night = listing.get('price_per_night', 0)
            host_user_id = listing['user_id']
            total_price = price_per_night * total_nights
            
            # Criar reserva
            booking_data = {
                'listing_id': listing_id,
                'guest_user_id': None,  # Reserva pública sem usuário logado
                'host_user_id': host_user_id,
                'checkin_date': start_date,
                'checkout_date': end_date,
                'total_nights': total_nights,
                'price_per_night': price_per_night,
                'total_price': total_price,
                'guest_name': guest_name,
                'guest_email': guest_email,
                'guest_phone': guest_phone,
                'status': 'pending',
                'payment_status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('listing_bookings').insert(booking_data).execute()
            
            if result.data:
                booking_id = result.data[0]['id']
                # Criar notificação automática para o anfitrião
                self.create_booking_notification(booking_id)
                return booking_id
            return None
        except Exception as e:
            print(f"❌ Erro ao criar reserva pública: {e}")
            return None
    
    def create_authenticated_booking(self, listing_id: int, guest_user_id: int, start_date: str, end_date: str,
                                   guest_name: str, guest_email: str, guests_count: int = 1) -> int:
        """Criar uma reserva para usuário autenticado"""
        try:
            # Calcular número de noites
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            total_nights = (end - start).days
            
            # Buscar preço do anúncio
            listing_result = self.supabase.table('user_listings').select(
                'price_per_night, user_id'
            ).eq('id', listing_id).execute()
            
            if not listing_result.data:
                return None
            
            listing = listing_result.data[0]
            price_per_night = listing.get('price_per_night', 0)
            host_user_id = listing['user_id']
            total_price = price_per_night * total_nights
            
            # Criar reserva (removendo guests_count que não existe na tabela)
            booking_data = {
                'listing_id': listing_id,
                'guest_user_id': guest_user_id,
                'host_user_id': host_user_id,
                'checkin_date': start_date,
                'checkout_date': end_date,
                'total_nights': total_nights,
                'price_per_night': price_per_night,
                'total_price': total_price,
                'guest_name': guest_name,
                'guest_email': guest_email,
                'status': 'pending',
                'payment_status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('listing_bookings').insert(booking_data).execute()
            
            if result.data:
                booking_id = result.data[0]['id']
                print(f"✅ Reserva autenticada criada com ID: {booking_id} para usuário {guest_user_id}")
                
                # Criar notificação para o host
                self.create_booking_notification(booking_id)
                
                return booking_id
            return None
        except Exception as e:
            print(f"❌ Erro ao criar reserva autenticada: {e}")
            return None
    
    def get_user_bookings(self, user_id: int) -> List[Dict]:
        """Buscar todas as reservas feitas por um usuário como hóspede"""
        try:
            result = self.supabase.table('listing_bookings').select(
                '*, user_listings(id, title, url, image_url, municipio_id, municipios(nome))'
            ).eq('guest_user_id', user_id).order('created_at', desc=True).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Erro ao buscar reservas do usuário: {e}")
            return []
    
    def get_user_reservation_for_listing(self, user_id: int, listing_id: int) -> Optional[Dict]:
        """Verificar se o usuário tem uma reserva ativa para um anúncio específico"""
        try:
            result = self.supabase.table('listing_bookings').select(
                '*, user_listings(id, title, url, image_url)'
            ).eq('guest_user_id', user_id).eq('listing_id', listing_id).in_('status', ['confirmed', 'pending']).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Erro ao verificar reserva do usuário: {e}")
            return None
    
    def get_next_available_date(self, listing_id: int, from_date: str) -> str:
        """Buscar a próxima data disponível para um anúncio a partir de uma data específica"""
        try:
            from datetime import datetime, timedelta
            
            # Converter data inicial
            start_date = datetime.strptime(from_date, '%Y-%m-%d')
            
            # Buscar até 365 dias à frente
            for i in range(365):
                check_date = start_date + timedelta(days=i)
                check_date_str = check_date.strftime('%Y-%m-%d')
                
                # Verificar se a data está disponível
                if self.check_availability(listing_id, check_date_str, check_date_str):
                    return check_date_str
            
            # Se não encontrou nenhuma data disponível nos próximos 365 dias
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar próxima data disponível: {e}")
            return None
    
    def get_available_period(self, listing_id: int, from_date: str) -> dict:
        """Buscar o período de disponibilidade contínua a partir de uma data específica"""
        try:
            from datetime import datetime, timedelta
            
            # Converter data inicial
            start_date = datetime.strptime(from_date, '%Y-%m-%d')
            
            # Buscar até 365 dias à frente
            available_start = None
            available_end = None
            
            for i in range(365):
                check_date = start_date + timedelta(days=i)
                check_date_str = check_date.strftime('%Y-%m-%d')
                
                # Verificar se a data está disponível
                if self.check_availability(listing_id, check_date_str, check_date_str):
                    if available_start is None:
                        available_start = check_date_str
                    available_end = check_date_str
                else:
                    # Se encontrou uma data indisponível e já tinha um período, parar
                    if available_start is not None:
                        break
            
            if available_start and available_end:
                return {
                    'start_date': available_start,
                    'end_date': available_end
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar período disponível: {e}")
            return None

    # =====================================================
    # FUNÇÕES DE FAVORITOS
    # =====================================================
    
    def add_favorite(self, user_id: int, listing_id: int) -> bool:
        """
        Adiciona um anúncio aos favoritos do usuário
        """
        try:
            result = self.supabase.table('user_favorites').insert({
                'user_id': user_id,
                'listing_id': listing_id
            }).execute()
            
            if result.data:
                print(f"✅ Anúncio {listing_id} adicionado aos favoritos do usuário {user_id}")
                return True
            return False
            
        except Exception as e:
            # Se for erro de duplicata (UNIQUE constraint), considerar como sucesso
            if 'duplicate key value' in str(e).lower() or 'unique constraint' in str(e).lower():
                print(f"ℹ️ Anúncio {listing_id} já está nos favoritos do usuário {user_id}")
                return True
            # Se a tabela não existir, avisar mas não falhar
            if 'does not exist' in str(e).lower() or 'not found' in str(e).lower():
                print(f"⚠️ Tabela user_favorites não existe. Execute o SQL de criação no Supabase.")
                return False
            print(f"❌ Erro ao adicionar favorito: {e}")
            return False
    
    def remove_favorite(self, user_id: int, listing_id: int) -> bool:
        """
        Remove um anúncio dos favoritos do usuário
        """
        try:
            result = self.supabase.table('user_favorites').delete().eq(
                'user_id', user_id
            ).eq('listing_id', listing_id).execute()
            
            print(f"✅ Anúncio {listing_id} removido dos favoritos do usuário {user_id}")
            return True
            
        except Exception as e:
            # Se a tabela não existir, avisar mas não falhar
            if 'does not exist' in str(e).lower() or 'not found' in str(e).lower():
                print(f"⚠️ Tabela user_favorites não existe. Execute o SQL de criação no Supabase.")
                return False
            print(f"❌ Erro ao remover favorito: {e}")
            return False
    
    def get_user_favorites(self, user_id: int) -> List[Dict]:
        """
        Busca todos os anúncios favoritos de um usuário
        """
        try:
            result = self.supabase.table('user_favorites').select(
                '*, user_listings(*, municipios(nome, estado))'
            ).eq('user_id', user_id).order('created_at', desc=True).execute()
            
            return result.data
            
        except Exception as e:
            # Se a tabela não existir, retornar lista vazia
            if 'does not exist' in str(e).lower() or 'not found' in str(e).lower():
                print(f"⚠️ Tabela user_favorites não existe. Execute o SQL de criação no Supabase.")
                return []
            print(f"❌ Erro ao buscar favoritos do usuário {user_id}: {e}")
            return []
    
    def is_favorite(self, user_id: int, listing_id: int) -> bool:
        """
        Verifica se um anúncio é favorito de um usuário
        """
        try:
            result = self.supabase.table('user_favorites').select('id').eq(
                'user_id', user_id
            ).eq('listing_id', listing_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Erro ao verificar se anúncio é favorito: {e}")
            return False
    
    def get_favorites_count(self, user_id: int) -> int:
        """
        Conta quantos favoritos um usuário tem
        """
        try:
            result = self.supabase.table('user_favorites').select(
                'id', count='exact'
            ).eq('user_id', user_id).execute()
            
            return result.count or 0
            
        except Exception as e:
            print(f"❌ Erro ao contar favoritos do usuário {user_id}: {e}")
            return 0
    
    def get_most_favorited_listings(self, limit: int = 10) -> List[Dict]:
        """
        Busca os anúncios mais favoritados
        """
        try:
            # Esta consulta pode precisar ser ajustada dependendo do Supabase
            result = self.supabase.rpc('get_most_favorited_listings', {
                'limit_count': limit
            }).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"❌ Erro ao buscar anúncios mais favoritados: {e}")
            # Fallback: buscar favoritos de forma simples
            try:
                result = self.supabase.table('user_favorites').select(
                    'listing_id, user_listings(title, url, price_per_night, rating)'
                ).execute()
                
                # Agrupar por listing_id e contar
                from collections import Counter
                listing_counts = Counter([fav['listing_id'] for fav in result.data])
                
                # Buscar detalhes dos mais favoritados
                most_favorited = []
                for listing_id, count in listing_counts.most_common(limit):
                    listing_result = self.supabase.table('user_listings').select(
                        '*, municipios(nome, estado)'
                    ).eq('id', listing_id).execute()
                    
                    if listing_result.data:
                        listing = listing_result.data[0]
                        listing['favorite_count'] = count
                        most_favorited.append(listing)
                
                return most_favorited
                
            except Exception as e2:
                print(f"❌ Erro no fallback para anúncios mais favoritados: {e2}")
                return []

    # ===== FUNÇÕES DE NOTIFICAÇÕES =====
    
    def create_notification(self, user_id: int, notification_type: str, title: str, message: str,
                          related_booking_id: int = None, related_listing_id: int = None) -> int:
        """
        Cria uma nova notificação para o usuário
        """
        try:
            notification_data = {
                'user_id': user_id,
                'type': notification_type,
                'title': title,
                'message': message,
                'related_booking_id': related_booking_id,
                'related_listing_id': related_listing_id,
                'is_read': False,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('notifications').insert(notification_data).execute()
            
            if result.data:
                print(f"✅ Notificação criada com ID: {result.data[0]['id']} para usuário {user_id}")
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"❌ Erro ao criar notificação: {e}")
            return None
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> List[Dict]:
        """
        Busca notificações do usuário
        """
        try:
            query = self.supabase.table('notifications').select(
                '*, listing_bookings(guest_name, checkin_date, checkout_date), user_listings(title)'
            ).eq('user_id', user_id)
            
            if unread_only:
                query = query.eq('is_read', False)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"❌ Erro ao buscar notificações: {e}")
            return []
    
    def mark_notification_as_read(self, notification_id: int, user_id: int = None) -> bool:
        """
        Marca uma notificação como lida
        """
        try:
            update_data = {
                'is_read': True,
                'read_at': datetime.now().isoformat()
            }
            
            query = self.supabase.table('notifications').update(update_data).eq('id', notification_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if result.data:
                print(f"✅ Notificação {notification_id} marcada como lida")
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao marcar notificação como lida: {e}")
            return False
    
    def mark_all_notifications_as_read(self, user_id: int) -> bool:
        """
        Marca todas as notificações do usuário como lidas
        """
        try:
            update_data = {
                'is_read': True,
                'read_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('notifications').update(update_data).eq('user_id', user_id).eq('is_read', False).execute()
            
            if result.data:
                print(f"✅ Todas as notificações do usuário {user_id} marcadas como lidas")
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao marcar todas as notificações como lidas: {e}")
            return False
    
    def get_unread_notifications_count(self, user_id: int) -> int:
        """
        Retorna o número de notificações não lidas do usuário
        """
        try:
            result = self.supabase.table('notifications').select('id', count='exact').eq('user_id', user_id).eq('is_read', False).execute()
            return result.count if result.count else 0
        except Exception as e:
            print(f"❌ Erro ao contar notificações não lidas: {e}")
            return 0
    
    def create_booking_notification(self, booking_id: int) -> bool:
        """
        Cria notificação automática quando uma nova reserva é feita
        """
        try:
            # Buscar dados da reserva
            booking_result = self.supabase.table('listing_bookings').select(
                '*, user_listings(title, user_id), users!guest_user_id(name)'
            ).eq('id', booking_id).execute()
            
            if not booking_result.data:
                print(f"❌ Reserva {booking_id} não encontrada")
                return False
            
            booking = booking_result.data[0]
            host_user_id = booking['user_listings']['user_id']
            guest_name = booking['users']['name'] if booking['users'] else booking['guest_name']
            listing_title = booking['user_listings']['title']
            checkin_date = booking['checkin_date']
            checkout_date = booking['checkout_date']
            
            # Criar notificação para o anfitrião
            title = "Nova Reserva Recebida!"
            message = f"Uma nova reserva de {guest_name} no anúncio '{listing_title}' do dia {checkin_date} até o dia {checkout_date}."
            
            return self.create_notification(
                user_id=host_user_id,
                notification_type='new_booking',
                title=title,
                message=message,
                related_booking_id=booking_id,
                related_listing_id=booking['listing_id']
            ) is not None
            
        except Exception as e:
            print(f"❌ Erro ao criar notificação de reserva: {e}")
            return False
    
    def delete_notification(self, notification_id: int, user_id: int = None) -> bool:
        """
        Deleta uma notificação
        """
        try:
            query = self.supabase.table('notifications').delete().eq('id', notification_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if result.data:
                print(f"✅ Notificação {notification_id} deletada")
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao deletar notificação: {e}")
            return False

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

    def create_review(self, booking_id: int, overall_rating: int, 
                     cleanliness_rating: int = None, communication_rating: int = None,
                     checkin_rating: int = None, accuracy_rating: int = None,
                     location_rating: int = None, value_rating: int = None, 
                     amenities_rating: int = None, review_title: str = None,
                     review_comment: str = None, would_recommend: bool = True) -> int:
        """
        Cria uma nova avaliação de hospedagem
        """
        try:
            # Buscar dados da reserva
            booking_result = self.supabase.table('listing_bookings').select(
                'listing_id, guest_user_id, host_user_id'
            ).eq('id', booking_id).execute()
            
            if not booking_result.data:
                print(f"❌ Reserva {booking_id} não encontrada")
                return None
            
            booking = booking_result.data[0]
            
            review_data = {
                'booking_id': booking_id,
                'listing_id': booking['listing_id'],
                'guest_user_id': booking['guest_user_id'],
                'host_user_id': booking['host_user_id'],
                'overall_rating': overall_rating,
                'would_recommend': would_recommend,
                'created_at': datetime.now().isoformat()
            }
            
            # Adicionar avaliações opcionais
            if cleanliness_rating:
                review_data['cleanliness_rating'] = cleanliness_rating
            if communication_rating:
                review_data['communication_rating'] = communication_rating
            if checkin_rating:
                review_data['checkin_rating'] = checkin_rating
            if accuracy_rating:
                review_data['accuracy_rating'] = accuracy_rating
            if location_rating:
                review_data['location_rating'] = location_rating
            if value_rating:
                review_data['value_rating'] = value_rating
            if amenities_rating:
                review_data['amenities_rating'] = amenities_rating
            if review_title:
                review_data['review_title'] = review_title
            if review_comment:
                review_data['review_comment'] = review_comment
            
            result = self.supabase.table('accommodation_reviews').insert(review_data).execute()
            
            if result.data:
                review_id = result.data[0]['id']
                print(f"✅ Avaliação criada com ID: {review_id}")
                
                # Atualizar estatísticas do anúncio
                self.update_listing_rating_stats(booking['listing_id'])
                
                return review_id
            return None
        except Exception as e:
            print(f"❌ Erro ao criar avaliação: {e}")
            return None
    
    def get_listing_reviews(self, listing_id: int, public_only: bool = True, limit: int = 50) -> List[Dict]:
        """
        Busca avaliações de um anúncio
        """
        try:
            query = self.supabase.table('accommodation_reviews').select(
                '*, users!guest_user_id(name)'
            ).eq('listing_id', listing_id)
            
            if public_only:
                query = query.eq('is_public', True).eq('is_approved', True)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"❌ Erro ao buscar avaliações: {e}")
            return []
    
    def get_user_reviews(self, user_id: int, as_guest: bool = True, limit: int = 50) -> List[Dict]:
        """
        Busca avaliações de um usuário (como hóspede ou anfitrião)
        """
        try:
            field = 'guest_user_id' if as_guest else 'host_user_id'
            
            query = self.supabase.table('accommodation_reviews').select(
                '*, user_listings(title), users!guest_user_id(name)'
            ).eq(field, user_id)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"❌ Erro ao buscar avaliações do usuário: {e}")
            return []
    
    def get_booking_review(self, booking_id: int) -> Optional[Dict]:
        """
        Busca avaliação de uma reserva específica
        """
        try:
            result = self.supabase.table('accommodation_reviews').select(
                '*'
            ).eq('booking_id', booking_id).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Erro ao buscar avaliação da reserva: {e}")
            return None
    
    def update_listing_rating_stats(self, listing_id: int) -> bool:
        """
        Atualiza as estatísticas de avaliação de um anúncio
        """
        try:
            # Buscar todas as avaliações aprovadas do anúncio
            reviews_result = self.supabase.table('accommodation_reviews').select(
                'overall_rating'
            ).eq('listing_id', listing_id).eq('is_approved', True).execute()
            
            if not reviews_result.data:
                return True
            
            ratings = [review['overall_rating'] for review in reviews_result.data]
            avg_rating = sum(ratings) / len(ratings)
            review_count = len(ratings)
            
            # Atualizar anúncio com nova média e contagem
            update_result = self.supabase.table('user_listings').update({
                'rating': round(avg_rating, 2),
                'reviews': review_count,
                'updated_at': datetime.now().isoformat()
            }).eq('id', listing_id).execute()
            
            return len(update_result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao atualizar estatísticas de avaliação: {e}")
            return False
    
    def can_user_review_booking(self, user_id: int, booking_id: int) -> bool:
        """
        Verifica se um usuário pode avaliar uma reserva
        """
        try:
            # Verificar se a reserva existe e pertence ao usuário
            booking_result = self.supabase.table('listing_bookings').select(
                'guest_user_id, status, checkout_date'
            ).eq('id', booking_id).eq('guest_user_id', user_id).execute()
            
            if not booking_result.data:
                return False
            
            booking = booking_result.data[0]
            
            # Só pode avaliar se a reserva foi concluída
            if booking['status'] != 'completed':
                return False
            
            # Verificar se já não existe uma avaliação
            review_result = self.supabase.table('accommodation_reviews').select(
                'id'
            ).eq('booking_id', booking_id).execute()
            
            return len(review_result.data) == 0
        except Exception as e:
            print(f"❌ Erro ao verificar permissão de avaliação: {e}")
            return False
    
    def can_user_edit_review(self, user_id: int, booking_id: int) -> Dict:
        """
        Verifica se um usuário pode editar uma avaliação existente
        Retorna dict com can_edit (bool) e reason (str)
        """
        try:
            # Verificar se a reserva existe e pertence ao usuário
            booking_result = self.supabase.table('listing_bookings').select(
                'guest_user_id, status, checkout_date'
            ).eq('id', booking_id).eq('guest_user_id', user_id).execute()
            
            if not booking_result.data:
                return {'can_edit': False, 'reason': 'Reserva não encontrada'}
            
            booking = booking_result.data[0]
            
            # Só pode editar se a reserva foi concluída
            if booking['status'] != 'completed':
                return {'can_edit': False, 'reason': 'Reserva não foi concluída'}
            
            # Verificar se existe uma avaliação
            review_result = self.supabase.table('accommodation_reviews').select(
                'id, created_at'
            ).eq('booking_id', booking_id).execute()
            
            if not review_result.data:
                return {'can_edit': False, 'reason': 'Nenhuma avaliação encontrada'}
            
            review = review_result.data[0]
            
            # Verificar se ainda está dentro do prazo de 10 dias
            from datetime import datetime, timedelta
            review_date = datetime.fromisoformat(review['created_at'].replace('Z', '+00:00'))
            current_date = datetime.now(review_date.tzinfo)
            days_since_review = (current_date - review_date).days
            
            if days_since_review > 10:
                return {
                    'can_edit': False, 
                    'reason': f'Prazo para reavaliar já se esgotou ({days_since_review} dias desde a avaliação)'
                }
            
            return {
                'can_edit': True, 
                'reason': f'Pode editar (ainda restam {10 - days_since_review} dias)'
            }
            
        except Exception as e:
            print(f"❌ Erro ao verificar permissão de edição: {e}")
            return {'can_edit': False, 'reason': 'Erro interno'}
    
    def update_review(self, booking_id: int, user_id: int, **review_data) -> bool:
        """
        Atualiza uma avaliação existente
        """
        try:
            # Verificar se pode editar
            edit_check = self.can_user_edit_review(user_id, booking_id)
            if not edit_check['can_edit']:
                print(f"❌ Não pode editar: {edit_check['reason']}")
                return False
            
            # Preparar dados para atualização
            update_data = {}
            allowed_fields = [
                'overall_rating', 'cleanliness_rating', 'communication_rating',
                'checkin_rating', 'accuracy_rating', 'location_rating', 'value_rating',
                'amenities_rating', 'review_title', 'review_comment', 'would_recommend'
            ]
            
            for field, value in review_data.items():
                if field in allowed_fields and value is not None:
                    update_data[field] = value
            
            if not update_data:
                print("❌ Nenhum campo válido para atualizar")
                return False
            
            # Adicionar timestamp de atualização
            update_data['updated_at'] = datetime.now().isoformat()
            
            # Atualizar a avaliação
            result = self.supabase.table('accommodation_reviews').update(
                update_data
            ).eq('booking_id', booking_id).execute()
            
            if result.data:
                print(f"✅ Avaliação atualizada com sucesso")
                
                # Atualizar estatísticas do anúncio
                booking_result = self.supabase.table('listing_bookings').select(
                    'listing_id'
                ).eq('id', booking_id).execute()
                
                if booking_result.data:
                    self.update_listing_rating_stats(booking_result.data[0]['listing_id'])
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro ao atualizar avaliação: {e}")
            return False
    
    def get_listing_rating_summary(self, listing_id: int) -> Dict:
        """
        Retorna resumo das avaliações de um anúncio
        """
        try:
            result = self.supabase.table('accommodation_reviews').select(
                'overall_rating, cleanliness_rating, communication_rating, location_rating, value_rating, amenities_rating, would_recommend'
            ).eq('listing_id', listing_id).eq('is_approved', True).execute()
            
            if not result.data:
                return {
                    'total_reviews': 0,
                    'average_overall': 0,
                    'average_cleanliness': 0,
                    'average_communication': 0,
                    'average_location': 0,
                    'average_value': 0,
                    'average_amenities': 0,
                    'recommendation_rate': 0
                }
            
            reviews = result.data
            total = len(reviews)
            
            # Calcular médias
            overall_ratings = [r['overall_rating'] for r in reviews]
            cleanliness_ratings = [r['cleanliness_rating'] for r in reviews if r['cleanliness_rating']]
            communication_ratings = [r['communication_rating'] for r in reviews if r['communication_rating']]
            location_ratings = [r['location_rating'] for r in reviews if r['location_rating']]
            value_ratings = [r['value_rating'] for r in reviews if r['value_rating']]
            amenities_ratings = [r['amenities_rating'] for r in reviews if r['amenities_rating']]
            recommendations = [r['would_recommend'] for r in reviews if r['would_recommend'] is not None]
            
            return {
                'total_reviews': total,
                'average_overall': round(sum(overall_ratings) / len(overall_ratings), 2) if overall_ratings else 0,
                'average_cleanliness': round(sum(cleanliness_ratings) / len(cleanliness_ratings), 2) if cleanliness_ratings else 0,
                'average_communication': round(sum(communication_ratings) / len(communication_ratings), 2) if communication_ratings else 0,
                'average_location': round(sum(location_ratings) / len(location_ratings), 2) if location_ratings else 0,
                'average_value': round(sum(value_ratings) / len(value_ratings), 2) if value_ratings else 0,
                'average_amenities': round(sum(amenities_ratings) / len(amenities_ratings), 2) if amenities_ratings else 0,
                'recommendation_rate': round((sum(recommendations) / len(recommendations)) * 100, 1) if recommendations else 0
            }
        except Exception as e:
            print(f"❌ Erro ao buscar resumo de avaliações: {e}")
            return {}

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