#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web para Análise de Preços Airbnb
Interface web para visualizar resultados da análise competitiva
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from airbnb_scraper import AirbnbClimateScraper
from datetime import datetime, timedelta
import json
import threading
import time
import os
from dotenv import load_dotenv
from database import get_database
from auth import GoogleAuth, User, init_auth

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'airbnb_analysis_2024')

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Configurar Google OAuth
google_auth = init_auth(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Variáveis globais para armazenar dados (fallback se banco não disponível)
latest_analysis = None
analysis_history = []
monitoring_active = False
monitoring_thread = None
favorite_competitors = []  # Lista de concorrentes favoritos

# Inicializar banco de dados
db = get_database()

def load_data_from_database():
    """Carrega dados do banco de dados na inicialização"""
    global latest_analysis, analysis_history
    
    if db:
        try:
            # Carregar última análise
            latest_db_analysis = db.get_latest_analysis()
            if latest_db_analysis:
                latest_analysis = latest_db_analysis
                print("✅ Última análise carregada do banco de dados")
            
            # Carregar histórico
            history_db = db.get_analysis_history(20)
            if history_db:
                analysis_history = history_db
                print(f"✅ {len(history_db)} análises carregadas do histórico")
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar dados do banco: {e}")
            print("📝 Usando dados em memória como fallback")
    else:
        print("⚠️ Banco de dados não disponível, usando dados em memória")

# Carregar dados na inicialização
load_data_from_database()

@app.route('/')
@login_required
def index():
    """Página principal"""
    return render_template('index.html', 
                          latest_analysis=latest_analysis,
                          monitoring_active=monitoring_active)

@app.route('/login')
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if not google_auth.is_configured():
        flash('Autenticação Google não configurada. Entre em contato com o administrador.', 'error')
        return render_template('login.html', auth_configured=False)
    
    return render_template('login.html', auth_configured=True)

@app.route('/auth/google')
def auth_google():
    """Redireciona para autenticação Google"""
    if not google_auth.is_configured():
        flash('Autenticação Google não configurada.', 'error')
        return redirect(url_for('login'))
    
    authorization_url = google_auth.get_authorization_url()
    if not authorization_url:
        flash('Erro ao gerar URL de autenticação.', 'error')
        return redirect(url_for('login'))
    
    return redirect(authorization_url)

@app.route('/auth/callback')
def auth_callback():
    """Callback do Google OAuth"""
    if not google_auth.is_configured():
        flash('Autenticação Google não configurada.', 'error')
        return redirect(url_for('login'))
    
    user = google_auth.handle_callback(request.url)
    if user:
        login_user(user, remember=True)
        flash(f'Bem-vindo, {user.name}!', 'success')
        
        # Redirecionar para página solicitada ou página inicial
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))
    else:
        flash('Erro na autenticação. Tente novamente.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    session.clear()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/analise')
@login_required
def analise():
    """Página de análise detalhada"""
    return render_template('analise.html', 
                         analysis_data=latest_analysis,
                         history=analysis_history[-10:])  # Últimas 10 análises

@app.route('/agenda')
@login_required
def agenda():
    """Página da agenda de preços"""
    return render_template('agenda.html')

@app.route('/similaridade')
@login_required
def similaridade():
    """Página de análise de similaridade"""
    return render_template('similaridade.html')

@app.route('/perfil')
@login_required
def perfil():
    """Página do perfil do usuário"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        flash('Erro ao carregar perfil do usuário', 'error')
        return redirect(url_for('index'))
    
    try:
        # Buscar todos os anúncios do usuário
        all_listings = db.get_user_listings(user_db_id)
        
        # Separar anúncios normais dos favoritos da similaridade
        regular_listings = []
        similarity_favorites = []
        
        for listing in all_listings:
            if listing.get('platform') == 'airbnb_similarity':
                similarity_favorites.append(listing)
            else:
                regular_listings.append(listing)
        
        # Buscar análises do usuário
        analyses = db.get_user_analyses(user_db_id)
        
        # Contar anúncios ativos (apenas regulares)
        active_listings = len([l for l in regular_listings if l.get('is_active', True)])
        
        # Contar favoritos da similaridade
        active_similarity_favorites = len([l for l in similarity_favorites if l.get('is_active', True)])
        
        return render_template('perfil.html', 
                             listings=regular_listings,
                             similarity_favorites=similarity_favorites,
                             analyses=analyses,
                             active_listings=active_listings,
                             active_similarity_favorites=active_similarity_favorites)
    except Exception as e:
        print(f"❌ Erro ao carregar perfil: {e}")
        flash('Erro ao carregar dados do perfil', 'error')
        return redirect(url_for('index'))

@app.route('/perfil/extract_listing_info', methods=['POST'])
@login_required
def extract_listing_info():
    """Extrai informações de um anúncio do Airbnb automaticamente"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL é obrigatória'})
        
        # Verificar se é um URL válido do Airbnb
        if 'airbnb.com' not in url:
            return jsonify({'success': False, 'error': 'URL deve ser do Airbnb'})
        
        # Usar o scraper para extrair informações
        scraper = AirbnbClimateScraper()
        
        # Simular dados de check-in/out para análise (próximo final de semana)
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and today.weekday() >= 4:
            days_until_friday = 7
        
        checkin = (today + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
        checkout = (today + timedelta(days=days_until_friday + 2)).strftime('%Y-%m-%d')
        
        # Extrair informações do anúncio
        listing_info = scraper.analyze_specific_listing(url, checkin, checkout)
        
        if not listing_info:
            return jsonify({'success': False, 'error': 'Não foi possível extrair informações do anúncio'})
        
        # Pegar o primeiro resultado
        info = listing_info[0] if isinstance(listing_info, list) else listing_info
        
        # Buscar município baseado na localização extraída
        municipio_id = None
        municipio_nome = None
        if info.get('municipality'):
            municipio = db.get_municipio_by_nome(info['municipality'], 'RJ')
            if municipio:
                municipio_id = municipio['id']
                municipio_nome = municipio['nome']
        
        # Retornar informações extraídas
        extracted_data = {
            'title': info.get('title', ''),
            'url': url,
            'platform': 'airbnb',
            'property_type': info.get('property_type', 'Casa'),
            'max_guests': info.get('max_guests', 2),
            'bedrooms': info.get('bedrooms', 1),
            'bathrooms': info.get('bathrooms', 1),
            'municipio_id': municipio_id,
            'municipio_nome': municipio_nome,
            'price_per_night': info.get('price_per_night', 0),
            'rating': info.get('rating', 0),
            'reviews': info.get('reviews', 0)
        }
        
        return jsonify({'success': True, 'data': extracted_data})
        
    except Exception as e:
        print(f"❌ Erro ao extrair informações do anúncio: {e}")
        return jsonify({'success': False, 'error': f'Erro ao processar anúncio: {str(e)}'})

@app.route('/perfil/listing', methods=['POST'])
@login_required
def add_listing():
    """Adiciona um novo anúncio do usuário"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        data = request.get_json()
        print(f"📝 Dados recebidos para salvar anúncio: {data}")
        
        # Verificar se URL está presente
        if not data.get('url'):
            print("❌ URL não fornecida nos dados")
            return jsonify({'success': False, 'error': 'URL do anúncio é obrigatória'})
        
        # Buscar município se fornecido
        municipio_id = None
        if data.get('municipio_nome'):
            municipio = db.get_municipio_by_nome(data['municipio_nome'])
            if municipio:
                municipio_id = municipio['id']
        elif data.get('municipio_id'):
            municipio_id = data['municipio_id']
        
        print(f"💾 Salvando anúncio com URL: {data['url']}")
        
        # Tentar extrair dados completos do scraper se for Airbnb
        extracted_data = {}
        if 'airbnb.com' in data['url']:
            try:
                scraper = AirbnbClimateScraper()
                today = datetime.now()
                checkin = (today + timedelta(days=7)).strftime('%Y-%m-%d')
                checkout = (today + timedelta(days=9)).strftime('%Y-%m-%d')
                
                listing_info = scraper.analyze_specific_listing(data['url'], checkin, checkout)
                if listing_info:
                    info = listing_info[0] if isinstance(listing_info, list) else listing_info
                    extracted_data = {
                        'price_per_night': info.get('price_per_night'),
                        'rating': info.get('rating'),
                        'reviews': info.get('reviews'),
                        'address': info.get('address'),
                        'latitude': info.get('latitude'),
                        'longitude': info.get('longitude'),
                        'description': info.get('description'),
                        'amenities': info.get('amenities'),
                        'image_url': info.get('image_url'),
                        'is_beachfront': info.get('is_beachfront', False),
                        'beach_confidence': info.get('beach_confidence', 0),
                        'instant_book': info.get('instant_book', False),
                        'superhost': info.get('superhost', False),
                        'cleaning_fee': info.get('cleaning_fee'),
                        'service_fee': info.get('service_fee'),
                        'total_price': info.get('total_price'),
                        'minimum_nights': info.get('minimum_nights', 1),
                        'maximum_nights': info.get('maximum_nights'),
                        'availability_365': info.get('availability_365'),
                        'host_name': info.get('host_name'),
                        'host_id': info.get('host_id'),
                        'host_response_rate': info.get('host_response_rate'),
                        'host_response_time': info.get('host_response_time'),
                        'extraction_method': 'airbnb_scraper',
                        'data_quality_score': 0.9 if info.get('price_per_night') else 0.5
                    }
                    print(f"🔍 Dados extraídos pelo scraper: {extracted_data}")
            except Exception as scraper_error:
                print(f"⚠️ Erro ao extrair dados com scraper: {scraper_error}")
        
        listing_id = db.save_user_listing(
            user_id=user_db_id,
            title=data['title'],
            url=data['url'],
            platform=data.get('platform', 'airbnb'),
            municipio_id=municipio_id,
            property_type=data.get('property_type'),
            max_guests=int(data['max_guests']) if data.get('max_guests') else None,
            bedrooms=int(data['bedrooms']) if data.get('bedrooms') else None,
            bathrooms=float(data['bathrooms']) if data.get('bathrooms') else None,
            # Dados extraídos pelo scraper
            **extracted_data
        )
        
        print(f"✅ Anúncio salvo com ID: {listing_id}")
        return jsonify({'success': True, 'listing_id': listing_id})
    except Exception as e:
        print(f"❌ Erro ao adicionar anúncio: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/perfil/listing/<int:listing_id>', methods=['PUT'])
@login_required
def update_listing(listing_id):
    """Atualiza um anúncio do usuário"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        data = request.get_json()
        
        # Preparar dados para atualização
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'url' in data:
            update_data['url'] = data['url']
        if 'platform' in data:
            update_data['platform'] = data['platform']
        if 'property_type' in data:
            update_data['property_type'] = data['property_type']
        if 'max_guests' in data and data['max_guests']:
            update_data['max_guests'] = int(data['max_guests'])
        if 'bedrooms' in data and data['bedrooms']:
            update_data['bedrooms'] = int(data['bedrooms'])
        if 'bathrooms' in data and data['bathrooms']:
            update_data['bathrooms'] = float(data['bathrooms'])
        
        success = db.update_user_listing(listing_id, **update_data)
        
        return jsonify({'success': success})
    except Exception as e:
        print(f"❌ Erro ao atualizar anúncio: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/perfil/listing/<int:listing_id>', methods=['DELETE'])
@login_required
def delete_listing(listing_id):
    """Remove um anúncio do usuário"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        success = db.delete_user_listing(listing_id, user_db_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"❌ Erro ao remover anúncio: {e}")
        return jsonify({'success': False, 'error': str(e)})

def get_next_weekends_and_weekdays(months_ahead=1):
    """Gera lista de próximos finais de semana e dias de semana para análise"""
    today = datetime.now()
    end_date = today + timedelta(days=30 * months_ahead)
    
    periods = []
    current_date = today
    
    while current_date <= end_date:
        # Encontrar próxima sexta-feira
        days_until_friday = (4 - current_date.weekday()) % 7
        if days_until_friday == 0 and current_date.weekday() >= 4:
            days_until_friday = 7
        
        friday = current_date + timedelta(days=days_until_friday)
        sunday = friday + timedelta(days=2)
        
        if friday <= end_date:
            periods.append({
                'type': 'weekend',
                'checkin': friday.strftime('%Y-%m-%d'),
                'checkout': sunday.strftime('%Y-%m-%d'),
                'label': f'FDS {friday.strftime("%d/%m")} - {sunday.strftime("%d/%m")}',
                'priority': True
            })
        
        # Adicionar alguns dias de semana (terça a quinta)
        tuesday = friday - timedelta(days=3)
        thursday = friday - timedelta(days=1)
        
        if tuesday >= today and tuesday <= end_date:
            periods.append({
                'type': 'weekday',
                'checkin': tuesday.strftime('%Y-%m-%d'),
                'checkout': thursday.strftime('%Y-%m-%d'),
                'label': f'Semana {tuesday.strftime("%d/%m")} - {thursday.strftime("%d/%m")}',
                'priority': False
            })
        
        current_date = friday + timedelta(days=7)
    
    return periods

@app.route('/api/get_periods', methods=['GET'])
def api_get_periods():
    """API para obter períodos disponíveis para análise"""
    try:
        periods = get_next_weekends_and_weekdays()
        return jsonify({
            'success': True,
            'data': periods
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/add_favorite', methods=['POST'])
def api_add_favorite():
    """API para adicionar anúncio aos favoritos"""
    global favorite_competitors
    
    try:
        data = request.get_json()
        listing_data = data.get('listing')
        
        if not listing_data:
            return jsonify({
                'success': False,
                'error': 'Dados do anúncio são obrigatórios'
            }), 400
        
        # Verificar se já existe nos favoritos
        listing_id = listing_data.get('id') or listing_data.get('url')
        if any(fav.get('id') == listing_id or fav.get('url') == listing_id for fav in favorite_competitors):
            return jsonify({
                'success': False,
                'error': 'Anúncio já está nos favoritos'
            })
        
        # Adicionar timestamp
        listing_data['added_at'] = datetime.now().isoformat()
        
        # Adicionar aos favoritos
        favorite_competitors.append(listing_data)
        
        return jsonify({
            'success': True,
            'message': 'Anúncio adicionado aos favoritos',
            'total_favorites': len(favorite_competitors)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/remove_favorite', methods=['POST'])
def api_remove_favorite():
    """API para remover anúncio dos favoritos"""
    global favorite_competitors
    
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        
        if not listing_id:
            return jsonify({
                'success': False,
                'error': 'ID do anúncio é obrigatório'
            }), 400
        
        # Remover dos favoritos
        original_count = len(favorite_competitors)
        favorite_competitors = [fav for fav in favorite_competitors 
                              if fav.get('id') != listing_id and fav.get('url') != listing_id]
        
        if len(favorite_competitors) == original_count:
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado nos favoritos'
            })
        
        return jsonify({
            'success': True,
            'message': 'Anúncio removido dos favoritos',
            'total_favorites': len(favorite_competitors)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get_favorites', methods=['GET'])
def api_get_favorites():
    """API para obter lista de favoritos"""
    return jsonify({
        'success': True,
        'data': favorite_competitors,
        'total': len(favorite_competitors)
    })

@app.route('/api/sync_favorites', methods=['POST'])
@login_required
def api_sync_favorites():
    """API para sincronizar favoritos do frontend com o banco de dados"""
    global favorite_competitors
    
    try:
        data = request.get_json()
        frontend_favorites = data.get('favorites', [])
        
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        user_id = current_user.db_id
        saved_count = 0
        errors = []
        
        # Atualizar lista global com os favoritos do frontend
        favorite_competitors = []
        
        for fav in frontend_favorites:
            try:
                # Preparar dados para salvar no banco
                title = fav.get('title', 'Anúncio para Acompanhar')
                url = fav.get('listing_url', '')
                
                # Se não tiver URL, criar uma baseada no ID
                if not url:
                    url = f"https://www.airbnb.com.br/similarity/{fav.get('id', 'unknown')}"
                
                # Salvar no banco de dados
                listing_id = db.save_user_listing(
                    user_id=user_id,
                    title=title,
                    url=url,
                    platform='airbnb_similarity',  # Marcar como favorito da similaridade
                    property_type='similarity_favorite'
                )
                
                if listing_id:
                    saved_count += 1
                    print(f"✅ Favorito salvo no banco: {title} (ID: {listing_id})")
                else:
                    errors.append(f"Erro ao salvar: {title}")
                    print(f"❌ Erro ao salvar favorito: {title}")
                
                # Manter na lista global para compatibilidade
                favorite_item = {
                    'id': fav.get('id'),
                    'title': title,
                    'price_per_night': fav.get('price_per_night'),
                    'location': fav.get('location'),
                    'is_beachfront': fav.get('is_beachfront', False),
                    'image_url': fav.get('image_url'),
                    'listing_url': url,
                    'added_date': fav.get('added_date'),
                    'last_sync': datetime.now().isoformat(),
                    'db_listing_id': listing_id
                }
                favorite_competitors.append(favorite_item)
                
            except Exception as e:
                error_msg = f"Erro ao processar favorito {fav.get('title', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        response_data = {
            'success': True,
            'message': f'{saved_count} favoritos salvos no banco de dados',
            'total_favorites': len(favorite_competitors),
            'saved_to_db': saved_count,
            'errors': errors
        }
        
        if errors:
            response_data['warning'] = f'{len(errors)} erros ocorreram durante o salvamento'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Erro geral na sincronização de favoritos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/run_analysis', methods=['POST'])
def api_run_analysis():
    """API para executar análise sob demanda"""
    global latest_analysis, analysis_history
    
    try:
        data = request.get_json()
        checkin = data.get('checkin')
        checkout = data.get('checkout')
        adults = data.get('adults', 2)
        beachfront = data.get('beachfront', True)
        period_type = data.get('period_type', 'weekend')
        listing_url = data.get('listing_url', '').strip()
        municipio_id = data.get('municipio_id')
        
        # Validar datas
        if not checkin or not checkout:
            # Usar próximo final de semana como padrão
            periods = get_next_weekends_and_weekdays()
            weekend_periods = [p for p in periods if p['type'] == 'weekend']
            if weekend_periods:
                checkin = weekend_periods[0]['checkin']
                checkout = weekend_periods[0]['checkout']
                period_type = 'weekend'
        
        # Validar se o link foi fornecido
        if not listing_url:
            return jsonify({
                'success': False,
                'error': 'Link do anúncio é obrigatório',
                'message': 'Por favor, informe o link do anúncio do Airbnb para análise'
            }), 400
        
        # Executar análise incluindo favoritos
        scraper = AirbnbClimateScraper()
        
        # Passar favoritos para o scraper temporariamente
        original_favorites = getattr(scraper, 'favorite_competitors', None)
        scraper.favorite_competitors = favorite_competitors
        
        try:
            result = scraper.run_competitive_analysis(checkin, checkout, beachfront, adults, listing_url)
        finally:
            # Restaurar estado original
            if original_favorites is not None:
                scraper.favorite_competitors = original_favorites
            else:
                delattr(scraper, 'favorite_competitors')
        
        # Calcular número de noites
        from datetime import datetime
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
        nights = (checkout_date - checkin_date).days
        
        # Extrair município do anúncio analisado
        extracted_municipality = None
        extracted_municipio_id = municipio_id  # Usar o ID do dropdown como fallback
        
        if result.get('competitive_data') and len(result['competitive_data']) > 0:
            extracted_municipality = result['competitive_data'][0].get('municipality')
            
            # Se extraiu um município, buscar seu ID no banco
            if extracted_municipality and db:
                municipio_data = db.get_municipio_by_nome(extracted_municipality, 'RJ')
                if municipio_data:
                    extracted_municipio_id = municipio_data['id']
                    print(f"🎯 Município '{extracted_municipality}' convertido para ID: {extracted_municipio_id}")
                else:
                    print(f"⚠️ Município '{extracted_municipality}' não encontrado no banco")
        
        # Adicionar informações do período
        result['timestamp'] = datetime.now().isoformat()
        result['checkin'] = checkin
        result['checkout'] = checkout
        result['adults'] = adults
        result['beachfront'] = beachfront
        result['period_type'] = period_type
        result['is_weekend'] = period_type == 'weekend'
        result['nights'] = nights
        result['municipio_id'] = extracted_municipio_id  # Usar o ID correto
        result['extracted_municipality'] = extracted_municipality
        
        # Salvar no banco de dados
        if db:
            try:
                # Obter user_id da sessão
                user_db_id = session.get('user_db_id')
                
                # Verificar se o link da análise corresponde a algum anúncio do usuário
                listing_id = None
                if user_db_id and listing_url:
                    user_listings = db.get_user_listings(user_db_id)
                    listing_found = False
                    
                    for listing in user_listings:
                        if listing_url in listing.get('url', '') or listing.get('url', '') in listing_url:
                            listing_id = listing['id']
                            listing_found = True
                            print(f"🎯 Análise associada ao anúncio existente: {listing['title']}")
                            break
                    
                    # Se o link não foi encontrado, salvar automaticamente na tabela user_listings
                    if not listing_found:
                        try:
                            # Extrair título do primeiro resultado da análise competitiva
                            listing_title = "Anúncio Analisado"
                            if result.get('competitive_data') and len(result['competitive_data']) > 0:
                                first_competitor = result['competitive_data'][0]
                                if first_competitor.get('title'):
                                    listing_title = first_competitor['title']
                            
                            # Salvar o link do anúncio automaticamente
                            listing_id = db.save_user_listing(
                                user_id=user_db_id,
                                title=listing_title,
                                url=listing_url,
                                municipio_id=extracted_municipio_id,
                                platform='airbnb',
                                is_beachfront=beachfront,
                                extraction_method='auto_analysis',
                                last_scraped=datetime.now().isoformat()
                            )
                            
                            if listing_id:
                                print(f"✅ Link do anúncio salvo automaticamente: {listing_title} (ID: {listing_id})")
                            else:
                                print("⚠️ Erro ao salvar link do anúncio automaticamente")
                                
                        except Exception as save_error:
                            print(f"⚠️ Erro ao salvar link automaticamente: {save_error}")
                            # Continuar com a análise mesmo se não conseguir salvar o link
                
                analysis_id = db.save_analysis(result, user_id=user_db_id, listing_id=listing_id)
                if analysis_id:
                    result['id'] = analysis_id
                    result['user_id'] = user_db_id
                    result['listing_id'] = listing_id
                    print(f"✅ Análise salva no banco com ID: {analysis_id}")
                    
                    # Salvar histórico de preços
                    if result.get('pricing_suggestion', {}).get('suggested_price'):
                        db.save_pricing_history(
                            checkin,
                            result['pricing_suggestion']['suggested_price'],
                            result['pricing_suggestion'].get('average_competitor_price', 0),
                            result['pricing_suggestion'].get('price_multiplier', 1.0)
                        )
                else:
                    print("⚠️ Erro ao salvar análise no banco")
            except Exception as e:
                print(f"⚠️ Erro ao salvar no banco: {e}")
        
        # Atualizar dados globais (fallback)
        latest_analysis = result
        analysis_history.append(result)
        
        # Manter apenas últimas 50 análises em memória
        if len(analysis_history) > 50:
            analysis_history.pop(0)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Análise executada com sucesso para {"final de semana" if period_type == "weekend" else "dias de semana"}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao executar análise'
        }), 500

@app.route('/api/start_monitoring', methods=['POST'])
def api_start_monitoring():
    """API para iniciar monitoramento automático"""
    global monitoring_active, monitoring_thread
    
    if monitoring_active:
        return jsonify({
            'success': False,
            'message': 'Monitoramento já está ativo'
        })
    
    try:
        data = request.get_json()
        beachfront = data.get('beachfront', True)
        
        def monitor_loop():
            global monitoring_active, latest_analysis, analysis_history
            
            scraper = AirbnbClimateScraper()
            
            while monitoring_active:
                try:
                    # Calcular próximo final de semana
                    today = datetime.now()
                    days_until_friday = (4 - today.weekday()) % 7
                    if days_until_friday == 0 and today.weekday() >= 4:
                        days_until_friday = 7
                    
                    next_friday = today + timedelta(days=days_until_friday)
                    next_sunday = next_friday + timedelta(days=2)
                    
                    checkin = next_friday.strftime('%Y-%m-%d')
                    checkout = next_sunday.strftime('%Y-%m-%d')
                    
                    # Executar análise
                    result = scraper.run_competitive_analysis(checkin, checkout, beachfront)
                    
                    # Adicionar timestamp
                    result['timestamp'] = datetime.now().isoformat()
                    result['checkin'] = checkin
                    result['checkout'] = checkout
                    result['beachfront'] = beachfront
                    result['auto_generated'] = True
                    
                    # Atualizar dados
                    latest_analysis = result
                    analysis_history.append(result)
                    
                    if len(analysis_history) > 50:
                        analysis_history.pop(0)
                    
                    print(f"✅ Análise automática executada: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                    
                except Exception as e:
                    print(f"❌ Erro na análise automática: {e}")
                
                # Aguardar 12 horas (2x ao dia)
                for _ in range(720):  # 720 minutos = 12 horas
                    if not monitoring_active:
                        break
                    time.sleep(60)  # 1 minuto
        
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitoring_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Monitoramento automático iniciado'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao iniciar monitoramento'
        }), 500

@app.route('/api/stop_monitoring', methods=['POST'])
def api_stop_monitoring():
    """API para parar monitoramento automático"""
    global monitoring_active
    
    monitoring_active = False
    
    return jsonify({
        'success': True,
        'message': 'Monitoramento automático parado'
    })

@app.route('/api/get_latest', methods=['GET'])
def api_get_latest():
    """API para obter última análise"""
    # Tentar buscar do banco primeiro
    if db:
        try:
            latest_db = db.get_latest_analysis()
            if latest_db:
                return jsonify({
                    'success': True,
                    'data': latest_db,
                    'monitoring_active': monitoring_active
                })
        except Exception as e:
            print(f"Erro ao buscar última análise do banco: {e}")
    
    # Fallback para dados em memória
    return jsonify({
        'success': True,
        'data': latest_analysis,
        'monitoring_active': monitoring_active
    })

@app.route('/api/get_history', methods=['GET'])
def api_get_history():
    """API para obter histórico de análises"""
    # Tentar buscar do banco primeiro
    if db:
        try:
            history_db = db.get_analysis_history(20)
            if history_db:
                return jsonify({
                    'success': True,
                    'data': history_db,
                    'total': len(history_db)
                })
        except Exception as e:
            print(f"Erro ao buscar histórico do banco: {e}")
    
    # Fallback para dados em memória
    return jsonify({
        'success': True,
        'data': analysis_history[-20:],  # Últimas 20
        'total': len(analysis_history)
    })

@app.route('/api/get_calendar_data', methods=['GET'])
def api_get_calendar_data():
    """Retorna dados de preços e clima para o calendário"""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if not month or not year:
            return jsonify({'success': False, 'error': 'Mês e ano são obrigatórios'})
        
        # Gerar dados para todos os dias do mês
        from calendar import monthrange
        _, days_in_month = monthrange(year, month)
        
        calendar_data = []
        
        for day in range(1, days_in_month + 1):
            date_obj = datetime(year, month, day)
            check_in = date_obj.strftime('%Y-%m-%d')
            check_out = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            
            try:
                # Usar o scraper para obter dados reais
                scraper = AirbnbClimateScraper()
                analysis_result = scraper.run_competitive_analysis(
                    check_in, check_out, 2
                )
                
                if analysis_result and 'pricing_suggestion' in analysis_result:
                    pricing = analysis_result['pricing_suggestion']
                    price = pricing.get('suggested_price', 200)
                    rain_probability = analysis_result.get('rain_probability', 0)
                    discount = pricing.get('discount_percentage', 0)
                else:
                    # Fallback para dados simulados
                    base_price = 200
                    day_of_week = date_obj.weekday()
                    is_weekend = day_of_week >= 5
                    
                    price = base_price + (50 if is_weekend else 0)
                    price += (day % 10) * 10  # Variação baseada no dia
                    rain_probability = (day * 7) % 100
                    discount = 5 + (day % 8)
                
            except Exception as e:
                print(f"Erro ao obter dados para {check_in}: {e}")
                # Dados simulados em caso de erro
                base_price = 200
                day_of_week = date_obj.weekday()
                is_weekend = day_of_week >= 5
                
                price = base_price + (50 if is_weekend else 0)
                price += (day % 10) * 10
                rain_probability = (day * 7) % 100
                discount = 5 + (day % 8)
            
            # Determinar ícone do clima
            if rain_probability <= 30:
                weather_icon = 'fas fa-sun'
                weather_class = 'sun-icon'
            elif rain_probability <= 60:
                weather_icon = 'fas fa-cloud-sun'
                weather_class = 'cloud-icon'
            else:
                weather_icon = 'fas fa-cloud-rain'
                weather_class = 'rain-icon'
            
            calendar_data.append({
                'day': day,
                'date': check_in,
                'price': int(price),
                'rain_probability': rain_probability,
                'discount': discount,
                'weather_icon': weather_icon,
                'weather_class': weather_class,
                'is_weekend': date_obj.weekday() >= 5
            })
        
        return jsonify({
            'success': True,
            'data': calendar_data,
            'month': month,
            'year': year
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao gerar dados do calendário: {str(e)}'
        })

@app.route('/api/similarity_analysis', methods=['POST'])
def api_similarity_analysis():
    """API para análise de similaridade com anúncio de referência"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['checkin_date', 'checkout_date', 'reference_listing']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório ausente: {field}'
                }), 400
        
        checkin_date = data['checkin_date']
        checkout_date = data['checkout_date']
        adults = data.get('adults', 2)
        reference_listing = data['reference_listing']
        
        # Validar estrutura do anúncio de referência
        ref_required = ['title', 'image_url']
        for field in ref_required:
            if field not in reference_listing:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório no anúncio de referência: {field}'
                }), 400
        
        print(f"🔍 Iniciando análise de similaridade...")
        print(f"📅 Período: {checkin_date} a {checkout_date}")
        print(f"🏠 Anúncio de referência: {reference_listing['title'][:50]}...")
        
        # Criar instância do scraper
        scraper = AirbnbClimateScraper()
        
        # Executar análise competitiva com similaridade
        competitive_result = scraper.get_competitive_analysis(
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=adults,
            reference_listing=reference_listing
        )
        
        # Processar resultados
        if isinstance(competitive_result, dict) and 'listings' in competitive_result:
            competitive_data = competitive_result['listings']
            total_found = competitive_result.get('total_found', 0)
            similar_count = len(competitive_data)  # Usar o tamanho real da lista retornada
            similarity_enabled = competitive_result.get('similarity_enabled', False)
        else:
            # Compatibilidade com formato antigo
            competitive_data = competitive_result if isinstance(competitive_result, list) else []
            total_found = len(competitive_data)
            similar_count = len(competitive_data)
            similarity_enabled = False
        
        # Calcular estatísticas
        if competitive_data:
            prices = [listing.get('price_per_night', 0) for listing in competitive_data if listing.get('price_per_night', 0) > 0]
            avg_price = sum(prices) / len(prices) if prices else 0
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
            
            # Contar anúncios com alta similaridade (score > 60)
            high_similarity_count = sum(1 for listing in competitive_data 
                                      if listing.get('similarity_analysis', {}).get('total_score', 0) > 60)
            
            # Se não há análise de similaridade, considerar todos como similares
            if not any(listing.get('similarity_analysis') for listing in competitive_data):
                high_similarity_count = len(competitive_data)
        else:
            avg_price = min_price = max_price = 0
            high_similarity_count = 0
        
        # Preparar resposta
        response_data = {
            'success': True,
            'analysis_type': 'similarity',
            'reference_listing': {
                'title': reference_listing['title'],
                'image_url': reference_listing.get('image_url', ''),
                'is_beachfront': reference_listing.get('is_beachfront', False)
            },
            'period': {
                'checkin': checkin_date,
                'checkout': checkout_date,
                'adults': adults
            },
            'statistics': {
                'total_found': total_found,
                'similar_count': similar_count,
                'high_similarity_count': high_similarity_count,
                'average_price': round(avg_price, 2),
                'price_range': {
                    'min': round(min_price, 2),
                    'max': round(max_price, 2)
                },
                'similarity_enabled': similarity_enabled
            },
            'similar_listings': competitive_data[:20],  # Limitar a 20 para performance
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Análise concluída: {similar_count} anúncios similares de {total_found} encontrados")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Erro na análise de similaridade: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na análise de similaridade: {str(e)}'
        }), 500

@app.route('/api/municipios', methods=['GET'])
def api_get_municipios():
    """Retorna lista de todos os municípios"""
    try:
        if db:
            municipios = db.get_all_municipios()
            return jsonify({
                'success': True,
                'municipios': municipios
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Banco de dados não disponível'
            })
    except Exception as e:
        print(f"Erro ao buscar municípios: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/municipios/<estado>', methods=['GET'])
def api_get_municipios_by_estado(estado):
    """Retorna municípios de um estado específico"""
    try:
        if db:
            municipios = db.get_municipios_by_estado(estado)
            return jsonify({
                'success': True,
                'municipios': municipios
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Banco de dados não disponível'
            })
    except Exception as e:
        print(f"Erro ao buscar municípios do estado {estado}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/municipios', methods=['POST'])
def api_create_municipio():
    """Cria um novo município"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['nome', 'estado', 'regiao']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                })
        
        if db:
            # Verificar se município já existe
            existing = db.get_municipio_by_nome(data['nome'], data['estado'])
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Município já existe neste estado'
                })
            
            municipio_id = db.save_municipio(
                nome=data['nome'],
                estado=data['estado'],
                regiao=data['regiao'],
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                populacao=data.get('populacao'),
                codigo_ibge=data.get('codigo_ibge')
            )
            
            if municipio_id:
                return jsonify({
                    'success': True,
                    'municipio_id': municipio_id,
                    'message': 'Município criado com sucesso'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Erro ao salvar município'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Banco de dados não disponível'
            })
    except Exception as e:
        print(f"Erro ao criar município: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/municipios/search', methods=['GET'])
def api_search_municipio():
    """Busca município por nome"""
    try:
        nome = request.args.get('nome')
        estado = request.args.get('estado', 'RJ')  # Default para RJ
        
        if not nome:
            return jsonify({
                'success': False,
                'error': 'Nome do município é obrigatório'
            })
        
        if db:
            municipio = db.get_municipio_by_nome(nome, estado)
            return jsonify({
                'success': True,
                'municipio': municipio
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Banco de dados não disponível'
            })
    except Exception as e:
        print(f"Erro ao buscar município: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/update-data', methods=['POST'])
def api_update_data():
    """Atualiza dados das tabelas com informações da internet"""
    global latest_analysis, analysis_history
    
    try:
        print("🔄 Iniciando atualização de dados da internet...")
        
        # Verificar se há uma análise recente para re-executar
        if not latest_analysis:
            return jsonify({
                'success': False,
                'error': 'Nenhuma análise disponível para atualizar'
            })
        
        # Extrair dados da última análise
        checkin = latest_analysis.get('checkin')
        checkout = latest_analysis.get('checkout')
        adults = latest_analysis.get('adults', 2)
        beachfront = latest_analysis.get('beachfront', True)
        municipio_id = latest_analysis.get('municipio_id')
        
        # Buscar URL do anúncio na última análise
        listing_url = None
        if latest_analysis.get('competitors'):
            # Tentar encontrar URL nos concorrentes ou usar um padrão
            for competitor in latest_analysis['competitors']:
                if competitor.get('url'):
                    listing_url = competitor['url']
                    break
        
        if not listing_url:
            # Se não encontrar URL, usar um padrão ou solicitar
            return jsonify({
                'success': False,
                'error': 'URL do anúncio não encontrada na última análise. Execute uma nova análise primeiro.'
            })
        
        # Executar nova análise com dados atualizados da internet
        scraper = AirbnbClimateScraper()
        
        # Passar favoritos para o scraper
        scraper.favorite_competitors = favorite_competitors
        
        try:
            print(f"🌐 Buscando dados atualizados para {checkin} - {checkout}")
            result = scraper.run_competitive_analysis(checkin, checkout, beachfront, adults, listing_url)
        finally:
            # Limpar favoritos do scraper
            if hasattr(scraper, 'favorite_competitors'):
                delattr(scraper, 'favorite_competitors')
        
        # Adicionar informações do período
        result['timestamp'] = datetime.now().isoformat()
        result['checkin'] = checkin
        result['checkout'] = checkout
        result['adults'] = adults
        result['beachfront'] = beachfront
        
        # Extrair município do resultado da análise e converter para ID
        extracted_municipality = result.get('competitive_data', {}).get('extracted_municipality')
        if extracted_municipality and db:
            try:
                municipio_data = db.get_municipio_by_nome(extracted_municipality, 'RJ')
                if municipio_data:
                    municipio_id = municipio_data['id']
                    print(f"✅ Município atualizado: {extracted_municipality} -> ID: {municipio_id}")
                else:
                    print(f"⚠️ Município '{extracted_municipality}' não encontrado no banco")
            except Exception as e:
                print(f"⚠️ Erro ao buscar município: {e}")
        
        result['municipio_id'] = municipio_id
        result['extracted_municipality'] = extracted_municipality
        
        # Calcular número de noites
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
        nights = (checkout_date - checkin_date).days
        result['nights'] = nights
        result['is_weekend'] = latest_analysis.get('is_weekend', False)
        result['period_type'] = latest_analysis.get('period_type', 'weekend')
        
        # Salvar no banco de dados
        if db:
            try:
                analysis_id = db.save_analysis(result)
                if analysis_id:
                    result['id'] = analysis_id
                    print(f"✅ Dados atualizados salvos no banco com ID: {analysis_id}")
                    
                    # Salvar histórico de preços atualizado
                    if result.get('pricing_suggestion', {}).get('suggested_price'):
                        db.save_pricing_history(
                            checkin,
                            result['pricing_suggestion']['suggested_price'],
                            result['pricing_suggestion'].get('average_competitor_price', 0),
                            result['pricing_suggestion'].get('price_multiplier', 1.0)
                        )
                else:
                    print("⚠️ Erro ao salvar dados atualizados no banco")
            except Exception as e:
                print(f"⚠️ Erro ao salvar no banco: {e}")
        
        # Atualizar dados globais
        latest_analysis = result
        analysis_history.append(result)
        
        # Manter apenas últimas 50 análises em memória
        if len(analysis_history) > 50:
            analysis_history.pop(0)
        
        print("✅ Dados atualizados com sucesso da internet!")
        
        return jsonify({
            'success': True,
            'message': 'Dados atualizados com sucesso da internet',
            'data': {
                'timestamp': result['timestamp'],
                'suggested_price': result.get('pricing_suggestion', {}).get('suggested_price'),
                'competitors_found': len(result.get('competitors', [])),
                'weather_updated': bool(result.get('weather_data'))
            }
        })
        
    except Exception as e:
        print(f"❌ Erro ao atualizar dados: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro ao atualizar dados: {str(e)}'
        })



@app.route('/health')
def health_check():
    """Endpoint de health check para monitoramento"""
    try:
        # Verificar conexão com banco
        db = get_database()
        if db:
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'version': '1.0.0'
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'disconnected',
                'error': 'Database connection failed'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

@app.route('/api/monitor')
def api_monitor():
    """Endpoint para monitoramento automático"""
    try:
        # Executar análise automática se configurado
        # (implementar lógica de monitoramento aqui)
        return jsonify({
            'status': 'monitoring_executed',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'monitoring_failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    print("🌐 Iniciando aplicação web...")
    print("📊 Acesse: http://localhost:5000")
    print("⚠️ Para parar, pressione Ctrl+C")
    
    app.run(debug=True, host='0.0.0.0', port=5000)