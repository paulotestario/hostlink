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

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validações
        if not name or len(name) < 2:
            flash('Nome deve ter pelo menos 2 caracteres.', 'error')
            return render_template('register.html')
        
        if not email or '@' not in email:
            flash('Email inválido.', 'error')
            return render_template('register.html')
        
        if not password or len(password) < 6:
            flash('Senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Senhas não coincidem.', 'error')
            return render_template('register.html')
        
        # Verificar se email já existe e qual tipo de autenticação
        db = get_database()
        if db:
            auth_type = db.check_email_auth_type(email)
            if auth_type == 'google':
                flash('Este email já está cadastrado com conta Google. Por favor, faça login usando sua conta Google.', 'error')
                return render_template('register.html')
            elif auth_type == 'email':
                flash('Este email já está cadastrado.', 'error')
                return render_template('register.html')
        
        # Criar usuário
        user = User.create_email_user(email, name, password)
        if user:
            login_user(user, remember=True)
            flash(f'Conta criada com sucesso! Bem-vindo, {user.name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Erro ao criar conta. Tente novamente.', 'error')
    
    return render_template('register.html')

@app.route('/auth/email', methods=['POST'])
def auth_email():
    """Autenticação por email e senha"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not email or not password:
        flash('Email e senha são obrigatórios.', 'error')
        return redirect(url_for('login'))
    
    # Verificar se email existe e qual tipo de autenticação
    db = get_database()
    if db:
        auth_type = db.check_email_auth_type(email)
        if auth_type == 'google':
            flash('Este email está associado a uma conta Google. Por favor, faça login usando sua conta Google.', 'error')
            return redirect(url_for('login'))
        elif auth_type is None:
            flash('Email não encontrado. Verifique o email ou crie uma nova conta.', 'error')
            return redirect(url_for('login'))
    
    # Autenticar usuário
    user = User.authenticate_email(email, password)
    if user:
        login_user(user, remember=True)
        flash(f'Bem-vindo de volta, {user.name}!', 'success')
        
        # Redirecionar para página solicitada ou página inicial
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))
    else:
        flash('Email ou senha incorretos.', 'error')
        return redirect(url_for('login'))

@app.route('/check-email-auth-type', methods=['POST'])
def check_email_auth_type():
    """Verifica o tipo de autenticação de um email via AJAX"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'auth_type': None})
        
        # Verificar tipo de autenticação do email
        db = get_database()
        if db:
            auth_type = db.check_email_auth_type(email)
            return jsonify({'auth_type': auth_type})
        else:
            return jsonify({'auth_type': None})
            
    except Exception as e:
        print(f"Erro ao verificar tipo de autenticação do email: {e}")
        return jsonify({'auth_type': None})

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

@app.route('/minhas_reservas')
@app.route('/minhas-reservas')
@login_required
def minhas_reservas():
    """Página das reservas do usuário"""
    user_db_id = session.get('user_db_id')
    current_user_db_id = getattr(current_user, 'db_id', None)
    
    print(f"🔍 Debug minhas_reservas: session user_db_id = {user_db_id}")
    print(f"🔍 Debug minhas_reservas: current_user.db_id = {current_user_db_id}")
    print(f"🔍 Debug minhas_reservas: current_user.id = {current_user.id}")
    print(f"🔍 Debug minhas_reservas: current_user.email = {current_user.email}")
    
    # Usar o db_id do current_user se disponível, senão usar da sessão
    effective_user_id = current_user_db_id or user_db_id
    
    # Cada usuário deve ver apenas suas próprias reservas
    print(f"🔍 Buscando reservas para usuário: {current_user.email} (ID: {effective_user_id})")
    
    if not effective_user_id or not db:
        print(f"❌ Erro: effective_user_id={effective_user_id}, db={db}")
        flash('Erro ao carregar reservas do usuário', 'error')
        return redirect(url_for('index'))
    
    try:
        # Buscar todas as reservas do usuário
        bookings = db.get_user_bookings(effective_user_id)
        print(f"🔍 Debug: Encontradas {len(bookings) if bookings else 0} reservas para user_id {effective_user_id}")
        
        # Não buscar reservas de outros usuários - cada usuário vê apenas as suas próprias
        
        return render_template('minhas_reservas.html', 
                             bookings=bookings,
                             current_user=current_user)
    except Exception as e:
        print(f"❌ Erro ao carregar reservas: {e}")
        flash('Erro ao carregar reservas', 'error')
        return redirect(url_for('index'))

@app.route('/favoritos')
@login_required
def favoritos():
    """Página de favoritos do usuário"""
    return render_template('favoritos.html')

@app.route('/hosting')
@login_required
def hosting():
    """Página de hospedagem - gerenciar anúncios"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        flash('Erro ao carregar página de hospedagem', 'error')
        return redirect(url_for('index'))
    
    try:
        # Buscar anúncios do usuário (apenas regulares, não favoritos de similaridade)
        all_listings = db.get_user_listings(user_db_id)
        user_listings = [l for l in all_listings if l.get('platform') != 'airbnb_similarity']
        
        return render_template('hosting.html', user_listings=user_listings)
    except Exception as e:
        print(f"❌ Erro ao carregar página de hospedagem: {e}")
        flash('Erro ao carregar dados da hospedagem', 'error')
        return render_template('hosting.html', user_listings=[])

@app.route('/anuncios')
def anuncios_publicos():
    """Página pública para listar todos os anúncios disponíveis"""
    try:
        # Verificar se o usuário está logado
        user_logged_in = current_user.is_authenticated
        user_info = None
        
        if user_logged_in:
            user_info = {
                'id': current_user.id,
                'name': current_user.name,
                'email': current_user.email
            }
        
        return render_template('anuncios_publicos.html', 
                             user_logged_in=user_logged_in, 
                             user_info=user_info)
    except Exception as e:
        print(f"❌ Erro ao carregar página de anúncios públicos: {e}")
        return render_template('anuncios_publicos.html', 
                             user_logged_in=False, 
                             user_info=None)

@app.route('/viagens')
@login_required
def viagens():
    """Rota para viagens - redireciona para anúncios públicos"""
    return redirect(url_for('anuncios_publicos'))

@app.route('/anuncios/<int:listing_id>')
def view_anuncio(listing_id):
    """Página para visualizar um anúncio específico"""
    try:
        # Verificar se o usuário está logado
        user_logged_in = current_user.is_authenticated
        user_info = None
        
        if user_logged_in:
            user_info = {
                'id': current_user.id,
                'name': current_user.name,
                'email': current_user.email
            }
        
        # Buscar o anúncio específico
        listing = db.get_public_listing_by_id(listing_id)
        
        if not listing:
            flash('Anúncio não encontrado', 'error')
            return redirect(url_for('anuncios_publicos'))
        
        return render_template('view_anuncio.html', 
                             listing=listing,
                             user_logged_in=user_logged_in, 
                             user_info=user_info)
    except Exception as e:
        print(f"❌ Erro ao carregar anúncio: {e}")
        flash('Erro ao carregar anúncio', 'error')
        return redirect(url_for('anuncios_publicos'))

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
        print(f"❌ Erro ao deletar anúncio: {e}")
        return jsonify({'success': False, 'error': str(e)})

def upload_single_image(file):
    """Função auxiliar para upload de uma única imagem"""
    try:
        if not file or file.filename == '':
            return {'success': False, 'error': 'Nenhuma imagem selecionada'}
        
        # Verificar se é uma imagem válida
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return {'success': False, 'error': 'Formato de imagem não suportado'}
        
        # Criar diretório de uploads se não existir
        upload_dir = os.path.join(app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Gerar nome único para o arquivo
        import uuid
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Salvar arquivo
        file.save(file_path)
        
        # Retornar dados da imagem
        return {
            'success': True, 
            'filename': unique_filename,
            'url': f"/static/uploads/{unique_filename}"
        }
        
    except Exception as e:
        print(f"❌ Erro no upload de imagem: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/api/upload_image', methods=['POST'])
@login_required
def upload_image():
    """Upload de imagem para anúncio"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhuma imagem enviada'})
        
        file = request.files['image']
        result = upload_single_image(file)
        
        if result['success']:
            return jsonify({'success': True, 'image_url': result['url']})
        else:
            return jsonify(result)
        
    except Exception as e:
        print(f"❌ Erro no upload de imagem: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/listings', methods=['GET'])
@login_required
def get_user_listings():
    """Busca todos os anúncios do usuário"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        listings = db.get_user_listings(user_db_id)
        return jsonify({'success': True, 'listings': listings})
    except Exception as e:
        print(f"❌ Erro ao buscar anúncios: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/listing', methods=['POST'])
@login_required
def create_listing():
    """Cria um novo anúncio"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        # Obter dados do formulário (FormData)
        data = request.form.to_dict()
        
        # Validar dados obrigatórios
        if not data.get('title'):
            return jsonify({'success': False, 'error': 'Título é obrigatório'})
        
        # Processar upload de imagens
        uploaded_images = []
        if 'listingImages' in request.files:
            files = request.files.getlist('listingImages')
            for file in files:
                if file and file.filename:
                    try:
                        # Usar a função de upload existente
                        result = upload_single_image(file)
                        if result['success']:
                            uploaded_images.append(result['url'])
                    except Exception as img_error:
                        print(f"⚠️ Erro ao fazer upload da imagem: {img_error}")
        
        # Buscar município se fornecido
        municipio_id = None
        if data.get('municipio_nome'):
            municipio = db.get_municipio_by_nome(data['municipio_nome'])
            if municipio:
                municipio_id = municipio['id']
        
        # Preparar dados para salvar
        listing_data = {
            'user_id': user_db_id,
            'title': data['title'],
            'url': data.get('url', ''),
            'platform': data.get('platform', 'manual'),
            'property_type': data.get('property_type', 'Casa'),
            'max_guests': int(data['max_guests']) if data.get('max_guests') else 2,
            'bedrooms': int(data['bedrooms']) if data.get('bedrooms') else 1,
            'bathrooms': int(data['bathrooms']) if data.get('bathrooms') else 1,
            'municipio_id': municipio_id,
            'price_per_night': float(data.get('price_per_night', 0)),
            'minimum_nights': int(data.get('minimum_nights', 1)),
            'description': data.get('description', ''),
            'address': data.get('address', ''),
            'amenities': [],
            'image_url': uploaded_images[0] if uploaded_images else (None if data.get('remove_existing_image') == 'true' else None),
            'is_active': True
        }
        
        # Salvar no banco
        listing_id = db.save_user_listing(**listing_data)
        
        if listing_id:
            return jsonify({'success': True, 'listing_id': listing_id})
        else:
            return jsonify({'success': False, 'error': 'Erro ao salvar anúncio'})
            
    except Exception as e:
        print(f"❌ Erro ao criar anúncio: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/listing/<int:listing_id>', methods=['GET'])
@login_required
def get_listing_api(listing_id):
    """Busca dados de um anúncio específico"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        # Buscar o anúncio específico
        listings = db.get_user_listings(user_db_id)
        listing = next((l for l in listings if l.get('id') == listing_id), None)
        
        if not listing:
            return jsonify({'success': False, 'error': 'Anúncio não encontrado'})
        

        return jsonify({'success': True, 'listing': listing})
    except Exception as e:
        print(f"❌ Erro ao buscar anúncio: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/listing/<int:listing_id>', methods=['PUT'])
@login_required
def update_listing_api(listing_id):
    """Atualiza um anúncio existente"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        print(f"❌ Erro: Usuário não encontrado - user_db_id: {user_db_id}, db: {db}")
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        print(f"🔍 Iniciando atualização do anúncio ID: {listing_id}")
        
        # Obter dados do FormData
        data = request.form.to_dict()
        print(f"📝 Dados recebidos do formulário: {data}")
        
        # Processar upload de imagens
        uploaded_images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            print(f"📸 Processando {len(files)} novas imagens")
            for file in files:
                if file and file.filename:
                    try:
                        result = upload_single_image(file)
                        if result['success']:
                            uploaded_images.append(result['url'])
                            print(f"✅ Imagem carregada: {result['url']}")
                    except Exception as img_error:
                        print(f"⚠️ Erro ao fazer upload da imagem: {img_error}")
        
        # Buscar município se fornecido
        municipio_id = None
        if data.get('municipio_nome'):
            print(f"🏙️ Buscando município: {data['municipio_nome']}")
            municipio = db.get_municipio_by_nome(data['municipio_nome'])
            if municipio:
                municipio_id = municipio['id']
                print(f"✅ Município encontrado - ID: {municipio_id}")
            else:
                print(f"⚠️ Município não encontrado: {data['municipio_nome']}")
        
        # Preparar dados para atualizar
        listing_data = {
            'title': data.get('title'),
            'url': data.get('url'),
            'platform': data.get('platform'),
            'property_type': data.get('property_type'),
            'max_guests': int(data['max_guests']) if data.get('max_guests') else None,
            'bedrooms': int(data['bedrooms']) if data.get('bedrooms') else None,
            'bathrooms': int(data['bathrooms']) if data.get('bathrooms') else None,
            'municipio_id': municipio_id,
            'price_per_night': float(data['price_per_night']) if data.get('price_per_night') else None,
            'minimum_nights': int(data['minimum_nights']) if data.get('minimum_nights') else None,
            'description': data.get('description'),
            'address': data.get('address'),
            'amenities': data.get('amenities'),
            'is_active': data.get('is_active', True)
        }
        
        # Lidar com image_url separadamente
        if uploaded_images:
            # Nova imagem foi carregada
            listing_data['image_url'] = uploaded_images[0]
        elif data.get('remove_existing_image') == 'true':
            # Remover imagem existente
            listing_data['image_url'] = None
        # Se não há nova imagem e não está removendo, não incluir image_url na atualização
        
        # Remover campos None (exceto image_url se foi explicitamente removida)
        if data.get('remove_existing_image') == 'true':
            # Manter image_url=None para remover a imagem existente
            listing_data = {k: v for k, v in listing_data.items() if v is not None or k == 'image_url'}
        else:
            listing_data = {k: v for k, v in listing_data.items() if v is not None}
        print(f"📊 Dados preparados para atualização: {listing_data}")
        
        # Atualizar no banco
        print(f"💾 Chamando db.update_user_listing({listing_id}, **listing_data)")
        success = db.update_user_listing(listing_id, **listing_data)
        print(f"📈 Resultado da atualização: {success}")
        
        if success:
            print(f"✅ Anúncio {listing_id} atualizado com sucesso")
        else:
            print(f"❌ Falha ao atualizar anúncio {listing_id}")
        
        return jsonify({'success': success})
            
    except Exception as e:
        print(f"❌ Erro ao atualizar anúncio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/listing/<int:listing_id>', methods=['DELETE'])
@login_required
def delete_listing_api(listing_id):
    """Remove um anúncio"""
    user_db_id = session.get('user_db_id')
    if not user_db_id or not db:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    try:
        success = db.delete_user_listing(listing_id, user_db_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"❌ Erro ao deletar anúncio: {e}")
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

# =====================================================
# NOVAS ROTAS DE API PARA FAVORITOS (BANCO DE DADOS)
# =====================================================

@app.route('/api/favorites/add', methods=['POST'])
@login_required
def api_add_favorite_db():
    """API para adicionar anúncio aos favoritos (banco de dados)"""
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        
        if not listing_id:
            return jsonify({
                'success': False,
                'error': 'ID do anúncio é obrigatório'
            }), 400
        
        user_id = current_user.db_id
        
        # Verificar se o anúncio existe
        listing = db.get_public_listing_by_id(listing_id)
        if not listing:
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        # Adicionar aos favoritos
        success = db.add_favorite(user_id, listing_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Anúncio adicionado aos favoritos',
                'listing': {
                    'id': listing['id'],
                    'title': listing['title'],
                    'url': listing['url']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao adicionar aos favoritos'
            }), 500
            
    except Exception as e:
        print(f"❌ Erro ao adicionar favorito: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/favorites/remove', methods=['POST'])
@login_required
def api_remove_favorite_db():
    """API para remover anúncio dos favoritos (banco de dados)"""
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        
        if not listing_id:
            return jsonify({
                'success': False,
                'error': 'ID do anúncio é obrigatório'
            }), 400
        
        user_id = current_user.db_id
        
        # Remover dos favoritos
        success = db.remove_favorite(user_id, listing_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Anúncio removido dos favoritos'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao remover dos favoritos'
            }), 500
            
    except Exception as e:
        print(f"❌ Erro ao remover favorito: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/favorites/list', methods=['GET'])
@login_required
def api_list_favorites_db():
    """API para listar favoritos do usuário (banco de dados)"""
    try:
        user_id = current_user.db_id
        favorites = db.get_user_favorites(user_id)
        
        # Formatar dados para o frontend
        formatted_favorites = []
        for fav in favorites:
            listing = fav.get('user_listings', {})
            municipio = listing.get('municipios', {})
            
            formatted_favorites.append({
                'favorite_id': fav['id'],
                'listing_id': listing.get('id'),
                'title': listing.get('title', 'Título não disponível'),
                'url': listing.get('url'),
                'price_per_night': listing.get('price_per_night'),
                'rating': listing.get('rating'),
                'reviews': listing.get('reviews'),
                'image_url': listing.get('image_url'),
                'location': municipio.get('nome') if municipio else 'Localização não informada',
                'state': municipio.get('estado') if municipio else '',
                'is_beachfront': listing.get('is_beachfront', False),
                'platform': listing.get('platform', 'airbnb'),
                'added_at': fav['created_at']
            })
        
        return jsonify({
            'success': True,
            'data': formatted_favorites,
            'total': len(formatted_favorites)
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar favoritos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/favorites/check', methods=['POST'])
@login_required
def api_check_favorite_db():
    """API para verificar se um anúncio é favorito (banco de dados)"""
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        
        if not listing_id:
            return jsonify({
                'success': False,
                'error': 'ID do anúncio é obrigatório'
            }), 400
        
        user_id = current_user.db_id
        is_favorite = db.is_favorite(user_id, listing_id)
        
        return jsonify({
            'success': True,
            'is_favorite': is_favorite
        })
        
    except Exception as e:
        print(f"❌ Erro ao verificar favorito: {e}")
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

# API Routes para Agenda/Disponibilidade
@app.route('/api/agenda/availability', methods=['POST'])
@login_required
def save_availability():
    """Salva disponibilidade de datas para um anúncio"""
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        price_per_night = data.get('price_per_night')
        
        if not all([listing_id, start_date, end_date, price_per_night]):
            return jsonify({
                'success': False,
                'error': 'Todos os campos são obrigatórios'
            }), 400
        
        # Verificar se o anúncio pertence ao usuário
        user_db_id = session.get('user_db_id')
        listings = db.get_user_listings(user_db_id)
        if not any(l.get('id') == listing_id for l in listings):
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        # Salvar disponibilidade
        success = db.save_listing_availability_period(
            listing_id=listing_id,
            user_id=user_db_id,
            start_date=start_date,
            end_date=end_date,
            price_per_night=price_per_night
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Disponibilidade salva com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao salvar disponibilidade'
            }), 500
        
    except Exception as e:
        print(f"❌ Erro ao salvar disponibilidade: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agenda/availability/<int:listing_id>', methods=['GET'])
@login_required
def get_availability(listing_id):
    """Busca disponibilidade de um anúncio"""
    try:
        # Verificar se o anúncio pertence ao usuário
        user_db_id = session.get('user_db_id')
        listings = db.get_user_listings(user_db_id)
        if not any(l.get('id') == listing_id for l in listings):
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        availability = db.get_listing_availability(listing_id)
        
        return jsonify({
            'success': True,
            'availability': availability
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar disponibilidade: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agenda/available-dates/<int:listing_id>', methods=['GET'])
@login_required
def get_available_dates(listing_id):
    """Busca datas disponíveis para reserva"""
    try:
        # Verificar se o anúncio pertence ao usuário
        user_db_id = session.get('user_db_id')
        listings = db.get_user_listings(user_db_id)
        if not any(l.get('id') == listing_id for l in listings):
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        # Definir período padrão (próximos 6 meses)
        from datetime import datetime, timedelta
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
        
        available_dates = db.get_available_dates(listing_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'available_dates': available_dates
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar datas disponíveis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agenda/availability/<int:listing_id>/<date>', methods=['DELETE'])
@login_required
def delete_availability(listing_id, date):
    """Remove disponibilidade de uma data específica"""
    try:
        # Verificar se o anúncio pertence ao usuário
        user_db_id = session.get('user_db_id')
        listings = db.get_user_listings(user_db_id)
        if not any(l.get('id') == listing_id for l in listings):
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        # Remover disponibilidade
        success = db.delete_listing_availability(
            listing_id=listing_id,
            date=date,
            user_id=user_db_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Disponibilidade removida com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao remover disponibilidade'
            }), 500
        
    except Exception as e:
        print(f"❌ Erro ao remover disponibilidade: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agenda/booking', methods=['POST'])
@login_required
def create_booking():
    """Cria uma nova reserva"""
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        guest_user_id = data.get('guest_user_id')
        checkin_date = data.get('checkin_date')
        checkout_date = data.get('checkout_date')
        total_price = data.get('total_price')
        guest_count = data.get('guest_count', 1)
        
        if not all([listing_id, guest_user_id, checkin_date, checkout_date, total_price]):
            return jsonify({
                'success': False,
                'error': 'Todos os campos são obrigatórios'
            }), 400
        
        # Verificar se o usuário não é o dono do anúncio
        listing = db.get_public_listing_by_id(listing_id)
        if not listing:
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        if listing.get('user_id') == guest_user_id:
            return jsonify({
                'success': False,
                'error': 'Você não pode reservar seu próprio anúncio'
            }), 400
        
        # Salvar reserva
        booking_id = db.save_booking(
            listing_id=listing_id,
            guest_user_id=guest_user_id,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            total_price=total_price,
            guest_count=guest_count
        )
        
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'message': 'Reserva criada com sucesso'
        })
        
    except Exception as e:
        print(f"❌ Erro ao criar reserva: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agenda/bookings/<int:listing_id>', methods=['GET'])
@login_required
def get_bookings(listing_id):
    """Busca reservas de um anúncio (excluindo canceladas)"""
    try:
        # Verificar se o anúncio pertence ao usuário
        user_db_id = session.get('user_db_id')
        listings = db.get_user_listings(user_db_id)
        if not any(l.get('id') == listing_id for l in listings):
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        # Buscar todas as reservas e filtrar canceladas
        all_bookings = db.get_listing_bookings(listing_id)
        bookings = [booking for booking in all_bookings if booking.get('status') != 'cancelled']
        
        return jsonify({
            'success': True,
            'bookings': bookings
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar reservas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agenda/recent-bookings/<int:listing_id>', methods=['GET'])
@login_required
def get_recent_bookings(listing_id):
    """Busca todas as reservas de um anúncio (incluindo canceladas) para exibição recente"""
    try:
        # Verificar se o anúncio pertence ao usuário
        user_db_id = session.get('user_db_id')
        listings = db.get_user_listings(user_db_id)
        if not any(l.get('id') == listing_id for l in listings):
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        # Buscar todas as reservas (incluindo canceladas)
        bookings = db.get_listing_bookings(listing_id)
        
        return jsonify({
            'success': True,
            'bookings': bookings
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar reservas recentes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancelar uma reserva - permitido para hóspede e anfitrião"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        # Buscar a reserva específica
        booking_result = db.supabase.table('listing_bookings').select(
            '*, user_listings(user_id, title)'
        ).eq('id', booking_id).execute()
        
        if not booking_result.data:
            return jsonify({
                'success': False,
                'error': 'Reserva não encontrada'
            }), 404
        
        booking = booking_result.data[0]
        
        # Verificar se o usuário pode cancelar a reserva
        # Pode cancelar se for:
        # 1. O hóspede (guest_user_id)
        # 2. O anfitrião (dono do anúncio)
        can_cancel = (
            booking.get('guest_user_id') == user_db_id or  # É o hóspede
            booking.get('user_listings', {}).get('user_id') == user_db_id  # É o anfitrião
        )
        
        if not can_cancel:
            return jsonify({
                'success': False,
                'error': 'Você não tem permissão para cancelar esta reserva'
            }), 403
        
        # Atualizar status da reserva para 'cancelled'
        success = db.update_booking_status(booking_id, 'cancelled')
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Reserva cancelada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao cancelar reserva'
            }), 500
            
    except Exception as e:
        print(f"Erro ao cancelar reserva: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/confirm-booking/<int:booking_id>', methods=['POST'])
@login_required
def confirm_booking(booking_id):
    """Confirmar uma reserva - permitido apenas para anfitrião"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        # Buscar a reserva específica
        booking_result = db.supabase.table('listing_bookings').select(
            '*, user_listings(user_id, title)'
        ).eq('id', booking_id).execute()
        
        if not booking_result.data:
            return jsonify({
                'success': False,
                'error': 'Reserva não encontrada'
            }), 404
        
        booking = booking_result.data[0]
        
        # Verificar se o usuário é o anfitrião (dono do anúncio)
        if booking.get('user_listings', {}).get('user_id') != user_db_id:
            return jsonify({
                'success': False,
                'error': 'Você não tem permissão para confirmar esta reserva'
            }), 403
        
        # Verificar se a reserva está pendente
        if booking.get('status') != 'pending':
            return jsonify({
                'success': False,
                'error': 'Apenas reservas pendentes podem ser confirmadas'
            }), 400
        
        # Atualizar status da reserva para 'confirmed'
        success = db.update_booking_status(booking_id, 'confirmed')
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Reserva confirmada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao confirmar reserva'
            }), 500
            
    except Exception as e:
        print(f"Erro ao confirmar reserva: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/complete-booking/<int:booking_id>', methods=['POST'])
@login_required
def complete_booking(booking_id):
    """Marcar uma reserva como concluída - permitido apenas para anfitrião"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        # Buscar a reserva específica
        booking_result = db.supabase.table('listing_bookings').select(
            '*, user_listings(user_id, title)'
        ).eq('id', booking_id).execute()
        
        if not booking_result.data:
            return jsonify({
                'success': False,
                'error': 'Reserva não encontrada'
            }), 404
        
        booking = booking_result.data[0]
        
        # Verificar se o usuário é o anfitrião (dono do anúncio)
        if booking.get('user_listings', {}).get('user_id') != user_db_id:
            return jsonify({
                'success': False,
                'error': 'Você não tem permissão para marcar esta reserva como concluída'
            }), 403
        
        # Verificar se a reserva está confirmada
        if booking.get('status') != 'confirmed':
            return jsonify({
                'success': False,
                'error': 'Apenas reservas confirmadas podem ser marcadas como concluídas'
            }), 400
        
        # Verificar se a data de checkout já passou
        from datetime import datetime
        checkout_date = datetime.strptime(booking['checkout_date'], '%Y-%m-%d')
        today = datetime.now()
        
        if checkout_date.date() > today.date():
            return jsonify({
                'success': False,
                'error': 'A reserva só pode ser marcada como concluída após a data de checkout'
            }), 400
        
        # Atualizar status da reserva para 'completed'
        success = db.update_booking_status(booking_id, 'completed')
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Reserva marcada como concluída com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao marcar reserva como concluída'
            }), 500
            
    except Exception as e:
        print(f"Erro ao marcar reserva como concluída: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anuncios/todos', methods=['GET'])
def get_all_listings():
    """Buscar todos os anúncios públicos"""
    try:
        # Buscar todos os anúncios ativos
        listings = db.get_all_public_listings()
        return jsonify({
            'success': True,
            'listings': listings
        })
    except Exception as e:
        print(f"❌ Erro ao buscar anúncios públicos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anuncios/disponiveis', methods=['GET'])
def get_available_listings():
    """Buscar anúncios disponíveis em uma data específica"""
    try:
        date = request.args.get('date')
        if not date:
            return jsonify({
                'success': False,
                'error': 'Data é obrigatória'
            }), 400
        
        # Buscar anúncios disponíveis na data
        listings = db.get_listings_available_on_date(date)
        return jsonify({
            'success': True,
            'listings': listings,
            'date': date
        })
    except Exception as e:
        print(f"❌ Erro ao buscar anúncios disponíveis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anuncios/periodo', methods=['GET'])
def get_listings_by_period():
    """Buscar anúncios para um período específico com informação de disponibilidade"""
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        print(f"🔍 [FILTRO] Requisição recebida - Início: {data_inicio}, Fim: {data_fim}")
        
        if not data_inicio or not data_fim:
            print("❌ [FILTRO] Datas não fornecidas")
            return jsonify({
                'success': False,
                'message': 'Datas de início e fim são obrigatórias'
            }), 400
        
        # Buscar todos os anúncios
        all_listings = db.get_all_public_listings()
        print(f"📋 [FILTRO] Total de anúncios encontrados: {len(all_listings)}")
        
        # Para cada anúncio, verificar disponibilidade no período
        listings_with_availability = []
        available_count = 0
        
        for listing in all_listings:
            # Verificar se está disponível no período
            is_available = db.check_availability(listing['id'], data_inicio, data_fim)
            
            if is_available:
                available_count += 1
            
            print(f"🏠 [FILTRO] Anúncio {listing['id']} ({listing.get('title', 'Sem título')[:30]}...) - Disponível: {is_available}")
            
            listing_data = dict(listing)
            listing_data['available'] = is_available
            
            # Buscar período de disponibilidade contínua sempre
            available_period = db.get_available_period(listing['id'], data_inicio)
            if available_period:
                listing_data['available_period'] = available_period
            
            # Se não disponível, buscar próxima data disponível
            if not is_available:
                next_available = db.get_next_available_date(listing['id'], data_inicio)
                listing_data['next_available_date'] = next_available
            
            listings_with_availability.append(listing_data)
        
        print(f"✅ [FILTRO] Resultado: {available_count} de {len(all_listings)} anúncios disponíveis no período")
        
        return jsonify({
            'success': True,
            'listings': listings_with_availability
        })
        
    except Exception as e:
        print(f"Erro ao buscar anúncios por período: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/anuncios/<int:listing_id>/disponibilidade', methods=['GET'])
def get_listing_availability(listing_id):
    """Buscar disponibilidade de um anúncio para calendário"""
    try:
        # Obter parâmetros de mês e ano da query string
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        # Se não especificado, usar mês/ano atual
        if not month or not year:
            today = datetime.now().date()
            month = today.month
            year = today.year
        
        print(f"📅 [CALENDARIO] Buscando disponibilidade para anúncio {listing_id} - {month}/{year}")
        
        # Verificar se o anúncio existe
        listing = db.get_public_listing_by_id(listing_id)
        if not listing:
            return jsonify({
                'success': False,
                'message': 'Anúncio não encontrado'
            }), 404
        
        # Validar se o mês/ano não é muito no passado ou futuro
        today = datetime.now().date()
        requested_date = datetime(year, month, 1).date()
        max_future_date = today.replace(year=today.year + 1)  # 12 meses no futuro
        
        if requested_date < today.replace(day=1) or requested_date > max_future_date:
            return jsonify({
                'success': False,
                'message': 'Mês/ano fora do intervalo permitido'
            }), 400
        
        # Calcular primeiro e último dia do mês
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        availability = {}
        current_date = first_day
        
        while current_date <= last_day:
            date_str = current_date.strftime('%Y-%m-%d')
            # Verificar disponibilidade para cada dia
            is_available = db.check_availability(listing_id, date_str, date_str)
            availability[date_str] = is_available
            current_date += timedelta(days=1)
        
        print(f"📅 [CALENDARIO] Disponibilidade calculada para {len(availability)} dias do mês {month}/{year}")
        
        return jsonify({
            'success': True,
            'availability': availability,
            'listing_id': listing_id
        })
        
    except Exception as e:
        print(f"❌ [CALENDARIO] Erro ao buscar disponibilidade: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anuncios/reservar', methods=['POST'])
def create_public_booking():
    """Criar uma reserva pública"""
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        guest_name = data.get('guest_name')
        guest_email = data.get('guest_email')
        guest_phone = data.get('guest_phone')
        
        if not all([listing_id, start_date, end_date, guest_name, guest_email]):
            return jsonify({
                'success': False,
                'error': 'Todos os campos obrigatórios devem ser preenchidos'
            }), 400
        
        # Verificar disponibilidade
        available = db.check_availability(listing_id, start_date, end_date)
        if not available:
            return jsonify({
                'success': False,
                'error': 'Datas não disponíveis para reserva'
            }), 400
        
        # Criar reserva
        booking_id = db.create_public_booking(
            listing_id=listing_id,
            start_date=start_date,
            end_date=end_date,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone
        )
        
        if booking_id:
            return jsonify({
                'success': True,
                'booking_id': booking_id,
                'message': 'Reserva criada com sucesso!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao criar reserva'
            }), 500
        
    except Exception as e:
        print(f"❌ Erro ao criar reserva pública: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anuncios/check-reservation/<int:listing_id>', methods=['GET'])
@login_required
def check_user_reservation(listing_id):
    """Verificar se o usuário já tem uma reserva para este anúncio"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado na sessão'
            }), 400
        
        # Verificar se existe reserva ativa para este usuário e anúncio
        reservation = db.get_user_reservation_for_listing(user_db_id, listing_id)
        
        return jsonify({
            'success': True,
            'has_reservation': reservation is not None,
            'reservation': reservation
        })
        
    except Exception as e:
        print(f"❌ Erro ao verificar reserva: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== ROTAS DE NOTIFICAÇÕES =====

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Buscar notificações do usuário"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        notifications = db.get_user_notifications(user_db_id)
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar notificações: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marcar notificação como lida"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        success = db.mark_notification_as_read(notification_id, user_db_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notificação marcada como lida'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notificação não encontrada ou não pertence ao usuário'
            }), 404
        
    except Exception as e:
        print(f"❌ Erro ao marcar notificação como lida: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marcar todas as notificações como lidas"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        count = db.mark_all_notifications_as_read(user_db_id)
        
        return jsonify({
            'success': True,
            'message': f'{count} notificações marcadas como lidas'
        })
        
    except Exception as e:
        print(f"❌ Erro ao marcar todas as notificações como lidas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_notifications_count():
    """Obter contagem de notificações não lidas"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        count = db.get_unread_notifications_count(user_db_id)
        
        return jsonify({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar contagem de notificações: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/<int:notification_id>/details', methods=['GET'])
@login_required
def get_notification_details(notification_id):
    """Buscar detalhes completos de uma notificação específica"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        # Buscar a notificação
        notification_result = db.supabase.table('notifications').select(
            '*, listing_bookings(*, user_listings(title, address, image_url), users!guest_user_id(name, email))'
        ).eq('id', notification_id).eq('user_id', user_db_id).execute()
        
        if not notification_result.data:
            return jsonify({
                'success': False,
                'error': 'Notificação não encontrada'
            }), 404
        
        notification = notification_result.data[0]
        
        # Preparar dados da resposta
        response_data = {
            'notification': {
                'id': notification['id'],
                'type': notification['type'],
                'title': notification['title'],
                'message': notification['message'],
                'is_read': notification['is_read'],
                'created_at': notification['created_at']
            }
        }
        
        # Adicionar detalhes da reserva se existir
        if notification.get('listing_bookings'):
            booking = notification['listing_bookings']
            listing = booking.get('user_listings', {})
            guest = booking.get('users', {})
            
            response_data['booking'] = {
                'id': booking['id'],
                'checkin_date': booking['checkin_date'],
                'checkout_date': booking['checkout_date'],
                'total_price': booking.get('total_price'),
                'status': booking['status'],
                'payment_status': booking.get('payment_status'),
                'guest_name': guest.get('name') or booking.get('guest_name'),
                'guest_email': guest.get('email') or booking.get('guest_email'),
                'guest_phone': booking.get('guest_phone'),
                'listing': {
                    'title': listing.get('title'),
                    'address': listing.get('address'),
                    'image_url': listing.get('image_url')
                }
            }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar detalhes da notificação: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anuncios/reservar-autenticado', methods=['POST'])
@login_required
def create_authenticated_booking():
    """Criar uma reserva para usuário autenticado"""
    try:
        data = request.get_json()
        listing_id = data.get('listing_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        guests_count = data.get('guests_count', 1)
        
        if not all([listing_id, start_date, end_date]):
            return jsonify({
                'success': False,
                'error': 'Todos os campos obrigatórios devem ser preenchidos'
            }), 400
        
        # Verificar disponibilidade
        available = db.check_availability(listing_id, start_date, end_date)
        if not available:
            return jsonify({
                'success': False,
                'error': 'Datas não disponíveis para reserva'
            }), 400
        
        # Obter informações do usuário logado
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado na sessão'
            }), 400
        
        # Verificar se o usuário não é o dono do anúncio
        listing = db.get_public_listing_by_id(listing_id)
        if not listing:
            return jsonify({
                'success': False,
                'error': 'Anúncio não encontrado'
            }), 404
        
        if listing.get('user_id') == user_db_id:
            return jsonify({
                'success': False,
                'error': 'Você não pode reservar seu próprio anúncio'
            }), 400
        
        # Criar reserva autenticada
        booking_id = db.create_authenticated_booking(
            listing_id=listing_id,
            guest_user_id=user_db_id,
            start_date=start_date,
            end_date=end_date,
            guest_name=current_user.name,
            guest_email=current_user.email,
            guests_count=guests_count
        )
        
        if booking_id:
            return jsonify({
                'success': True,
                'booking_id': booking_id,
                'message': 'Reserva confirmada com sucesso!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao criar reserva'
            }), 500
        
    except Exception as e:
        print(f"❌ Erro ao criar reserva autenticada: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

# ==================== ROTAS DE AVALIAÇÕES ====================

@app.route('/avaliar-hospedagem')
@login_required
def avaliar_hospedagem():
    """Página para avaliar uma hospedagem"""
    return render_template('avaliar_hospedagem.html')

@app.route('/api/reviews', methods=['POST'])
@login_required
def create_review():
    """Criar uma nova avaliação para uma hospedagem"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['booking_id', 'listing_id', 'cleanliness_rating', 
                          'communication_rating', 'checkin_rating', 
                          'accuracy_rating', 'location_rating', 'value_rating']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Verificar se o usuário pode avaliar esta reserva
        can_review = db.can_user_review_booking(current_user.id, data['booking_id'])
        if not can_review:
            return jsonify({'error': 'Você não pode avaliar esta reserva'}), 403
        
        # Verificar se já existe uma avaliação para esta reserva
        existing_review = db.get_booking_review(data['booking_id'])
        if existing_review:
            return jsonify({'error': 'Já existe uma avaliação para esta reserva'}), 409
        
        # Criar a avaliação com os parâmetros corretos
        review_id = db.create_review(
            booking_id=data['booking_id'],
            overall_rating=data.get('overall_rating', 5),
            cleanliness_rating=data.get('cleanliness_rating'),
            communication_rating=data.get('communication_rating'),
            checkin_rating=data.get('checkin_rating'),
            accuracy_rating=data.get('accuracy_rating'),
            location_rating=data.get('location_rating'),
            value_rating=data.get('value_rating'),
            review_title=data.get('review_title', ''),
            review_comment=data.get('review_comment', ''),
            would_recommend=data.get('would_recommend', True)
        )
        
        if review_id:
            return jsonify({
                'message': 'Avaliação criada com sucesso',
                'review_id': review_id
            }), 201
        else:
            return jsonify({'error': 'Erro ao criar avaliação'}), 500
            
    except Exception as e:
        print(f"Erro ao criar avaliação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/reviews', methods=['PUT'])
@login_required
def update_review():
    """Atualizar uma avaliação existente"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if 'booking_id' not in data:
            return jsonify({'error': 'Campo obrigatório: booking_id'}), 400
        
        booking_id = data['booking_id']
        
        # Verificar se o usuário pode editar esta avaliação
        edit_check = db.can_user_edit_review(current_user.id, booking_id)
        if not edit_check['can_edit']:
            return jsonify({'error': edit_check['reason']}), 403
        
        # Preparar dados para atualização
        review_data = {}
        allowed_fields = [
            'overall_rating', 'cleanliness_rating', 'communication_rating',
            'checkin_rating', 'accuracy_rating', 'location_rating', 'value_rating',
            'review_title', 'review_comment', 'would_recommend'
        ]
        
        for field in allowed_fields:
            if field in data:
                review_data[field] = data[field]
        
        # Atualizar a avaliação
        success = db.update_review(booking_id, current_user.id, **review_data)
        
        if success:
            return jsonify({
                'message': 'Avaliação atualizada com sucesso'
            }), 200
        else:
            return jsonify({'error': 'Erro ao atualizar avaliação'}), 500
            
    except Exception as e:
        print(f"Erro ao atualizar avaliação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/reviews/listing/<int:listing_id>', methods=['GET'])
def get_listing_reviews(listing_id):
    """Obter todas as avaliações de uma hospedagem"""
    try:
        reviews = db.get_listing_reviews(listing_id)
        rating_summary = db.get_listing_rating_summary(listing_id)
        
        return jsonify({
            'reviews': reviews,
            'rating_summary': rating_summary
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar avaliações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/reviews/user', methods=['GET'])
@login_required
def get_user_reviews():
    """Obter avaliações do usuário (como hóspede ou anfitrião)"""
    try:
        user_type = request.args.get('type', 'guest')  # 'guest' ou 'host'
        
        if user_type == 'guest':
            reviews = db.get_user_reviews(current_user.id, as_guest=True)
        elif user_type == 'host':
            reviews = db.get_user_reviews(current_user.id, as_host=True)
        else:
            return jsonify({'error': 'Tipo de usuário inválido'}), 400
        
        return jsonify({'reviews': reviews}), 200
        
    except Exception as e:
        print(f"Erro ao buscar avaliações do usuário: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/booking/<int:booking_id>', methods=['GET'])
@login_required
def get_booking_details(booking_id):
    """Obter detalhes de uma reserva específica"""
    try:
        user_db_id = session.get('user_db_id')
        if not user_db_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        # Buscar a reserva específica com dados do anúncio
        booking_result = db.supabase.table('listing_bookings').select(
            '*, user_listings(id, title, address, image_url, municipio_id, municipios(nome))'
        ).eq('id', booking_id).execute()
        
        if not booking_result.data:
            return jsonify({
                'success': False,
                'error': 'Reserva não encontrada'
            }), 404
        
        booking = booking_result.data[0]
        
        # Verificar se o usuário tem permissão para ver esta reserva
        # (deve ser o hóspede ou o anfitrião)
        if (booking.get('guest_user_id') != user_db_id and 
            booking.get('user_listings', {}).get('user_id') != user_db_id):
            return jsonify({
                'success': False,
                'error': 'Você não tem permissão para ver esta reserva'
            }), 403
        
        return jsonify({
            'success': True,
            'booking': booking
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar detalhes da reserva: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reviews/booking/<int:booking_id>', methods=['GET'])
@login_required
def get_booking_review(booking_id):
    """Obter avaliação de uma reserva específica"""
    try:
        review = db.get_booking_review(booking_id)
        
        if review:
            return jsonify({'review': review}), 200
        else:
            return jsonify({'review': None}), 200
        
    except Exception as e:
        print(f"Erro ao buscar avaliação da reserva: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/reviews/can-review/<int:booking_id>', methods=['GET'])
@login_required
def can_review_booking(booking_id):
    """Verificar se o usuário pode avaliar uma reserva"""
    try:
        can_review = db.can_user_review_booking(current_user.id, booking_id)
        
        return jsonify({'can_review': can_review}), 200
        
    except Exception as e:
        print(f"Erro ao verificar permissão de avaliação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/reviews/can-edit/<int:booking_id>', methods=['GET'])
@login_required
def can_edit_review(booking_id):
    """Verificar se o usuário pode editar uma avaliação"""
    try:
        edit_check = db.can_user_edit_review(current_user.id, booking_id)
        
        # Se pode editar, incluir os dados da avaliação existente
        if edit_check.get('can_edit'):
            existing_review = db.get_booking_review(booking_id)
            if existing_review:
                edit_check['review'] = {
                    'overall_rating': existing_review.get('overall_rating'),
                    'cleanliness_rating': existing_review.get('cleanliness_rating'),
                    'communication_rating': existing_review.get('communication_rating'),
                    'checkin_rating': existing_review.get('checkin_rating'),
                    'accuracy_rating': existing_review.get('accuracy_rating'),
                    'location_rating': existing_review.get('location_rating'),
                    'value_rating': existing_review.get('value_rating'),
                    'title': existing_review.get('review_title'),
                    'comment': existing_review.get('review_comment'),
                    'would_recommend': existing_review.get('would_recommend', False),
                    'is_public': existing_review.get('is_public', False)
                }
        
        return jsonify(edit_check), 200
        
    except Exception as e:
        print(f"Erro ao verificar permissão de edição: {e}")
        return jsonify({'can_edit': False, 'reason': 'Erro interno do servidor'}), 500


# ===== ROTAS DE API PARA SISTEMA DE PREÇO DINÂMICO =====

@app.route('/api/dynamic-pricing/apply', methods=['POST'])
@login_required
def apply_dynamic_pricing():
    """Aplicar preço dinâmico a um anúncio"""
    try:
        from dynamic_pricing_system import DynamicPricingSystem
        
        data = request.get_json()
        listing_id = data.get('listing_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not all([listing_id, start_date, end_date]):
            return jsonify({'error': 'listing_id, start_date e end_date são obrigatórios'}), 400
        
        # Verificar se o anúncio pertence ao usuário
        listing = db.get_listing_by_id(listing_id)
        if not listing or listing.get('user_id') != current_user.id:
            return jsonify({'error': 'Anúncio não encontrado ou sem permissão'}), 404
        
        # Aplicar preço dinâmico
        pricing_system = DynamicPricingSystem()
        result = pricing_system.apply_dynamic_pricing_to_listing(
            listing_id, start_date, end_date
        )
        
        return jsonify({
            'success': True,
            'message': 'Preço dinâmico aplicado com sucesso',
            'result': result
        }), 200
        
    except Exception as e:
        print(f"Erro ao aplicar preço dinâmico: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/dynamic-pricing/history/<int:listing_id>', methods=['GET'])
@login_required
def get_dynamic_pricing_history(listing_id):
    """Obter histórico de preços dinâmicos de um anúncio"""
    try:
        # Verificar se o anúncio pertence ao usuário
        listing = db.get_listing_by_id(listing_id)
        if not listing or listing.get('user_id') != current_user.id:
            return jsonify({'error': 'Anúncio não encontrado ou sem permissão'}), 404
        
        # Obter histórico
        history = db.get_dynamic_pricing_history(listing_id)
        
        return jsonify({
            'success': True,
            'history': history
        }), 200
        
    except Exception as e:
        print(f"Erro ao obter histórico de preços: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/dynamic-pricing/demand/<int:municipio_id>', methods=['GET'])
@login_required
def get_regional_demand(municipio_id):
    """Obter dados de demanda regional"""
    try:
        from dynamic_pricing_system import DynamicPricingSystem
        
        pricing_system = DynamicPricingSystem()
        demand_data = pricing_system.get_regional_demand_data(municipio_id)
        
        return jsonify({
            'success': True,
            'demand_data': demand_data
        }), 200
        
    except Exception as e:
        print(f"Erro ao obter dados de demanda: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/dynamic-pricing/calculate', methods=['POST'])
@login_required
def calculate_dynamic_price():
    """Calcular preço dinâmico para uma data específica"""
    try:
        from dynamic_pricing_system import DynamicPricingSystem
        
        data = request.get_json()
        listing_id = data.get('listing_id')
        date = data.get('date')
        
        if not all([listing_id, date]):
            return jsonify({'error': 'listing_id e date são obrigatórios'}), 400
        
        # Verificar se o anúncio pertence ao usuário
        listing = db.get_listing_by_id(listing_id)
        if not listing or listing.get('user_id') != current_user.id:
            return jsonify({'error': 'Anúncio não encontrado ou sem permissão'}), 404
        
        # Calcular preço dinâmico
        pricing_system = DynamicPricingSystem()
        price_data = pricing_system.calculate_dynamic_price(listing_id, date)
        
        return jsonify({
            'success': True,
            'price_data': price_data
        }), 200
        
    except Exception as e:
        print(f"Erro ao calcular preço dinâmico: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/dynamic-pricing')
@login_required
def dynamic_pricing_page():
    """Página de gerenciamento de preços dinâmicos"""
    return render_template('dynamic_pricing.html')

if __name__ == '__main__':
    print("🌐 Iniciando aplicação web...")
    print("📊 Acesse: http://localhost:5000")
    print("⚠️ Para parar, pressione Ctrl+C")
    
    app.run(debug=True, host='0.0.0.0', port=5000)