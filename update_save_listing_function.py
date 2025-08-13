# =====================================================
# ATUALIZAÇÃO DA FUNÇÃO save_user_listing
# Este arquivo contém a versão atualizada da função para usar as novas colunas
# =====================================================

def save_user_listing(self, user_id: int, title: str, url: str, municipio_id: int = None,
                     platform: str = 'airbnb', property_type: str = None, 
                     max_guests: int = None, bedrooms: int = None, bathrooms: int = None,
                     # Novas colunas de preço e avaliação
                     price_per_night: float = None, rating: float = None, reviews: int = None,
                     # Novas colunas de localização
                     address: str = None, latitude: float = None, longitude: float = None,
                     # Novas colunas de descrição
                     description: str = None, amenities: list = None, image_url: str = None,
                     # Características específicas
                     is_beachfront: bool = False, beach_confidence: float = 0,
                     instant_book: bool = False, superhost: bool = False,
                     # Preços detalhados
                     cleaning_fee: float = None, service_fee: float = None, total_price: float = None,
                     # Disponibilidade
                     minimum_nights: int = 1, maximum_nights: int = None, availability_365: int = None,
                     # Informações do host
                     host_name: str = None, host_id: str = None, 
                     host_response_rate: int = None, host_response_time: str = None,
                     # Metadados
                     extraction_method: str = None, data_quality_score: float = None) -> int:
    """
    Salva um link de anúncio do usuário com todas as informações extraídas
    """
    try:
        from datetime import datetime
        
        listing_data = {
            # Campos originais
            'user_id': user_id,
            'title': title,
            'url': url,
            'platform': platform,
            'municipio_id': municipio_id,
            'property_type': property_type,
            'max_guests': max_guests,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            
            # Novos campos de preço e avaliação
            'price_per_night': price_per_night,
            'rating': rating,
            'reviews': reviews,
            
            # Novos campos de localização
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            
            # Novos campos de descrição
            'description': description,
            'amenities': amenities,  # Será convertido para JSON
            'image_url': image_url,
            
            # Características específicas
            'is_beachfront': is_beachfront,
            'beach_confidence': beach_confidence,
            'instant_book': instant_book,
            'superhost': superhost,
            
            # Preços detalhados
            'cleaning_fee': cleaning_fee,
            'service_fee': service_fee,
            'total_price': total_price,
            
            # Disponibilidade
            'minimum_nights': minimum_nights,
            'maximum_nights': maximum_nights,
            'availability_365': availability_365,
            
            # Informações do host
            'host_name': host_name,
            'host_id': host_id,
            'host_response_rate': host_response_rate,
            'host_response_time': host_response_time,
            
            # Metadados
            'last_scraped': datetime.now().isoformat(),
            'extraction_method': extraction_method,
            'data_quality_score': data_quality_score
        }
        
        # Remover campos None para não sobrescrever valores padrão
        listing_data = {k: v for k, v in listing_data.items() if v is not None}
        
        print(f"🔍 Dados que serão inseridos na tabela user_listings: {listing_data}")
        
        result = self.supabase.table('user_listings').insert(listing_data).execute()
        
        print(f"📊 Resultado da inserção: {result.data}")
        
        return result.data[0]['id']
    except Exception as e:
        print(f"❌ Erro ao salvar link de anúncio: {e}")
        print(f"🔍 Dados que causaram o erro: user_id={user_id}, title={title}, url={url}")
        raise

# =====================================================
# FUNÇÃO AUXILIAR PARA EXTRAIR DADOS COMPLETOS
# =====================================================

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
            
            # Host
            'host_name': scraper_data.get('host_name'),
            'host_id': scraper_data.get('host_id'),
            'host_response_rate': scraper_data.get('host_response_rate'),
            'host_response_time': scraper_data.get('host_response_time'),
            
            # Metadados
            'extraction_method': scraper_data.get('extraction_method', 'manual'),
            'data_quality_score': scraper_data.get('data_quality_score')
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

# =====================================================
# EXEMPLO DE USO NO WEB_APP.PY
# =====================================================

"""
# No arquivo web_app.py, na função extract_listing_info:

@app.route('/perfil/extract_listing_info', methods=['POST'])
@login_required
def extract_listing_info():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        user_db_id = session.get('user_db_id')
        
        if not url or not user_db_id:
            return jsonify({'success': False, 'error': 'URL e usuário são obrigatórios'})
        
        # Usar o scraper para extrair informações completas
        scraper = AirbnbClimateScraper()
        
        # Simular datas para análise
        today = datetime.now()
        checkin = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        checkout = (today + timedelta(days=9)).strftime('%Y-%m-%d')
        
        # Extrair informações completas
        listing_info = scraper.analyze_specific_listing(url, checkin, checkout)
        
        if not listing_info:
            return jsonify({'success': False, 'error': 'Não foi possível extrair informações'})
        
        # Salvar com dados completos
        listing_id = db.extract_and_save_listing(user_db_id, url, listing_info[0])
        
        return jsonify({
            'success': True, 
            'listing_id': listing_id,
            'data': listing_info[0]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
"""

# =====================================================
# QUERIES ÚTEIS PARA AS NOVAS COLUNAS
# =====================================================

QUERIES_EXAMPLES = """
-- 1. Anúncios com melhor custo-benefício
SELECT title, price_per_night, rating, reviews, 
       (rating * reviews / NULLIF(price_per_night, 0)) as value_score
FROM user_listings 
WHERE price_per_night > 0 AND rating > 0 AND reviews > 5
ORDER BY value_score DESC;

-- 2. Análise de mercado por região
SELECT m.nome, 
       COUNT(*) as total_listings,
       AVG(ul.price_per_night) as avg_price,
       AVG(ul.rating) as avg_rating,
       COUNT(CASE WHEN ul.is_beachfront THEN 1 END) as beachfront_count
FROM user_listings ul
JOIN municipios m ON ul.municipio_id = m.id
WHERE ul.is_active = TRUE
GROUP BY m.id, m.nome
ORDER BY avg_price DESC;

-- 3. Anúncios que precisam de atualização
SELECT title, url, last_scraped,
       EXTRACT(days FROM NOW() - last_scraped) as days_since_update
FROM user_listings
WHERE last_scraped < NOW() - INTERVAL '7 days'
   OR last_scraped IS NULL
ORDER BY last_scraped NULLS FIRST;

-- 4. Top anúncios por características
SELECT title, price_per_night, rating, reviews,
       CASE WHEN is_beachfront THEN '🏖️' ELSE '' END as beachfront,
       CASE WHEN superhost THEN '⭐' ELSE '' END as superhost,
       CASE WHEN instant_book THEN '⚡' ELSE '' END as instant
FROM user_listings
WHERE is_active = TRUE AND rating >= 4.5
ORDER BY rating DESC, reviews DESC;
"""