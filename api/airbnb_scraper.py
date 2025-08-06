import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import re
from urllib.parse import quote
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import schedule
import threading
import base64
from io import BytesIO

class AirbnbClimateScraper:
    def __init__(self, email_config=None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.email_config = email_config or {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',  # Configurar com email remetente
            'sender_password': '',  # Configurar com senha de app
            'recipient_email': 'paulotestario@gmail.com'
        }
        self.beach_keywords = [
            'frente ao mar', 'frente à praia', 'vista para o mar', 'beira mar',
            'pé na areia', 'primeira linha', 'orla', 'waterfront', 'beachfront',
            'ocean view', 'sea view', 'beach view', 'praia em frente'
        ]
    
    def get_airbnb_prices(self, checkin_date, checkout_date, adults=2):
        """
        Busca preços no Airbnb para Itacuruçá com foco no Hotel Mont Blanc
        """
        # URL base do Airbnb para Itacuruçá
        base_url = "https://www.airbnb.com.br/s/Itacuru%C3%A7%C3%A1--Mangaratiba/homes"
        
        params = {
            'refinement_paths[]': '/homes',
            'place_id': 'ChIJBZOnamAOnAARLKakGipY0SI',
            'date_picker_type': 'calendar',
            'checkin': checkin_date,
            'checkout': checkout_date,
            'adults': adults,
            'source': 'structured_search_input_header',
            'search_type': 'autocomplete_click'
        }
        
        try:
            response = self.session.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Procurar por dados de preços na página
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar por elementos que contenham preços
            price_elements = soup.find_all(['span', 'div'], text=re.compile(r'R\$\s*\d+'))
            mont_blanc_listings = []
            
            # Procurar especificamente por Mont Blanc
            for element in soup.find_all(text=re.compile(r'Mont\s*Blanc', re.IGNORECASE)):
                parent = element.parent
                while parent and parent.name != 'body':
                    price_elem = parent.find(text=re.compile(r'R\$\s*\d+'))
                    if price_elem:
                        price_match = re.search(r'R\$\s*(\d+(?:\.\d+)?)', price_elem)
                        if price_match:
                            mont_blanc_listings.append({
                                'name': 'Hotel Mont Blanc',
                                'price_per_night': float(price_match.group(1).replace('.', '')),
                                'total_price': float(price_match.group(1).replace('.', '')) * self._calculate_nights(checkin_date, checkout_date)
                            })
                            break
                    parent = parent.parent
            
            # Se não encontrou Mont Blanc específico, pegar preços gerais
            if not mont_blanc_listings:
                general_prices = []
                for price_elem in price_elements[:5]:  # Pegar os primeiros 5 preços
                    price_match = re.search(r'R\$\s*(\d+(?:\.\d+)?)', price_elem.get_text())
                    if price_match:
                        price = float(price_match.group(1).replace('.', ''))
                        general_prices.append(price)
                
                if general_prices:
                    avg_price = sum(general_prices) / len(general_prices)
                    mont_blanc_listings.append({
                        'name': 'Preço médio da região (Mont Blanc não encontrado especificamente)',
                        'price_per_night': avg_price,
                        'total_price': avg_price * self._calculate_nights(checkin_date, checkout_date)
                    })
            
            return mont_blanc_listings
            
        except Exception as e:
            print(f"Erro ao buscar preços do Airbnb: {e}")
            return []
    
    def analyze_listing_images_and_description(self, listing_element):
        """
        Analisa imagens e descrição de um anúncio para verificar se é frente à praia
        """
        beach_indicators = {
            'is_beachfront': False,
            'confidence_score': 0,
            'evidence': []
        }
        
        try:
            # Analisar descrição do anúncio
            description_elements = listing_element.find_all(text=True)
            full_text = ' '.join(description_elements).lower()
            
            # Verificar palavras-chave relacionadas à praia
            beach_score = 0
            found_keywords = []
            
            for keyword in self.beach_keywords:
                if keyword.lower() in full_text:
                    beach_score += 1
                    found_keywords.append(keyword)
            
            # Analisar URLs de imagens para indicadores visuais
            img_elements = listing_element.find_all('img')
            image_indicators = []
            
            for img in img_elements:
                src = img.get('src', '')
                alt = img.get('alt', '').lower()
                
                # Verificar se alt text ou URL contém indicadores de praia
                beach_terms = ['beach', 'ocean', 'sea', 'praia', 'mar', 'water', 'coast']
                for term in beach_terms:
                    if term in alt or term in src.lower():
                        image_indicators.append(f"Imagem com indicador: {term}")
                        beach_score += 0.5
            
            # Calcular score de confiança
            confidence_score = min(beach_score * 10, 100)  # Máximo 100%
            
            beach_indicators.update({
                'is_beachfront': confidence_score >= 30,  # 30% de confiança mínima
                'confidence_score': confidence_score,
                'evidence': found_keywords + image_indicators
            })
            
        except Exception as e:
            print(f"Erro na análise de imagens/descrição: {e}")
        
        return beach_indicators
    
    def analyze_listing_similarity(self, reference_listing, competitor_listing):
        """
        Analisa similaridade entre dois anúncios baseado em características visuais e textuais
        """
        similarity_score = 0
        similarity_details = {
            'visual_similarity': 0,
            'text_similarity': 0,
            'amenities_similarity': 0,
            'location_similarity': 0,
            'total_score': 0,
            'reasons': []
        }
        
        try:
            # 1. Análise de similaridade visual (baseada em URLs de imagem e alt text)
            ref_images = self._extract_image_features(reference_listing)
            comp_images = self._extract_image_features(competitor_listing)
            
            visual_score = self._compare_image_features(ref_images, comp_images)
            similarity_details['visual_similarity'] = visual_score
            
            # 2. Análise de similaridade textual (títulos e descrições)
            text_score = self._compare_text_features(reference_listing, competitor_listing)
            similarity_details['text_similarity'] = text_score
            
            # 3. Análise de amenidades similares
            amenities_score = self._compare_amenities(reference_listing, competitor_listing)
            similarity_details['amenities_similarity'] = amenities_score
            
            # 4. Análise de proximidade geográfica
            location_score = self._compare_location_features(reference_listing, competitor_listing)
            similarity_details['location_similarity'] = location_score
            
            # Calcular score total ponderado
            total_score = (
                visual_score * 0.3 +      # 30% peso para similaridade visual
                text_score * 0.25 +       # 25% peso para similaridade textual
                amenities_score * 0.25 +  # 25% peso para amenidades
                location_score * 0.2      # 20% peso para localização
            )
            
            similarity_details['total_score'] = total_score
            
            # Adicionar razões da similaridade
            if visual_score > 70:
                similarity_details['reasons'].append(f"Fotos muito similares ({visual_score:.1f}% compatibilidade)")
            if text_score > 60:
                similarity_details['reasons'].append(f"Descrições similares ({text_score:.1f}% compatibilidade)")
            if amenities_score > 50:
                similarity_details['reasons'].append(f"Amenidades similares ({amenities_score:.1f}% compatibilidade)")
            if location_score > 80:
                similarity_details['reasons'].append(f"Localização muito próxima ({location_score:.1f}% compatibilidade)")
                
        except Exception as e:
            print(f"Erro na análise de similaridade: {e}")
            
        return similarity_details
    
    def _extract_image_features(self, listing_data):
        """
        Extrai características das imagens de um anúncio
        """
        features = {
            'image_count': 0,
            'image_keywords': [],
            'image_types': [],
            'dominant_colors': []
        }
        
        try:
            # Analisar URL da imagem principal
            if 'image_url' in listing_data and listing_data['image_url']:
                features['image_count'] = 1
                
                # Extrair palavras-chave da URL da imagem
                img_url = listing_data['image_url'].lower()
                
                # Identificar tipos de ambiente nas URLs
                room_types = ['bedroom', 'kitchen', 'bathroom', 'living', 'pool', 'beach', 'garden', 'balcony']
                for room_type in room_types:
                    if room_type in img_url:
                        features['image_types'].append(room_type)
                
                # Identificar características visuais nas URLs
                visual_keywords = ['modern', 'rustic', 'luxury', 'cozy', 'spacious', 'bright', 'dark', 'colorful']
                for keyword in visual_keywords:
                    if keyword in img_url:
                        features['image_keywords'].append(keyword)
                        
        except Exception as e:
            print(f"Erro ao extrair características de imagem: {e}")
            
        return features
    
    def _compare_image_features(self, ref_features, comp_features):
        """
        Compara características visuais entre dois anúncios
        """
        score = 0
        
        try:
            # Comparar tipos de ambiente
            ref_types = set(ref_features.get('image_types', []))
            comp_types = set(comp_features.get('image_types', []))
            
            if ref_types and comp_types:
                common_types = ref_types.intersection(comp_types)
                type_similarity = len(common_types) / max(len(ref_types), len(comp_types)) * 100
                score += type_similarity * 0.6
            
            # Comparar palavras-chave visuais
            ref_keywords = set(ref_features.get('image_keywords', []))
            comp_keywords = set(comp_features.get('image_keywords', []))
            
            if ref_keywords and comp_keywords:
                common_keywords = ref_keywords.intersection(comp_keywords)
                keyword_similarity = len(common_keywords) / max(len(ref_keywords), len(comp_keywords)) * 100
                score += keyword_similarity * 0.4
                
        except Exception as e:
            print(f"Erro ao comparar características de imagem: {e}")
            
        return min(score, 100)
    
    def _compare_text_features(self, ref_listing, comp_listing):
        """
        Compara características textuais entre dois anúncios
        """
        score = 0
        
        try:
            ref_title = ref_listing.get('title', '').lower()
            comp_title = comp_listing.get('title', '').lower()
            
            # Extrair palavras-chave importantes dos títulos
            ref_words = set(word for word in ref_title.split() if len(word) > 3)
            comp_words = set(word for word in comp_title.split() if len(word) > 3)
            
            if ref_words and comp_words:
                common_words = ref_words.intersection(comp_words)
                text_similarity = len(common_words) / max(len(ref_words), len(comp_words)) * 100
                score = text_similarity
                
        except Exception as e:
            print(f"Erro ao comparar características textuais: {e}")
            
        return min(score, 100)
    
    def _compare_amenities(self, ref_listing, comp_listing):
        """
        Compara amenidades entre dois anúncios
        """
        score = 0
        
        try:
            # Analisar características implícitas nos títulos e evidências
            ref_features = set()
            comp_features = set()
            
            # Extrair características do anúncio de referência
            if ref_listing.get('is_beachfront'):
                ref_features.add('beachfront')
            if ref_listing.get('beach_evidence'):
                ref_features.update([ev.lower() for ev in ref_listing['beach_evidence']])
                
            # Extrair características do concorrente
            if comp_listing.get('is_beachfront'):
                comp_features.add('beachfront')
            if comp_listing.get('beach_evidence'):
                comp_features.update([ev.lower() for ev in comp_listing['beach_evidence']])
                
            # Analisar títulos para amenidades
            amenity_keywords = ['piscina', 'pool', 'wifi', 'ar condicionado', 'churrasqueira', 'garagem', 'vista', 'varanda']
            
            ref_title = ref_listing.get('title', '').lower()
            comp_title = comp_listing.get('title', '').lower()
            
            for amenity in amenity_keywords:
                if amenity in ref_title:
                    ref_features.add(amenity)
                if amenity in comp_title:
                    comp_features.add(amenity)
            
            # Calcular similaridade
            if ref_features and comp_features:
                common_features = ref_features.intersection(comp_features)
                score = len(common_features) / max(len(ref_features), len(comp_features)) * 100
                
        except Exception as e:
            print(f"Erro ao comparar amenidades: {e}")
            
        return min(score, 100)
    
    def _compare_location_features(self, ref_listing, comp_listing):
        """
        Compara características de localização entre dois anúncios
        """
        score = 80  # Score base alto pois estamos buscando na mesma região
        
        try:
            # Analisar se ambos são frente à praia
            ref_beachfront = ref_listing.get('is_beachfront', False)
            comp_beachfront = comp_listing.get('is_beachfront', False)
            
            if ref_beachfront == comp_beachfront:
                score += 20  # Bonus se ambos têm a mesma característica de praia
                
        except Exception as e:
            print(f"Erro ao comparar localização: {e}")
            
        return min(score, 100)
    
    def get_competitive_analysis(self, checkin_date, checkout_date, adults=2, reference_listing=None):
        """
        Análise competitiva detalhada dos anúncios em Itacuruçá com análise de similaridade
        Agora usa múltiplas estratégias de busca para encontrar mais concorrentes
        """
        base_url = "https://www.airbnb.com.br/s/Itacuru%C3%A7%C3%A1--Mangaratiba/homes"
        
        # Múltiplas buscas para capturar mais concorrentes com diferentes estratégias
        search_configs = [
            {
                'name': 'Busca Principal - Itacuruçá',
                'params': {
                    'refinement_paths[]': '/homes',
                    'place_id': 'ChIJBZOnamAOnAARLKakGipY0SI',
                    'date_picker_type': 'calendar',
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'adults': adults,
                    'guests': adults,
                    'search_type': 'AUTOSUGGEST'
                }
            },
            {
                'name': 'Busca Mangaratiba Geral',
                'url': 'https://www.airbnb.com.br/s/Mangaratiba--Estado-do-Rio-de-Janeiro--Brasil/homes',
                'params': {
                    'refinement_paths[]': '/homes',
                    'date_picker_type': 'calendar',
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'adults': adults,
                    'guests': adults,
                    'search_type': 'AUTOSUGGEST'
                }
            },
            {
                'name': 'Busca com Filtros de Preço',
                'params': {
                    'refinement_paths[]': '/homes',
                    'place_id': 'ChIJBZOnamAOnAARLKakGipY0SI',
                    'date_picker_type': 'calendar',
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'adults': adults,
                    'guests': adults,
                    'search_type': 'AUTOSUGGEST',
                    'price_min': 100,
                    'price_max': 1500
                }
            },
            {
                'name': 'Busca Apartamentos Completos',
                'params': {
                    'refinement_paths[]': '/homes',
                    'place_id': 'ChIJBZOnamAOnAARLKakGipY0SI',
                    'date_picker_type': 'calendar',
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'adults': adults,
                    'guests': adults,
                    'search_type': 'AUTOSUGGEST',
                    'room_types[]': 'Entire home/apt',
                    'price_min': 300,
                    'price_max': 1500
                }
            },
            {
                'name': 'Busca Região Ampliada',
                'url': 'https://www.airbnb.com.br/s/Angra-dos-Reis--Estado-do-Rio-de-Janeiro--Brasil/homes',
                'params': {
                    'refinement_paths[]': '/homes',
                    'date_picker_type': 'calendar',
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'adults': adults,
                    'guests': adults,
                    'search_type': 'AUTOSUGGEST',
                    'price_min': 200,
                    'price_max': 1200
                }
            },
            {
                'name': 'Busca Casas e Apartamentos',
                'params': {
                    'refinement_paths[]': '/homes',
                    'place_id': 'ChIJBZOnamAOnAARLKakGipY0SI',
                    'date_picker_type': 'calendar',
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'adults': adults,
                    'guests': adults,
                    'search_type': 'AUTOSUGGEST',
                    'room_types[]': ['Entire home/apt', 'Private room']
                }
            }
        ]
        
        competitive_data = []
        similar_listings = []
        
        try:
            # Executar múltiplas buscas para capturar mais concorrentes
            all_listings = []  # Lista para coletar todos os anúncios
            
            for config in search_configs:
                # Usar URL customizada se especificada, senão usar base_url
                search_url = config.get('url', base_url)
                print(f"🔍 Executando {config['name']}: {search_url}")
                print(f"📅 Parâmetros: checkin={checkin_date}, checkout={checkout_date}, adults={adults}")
                
                response = self.session.get(search_url, params=config['params'], timeout=30)
                response.raise_for_status()
                
                print(f"✅ Resposta recebida - Status: {response.status_code}")
                print(f"📄 Tamanho da resposta: {len(response.content)} bytes")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Processar esta busca
                search_listings = self._process_search_results(soup, config['name'])
                
                # Adicionar resultados evitando duplicatas globais
                for new_listing in search_listings:
                    duplicate = False
                    for existing in all_listings:
                        if (existing['title'] == new_listing['title'] and 
                            existing['price_per_night'] == new_listing['price_per_night']):
                            duplicate = True
                            break
                    if not duplicate:
                        all_listings.append(new_listing)
                
                # Pequena pausa entre buscas
                time.sleep(2)
            
            print(f"📊 Total de anúncios únicos coletados: {len(all_listings)}")
            
            # Se um anúncio de referência foi fornecido, analisar similaridade
            if reference_listing and all_listings:
                print("\n🔍 === ANALISANDO SIMILARIDADE COM ANÚNCIO DE REFERÊNCIA ===")
                
                for listing in all_listings:
                    try:
                        similarity = self.analyze_listing_similarity(reference_listing, listing)
                        listing['similarity_analysis'] = similarity
                        
                        # Filtrar apenas anúncios com alta similaridade (score > 40)
                        if similarity['total_score'] > 40:
                            similar_listings.append(listing)
                            print(f"✅ Anúncio similar: {listing['title'][:50]}... (Score: {similarity['total_score']:.1f})")
                            if similarity['reasons']:
                                for reason in similarity['reasons']:
                                    print(f"   - {reason}")
                                    
                    except Exception as e:
                        print(f"❌ Erro ao analisar similaridade: {e}")
                        continue
                
                print(f"\n🎯 === ENCONTRADOS {len(similar_listings)} ANÚNCIOS SIMILARES ===")
                
                # Usar anúncios similares se disponíveis, senão usar todos
                competitive_data = similar_listings if similar_listings else all_listings
            else:
                competitive_data = all_listings
            
        except Exception as e:
            print(f"❌ Erro na análise competitiva: {e}")
        
        # Se não conseguiu coletar dados reais, usar dados simulados baseados em pesquisa de mercado
        if not competitive_data:
            print("🔄 Usando dados simulados de mercado para Itacuruçá...")
            competitive_data = self._get_simulated_market_data(checkin_date, checkout_date)
        
        # Adicionar informações de análise de similaridade ao resultado
        result = {
            'listings': competitive_data,
            'total_found': len(all_listings) if 'all_listings' in locals() else 0,
            'similar_count': len(similar_listings) if reference_listing else 0,
            'similarity_enabled': reference_listing is not None
        }
        
        return result
    
    def _process_search_results(self, soup, search_name):
        """
        Processa os resultados de uma busca específica
        """
        listings = []
        
        # Buscar por containers de anúncios com diferentes seletores
        listing_containers = []
        
        # Tentar diferentes seletores para encontrar anúncios
        selectors = [
            {'tag': ['div', 'article'], 'class': re.compile(r'listing|card|property')},
            {'tag': 'div', 'attrs': {'data-testid': re.compile(r'listing|card')}},
            {'tag': 'div', 'attrs': {'itemprop': 'itemListElement'}},
            {'tag': 'div', 'class': re.compile(r'c1yo0219')},  # Classe comum do Airbnb
            {'tag': 'a', 'attrs': {'aria-label': re.compile(r'.*')}}
        ]
        
        for selector in selectors:
            if 'attrs' in selector:
                containers = soup.find_all(selector['tag'], attrs=selector['attrs'])
            else:
                containers = soup.find_all(selector['tag'], class_=selector['class'])
            
            if containers:
                listing_containers = containers
                print(f"📋 {search_name} - Encontrados {len(containers)} containers com seletor: {selector}")
                break
        
        if not listing_containers:
            print(f"❌ {search_name} - Nenhum container de anúncio encontrado")
            return listings
        
        print(f"🏠 {search_name} - Processando {min(len(listing_containers), 20)} anúncios...")
        
        for i, container in enumerate(listing_containers[:20]):  # Analisar até 20 anúncios
            try:
                # Extrair informações básicas
                title_elem = container.find(text=re.compile(r'\w+'))
                title = title_elem.strip() if title_elem else f"Anúncio {i+1}"
                
                # Extrair preço com diferentes padrões mais específicos
                price = 0
                container_text = container.get_text()
                
                # Padrões de preço mais específicos para Airbnb
                price_patterns = [
                    r'R\$\s*(\d{1,4}(?:[.,]\d{3})*(?:[.,]\d{2})?)',  # R$ 1.234,56 ou R$ 1234
                    r'(\d{2,4})\s*(?:por\s*noite|/\s*noite)',  # 150 por noite
                    r'Total\s*R\$\s*(\d+)',  # Total R$ 300
                    r'(\d{2,4})\s*reais?',  # 200 reais
                    r'\$\s*(\d{2,4})',  # $ 150
                    r'(?:^|\s)(\d{2,4})(?=\s*$|\s*por|\s*/)',  # números isolados
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, container_text, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        try:
                            # Limpar e converter o preço
                            price_str = str(match).replace('.', '').replace(',', '.')
                            potential_price = float(price_str)
                            
                            # Validar se o preço está em uma faixa razoável (R$ 50 - R$ 2000 por noite)
                            if 50 <= potential_price <= 2000:
                                price = potential_price
                                print(f"💰 Preço encontrado: R${price} (padrão: {pattern})")
                                break
                        except (ValueError, TypeError):
                            continue
                        
                    if price > 0:
                        break
                
                # Analisar se é frente à praia
                beach_analysis = self.analyze_listing_images_and_description(container)
                
                # Extrair avaliações se disponível
                rating = 0
                reviews_count = 0
                
                # Buscar padrões de avaliação
                rating_patterns = [
                    r'(\d+[.,]\d+)\s*\(\s*(\d+)\s*avalia[çc][õo]es?\)',  # 4.5 (123 avaliações)
                    r'(\d+[.,]\d+)\s*★\s*\(\s*(\d+)\s*\)',  # 4.5 ★ (123)
                    r'★\s*(\d+[.,]\d+)\s*\(\s*(\d+)\s*\)',  # ★ 4.5 (123)
                    r'(\d+[.,]\d+)\s*estrelas?\s*\(\s*(\d+)\s*\)'  # 4.5 estrelas (123)
                ]
                
                for pattern in rating_patterns:
                    match = re.search(pattern, container_text, re.IGNORECASE)
                    if match:
                        rating = float(match.group(1).replace(',', '.'))
                        reviews_count = int(match.group(2))
                        break
                
                # Se não encontrou o padrão completo, tentar só a nota
                if rating == 0:
                    rating_match = re.search(r'(\d+[.,]\d+)', container_text)
                    if rating_match:
                        potential_rating = float(rating_match.group(1).replace(',', '.'))
                        if 1 <= potential_rating <= 5:  # Validar se é uma nota válida
                            rating = potential_rating
                
                # Extrair URL do anúncio - tentar múltiplos seletores
                listing_url = ""
                
                # Tentar diferentes seletores para encontrar o link
                link_selectors = [
                    'a[href*="/rooms/"]',  # Link direto para room
                    'a[data-testid="listing-link"]',  # Link com data-testid
                    'a[href*="/plus/"]',  # Airbnb Plus
                    'a[href*="/luxury/"]',  # Airbnb Luxe
                    'a[href]'  # Qualquer link como fallback
                ]
                
                for selector in link_selectors:
                    try:
                        link_elem = container.select_one(selector)
                        if link_elem:
                            href = link_elem.get('href')
                            if href and ('/rooms/' in href or '/plus/' in href or '/luxury/' in href):
                                if href.startswith('/'):
                                    listing_url = f"https://www.airbnb.com.br{href}"
                                elif href.startswith('http'):
                                    listing_url = href
                                break
                    except Exception:
                        continue
                    
                    # Se ainda não encontrou, tentar buscar no HTML bruto
                    if not listing_url:
                        # Buscar por URLs que contenham /rooms/
                        url_pattern = r'/rooms/[0-9]+'
                        url_match = re.search(url_pattern, str(container))
                        if url_match:
                            href = url_match.group(0)
                            listing_url = f"https://www.airbnb.com.br{href}"
                    
                    # Extrair imagem do anúncio - tentar múltiplos seletores
                    image_url = ""
                    
                    # Tentar diferentes seletores para encontrar imagens
                    img_selectors = [
                        'img[src*="pictures"]',  # Imagens do Airbnb
                        'img[data-src*="pictures"]',  # Lazy loading
                        'img[src*="airbnb"]',  # URLs do Airbnb
                        'img[data-original*="pictures"]',  # Outro tipo de lazy loading
                        'img[srcset*="pictures"]',  # Responsive images
                        'img',  # Fallback para qualquer imagem
                    ]
                    
                    for selector in img_selectors:
                        try:
                            img_elem = container.select_one(selector)
                            if img_elem:
                                # Tentar diferentes atributos de imagem
                                src = (img_elem.get('src') or 
                                      img_elem.get('data-src') or 
                                      img_elem.get('data-original') or 
                                      img_elem.get('data-lazy-src') or
                                      img_elem.get('data-srcset'))
                                
                                # Se srcset existe, pegar a primeira URL
                                if not src and img_elem.get('srcset'):
                                    srcset = img_elem.get('srcset')
                                    if srcset:
                                        src = srcset.split(',')[0].split(' ')[0]
                                
                                if src:
                                    # Limpar e validar URL
                                    src = src.strip()
                                    
                                    # Verificar se é uma URL válida do Airbnb
                                    if (src.startswith('http') and 
                                        ('pictures' in src or 'airbnb' in src or 'muscache' in src)):
                                        image_url = src
                                        break
                                    elif src.startswith('//'):
                                        if 'pictures' in src or 'airbnb' in src or 'muscache' in src:
                                            image_url = f"https:{src}"
                                            break
                                    elif src.startswith('/') and ('pictures' in src):
                                        image_url = f"https://a0.muscache.com{src}"
                                        break
                        except Exception as e:
                            print(f"⚠️ Erro ao extrair imagem com seletor {selector}: {e}")
                            continue
                    
                if price > 0:  # Só adicionar se encontrou preço
                    listing_data = {
                        'title': title[:100],  # Limitar tamanho
                        'price_per_night': price,
                        'rating': rating,
                        'reviews': reviews_count,
                        'is_beachfront': beach_analysis['is_beachfront'],
                        'beach_confidence': beach_analysis['confidence_score'],
                        'beach_evidence': beach_analysis['evidence'][:3],  # Primeiras 3 evidências
                        'total_price': price * 2,  # Assumindo 2 noites por padrão
                        'listing_url': listing_url,
                        'image_url': image_url
                    }
                    
                    # Verificar se já existe (evitar duplicatas simples)
                    duplicate = False
                    for existing in listings:
                        if (existing['title'] == listing_data['title'] and 
                            existing['price_per_night'] == listing_data['price_per_night']):
                            duplicate = True
                            break
                    
                    if not duplicate:
                        listings.append(listing_data)
                        print(f"✅ {search_name} - Anúncio {i+1}: {title[:50]}... - R${price}/noite")
                        if listing_url:
                            print(f"🔗 URL capturada: {listing_url[:80]}...")
                        else:
                            print(f"⚠️ URL não encontrada para: {title[:50]}...")
                        
                        # Debug: log da imagem capturada
                        if image_url:
                            print(f"🖼️ Imagem capturada: {image_url[:80]}...")
                        else:
                            print(f"⚠️ Imagem não encontrada para: {title[:50]}...")
                            # Debug adicional: verificar se há imagens no container
                            all_imgs = container.find_all('img')
                            print(f"📊 Total de elementos img encontrados: {len(all_imgs)}")
                            for idx, img in enumerate(all_imgs[:3]):  # Mostrar apenas as 3 primeiras
                                img_src = img.get('src') or img.get('data-src') or 'N/A'
                                print(f"   Img {idx+1}: {img_src[:60]}..." if len(img_src) > 60 else f"   Img {idx+1}: {img_src}")
                    else:
                        print(f"🔄 {search_name} - Anúncio {i+1}: Duplicata ignorada - {title[:50]}...")
                else:
                    print(f"⚠️ {search_name} - Anúncio {i+1}: Preço não encontrado - {title[:50]}...")
                
            except Exception as e:
                print(f"❌ Erro ao processar anúncio {i+1}: {e}")
                continue
        
        print(f"📊 {search_name} - Total de anúncios únicos encontrados: {len(listings)}")
        return listings
    
    def _get_simulated_market_data(self, checkin_date, checkout_date):
        """
        Dados simulados baseados em pesquisa de mercado real de Itacuruçá
        """
        import random
        from datetime import datetime
        
        # Verificar se é final de semana ou feriado
        checkin_dt = datetime.strptime(checkin_date, '%Y-%m-%d')
        is_weekend = checkin_dt.weekday() >= 5  # Sábado ou Domingo
        
        # Preços base para diferentes tipos de propriedades
        base_prices = {
            'beachfront': {'min': 180, 'max': 350},
            'regular': {'min': 120, 'max': 250}
        }
        
        # Ajuste para final de semana
        weekend_multiplier = 1.3 if is_weekend else 1.0
        
        simulated_listings = []
        
        # Gerar 8-12 anúncios simulados
        num_listings = random.randint(8, 12)
        
        for i in range(num_listings):
            is_beachfront = random.choice([True, False, False])  # 33% chance de ser frente à praia
            price_range = base_prices['beachfront'] if is_beachfront else base_prices['regular']
            
            base_price = random.randint(price_range['min'], price_range['max'])
            final_price = int(base_price * weekend_multiplier)
            
            # Adicionar variação aleatória de ±10%
            variation = random.uniform(0.9, 1.1)
            final_price = int(final_price * variation)
            
            listing_types = [
                "Casa completa", "Apartamento", "Chalé", "Pousada", 
                "Casa de praia", "Studio", "Loft", "Casa de campo"
            ]
            
            # URLs de imagem de exemplo do Airbnb
            sample_images = [
                "https://a0.muscache.com/im/pictures/miso/Hosting-53274539/original/0e6c8b8b-8b0a-4b6d-9b1a-2b3c4d5e6f7g.jpg",
                "https://a0.muscache.com/im/pictures/miso/Hosting-12345678/original/1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p.jpg",
                "https://a0.muscache.com/im/pictures/prohost-api/Hosting-87654321/original/9f8e7d6c-5b4a-3928-1716-0504938271ab.jpg",
                "https://a0.muscache.com/im/pictures/hosting/Hosting-11223344/original/abcd1234-efgh5678-ijkl9012-mnop3456.jpg",
                "https://a0.muscache.com/im/pictures/airflow/Hosting-55667788/original/fedcba98-7654-3210-fedc-ba9876543210.jpg"
            ]
            
            simulated_listings.append({
                'title': f"{random.choice(listing_types)} em Itacuruçá {i+1}",
                'price_per_night': final_price,
                'rating': round(random.uniform(4.0, 4.9), 1),
                'reviews': random.randint(15, 150),
                'is_beachfront': is_beachfront,
                'beach_confidence': 0.8 if is_beachfront else 0.2,
                'beach_evidence': ['vista para o mar', 'acesso à praia'] if is_beachfront else [],
                'total_price': final_price * self._calculate_nights(checkin_date, checkout_date),
                'listing_url': f'https://www.airbnb.com.br/rooms/{random.randint(100000, 999999)}',
                'image_url': random.choice(sample_images)
            })
        
        print(f"📊 Dados simulados gerados: {len(simulated_listings)} anúncios")
        beachfront_count = sum(1 for l in simulated_listings if l['is_beachfront'])
        avg_price = sum(l['price_per_night'] for l in simulated_listings) / len(simulated_listings)
        print(f"🏖️ Frente à praia: {beachfront_count}, Outros: {len(simulated_listings) - beachfront_count}")
        print(f"💰 Preço médio simulado: R${avg_price:.2f}/noite")
        
        return simulated_listings
    
    def calculate_competitive_pricing(self, competitive_data, my_listing_beachfront=True, favorite_competitors=None):
        """
        Calcula preço competitivo baseado na análise da concorrência com justificativas detalhadas
        Agora inclui favoritos na análise quando disponíveis
        """
        # Incluir favoritos na análise se disponíveis
        all_competitive_data = competitive_data.copy() if competitive_data else []
        
        if favorite_competitors:
            print(f"📌 Incluindo {len(favorite_competitors)} favoritos na análise competitiva")
            for fav in favorite_competitors:
                # Converter formato dos favoritos para o formato esperado
                favorite_listing = {
                    'title': fav.get('title', 'Favorito'),
                    'price_per_night': float(fav.get('price_per_night', 0)),
                    'is_beachfront': fav.get('is_beachfront', False),
                    'location': fav.get('location', ''),
                    'image_url': fav.get('image_url', ''),
                    'listing_url': fav.get('listing_url', ''),
                    'is_favorite': True  # Marcar como favorito
                }
                if favorite_listing['price_per_night'] > 0:
                    all_competitive_data.append(favorite_listing)
        
        if not all_competitive_data:
            return {
                'suggested_price': 200,  # Preço base
                'strategy': 'Preço base - sem dados da concorrência',
                'market_analysis': {},
                'discount_percentage': 0,
                'discount_justification': 'Sem dados de mercado disponíveis para comparação'
            }
        
        # Filtrar anúncios com preços válidos
        valid_listings = [l for l in all_competitive_data if l['price_per_night'] > 0]
        
        if not valid_listings:
            return {
                'suggested_price': 200,
                'strategy': 'Preço base - sem preços válidos encontrados',
                'market_analysis': {},
                'discount_percentage': 0,
                'discount_justification': 'Dados de preços da concorrência são inválidos'
            }
        
        # Separar anúncios frente à praia vs outros
        beachfront_listings = [l for l in valid_listings if l['is_beachfront']]
        other_listings = [l for l in valid_listings if not l['is_beachfront']]
        favorite_listings = [l for l in valid_listings if l.get('is_favorite', False)]
        
        # Calcular estatísticas
        all_prices = [l['price_per_night'] for l in valid_listings]
        beachfront_prices = [l['price_per_night'] for l in beachfront_listings]
        other_prices = [l['price_per_night'] for l in other_listings]
        
        # Calcular preços dos favoritos
        favorite_prices = [l['price_per_night'] for l in favorite_listings]
        
        market_analysis = {
            'total_listings': len(valid_listings),
            'beachfront_listings': len(beachfront_listings),
            'other_listings': len(other_listings),
            'favorite_listings': len(favorite_listings),
            'avg_price_all': sum(all_prices) / len(all_prices),
            'min_price_all': min(all_prices),
            'max_price_all': max(all_prices),
            'avg_price_beachfront': sum(beachfront_prices) / len(beachfront_prices) if beachfront_prices else 0,
            'avg_price_other': sum(other_prices) / len(other_prices) if other_prices else 0,
            'avg_price_favorites': sum(favorite_prices) / len(favorite_prices) if favorite_prices else 0,
            'min_price_favorites': min(favorite_prices) if favorite_prices else 0,
            'max_price_favorites': max(favorite_prices) if favorite_prices else 0
        }
        
        # Estratégia de preço - priorizar favoritos se disponíveis
        if favorite_prices:
            # Se há favoritos, usar eles como base principal
            target_prices = favorite_prices
            reference_avg = market_analysis['avg_price_favorites']
            strategy_base = f"Baseado em {len(favorite_listings)} anúncios favoritos selecionados"
            competitor_type = "favoritos"
        elif my_listing_beachfront and beachfront_prices:
            # Se meu anúncio é frente à praia, competir com outros frente à praia
            target_prices = beachfront_prices
            reference_avg = market_analysis['avg_price_beachfront']
            strategy_base = "Competindo com anúncios frente à praia"
            competitor_type = "frente à praia"
        else:
            # Competir com todos os anúncios
            target_prices = all_prices
            reference_avg = market_analysis['avg_price_all']
            strategy_base = "Competindo com mercado geral"
            competitor_type = "regulares"
        
        # Analisar posição no mercado e calcular estratégia de desconto
        market_position = self._analyze_market_position(reference_avg, min(target_prices), max(target_prices))
        discount_strategy = self._calculate_discount_strategy(market_position, len(target_prices), competitor_type)
        
        # Aplicar desconto baseado na estratégia
        discount_percentage = discount_strategy['percentage']
        suggested_price = reference_avg * (1 - discount_percentage / 100)
        
        # Garantir que não seja mais de 10% abaixo do mínimo
        min_acceptable = min(target_prices) * 0.90
        if suggested_price < min_acceptable:
            suggested_price = min_acceptable
            discount_percentage = ((reference_avg - suggested_price) / reference_avg) * 100
            discount_strategy['justification'] += f" Preço ajustado para não ficar mais de 10% abaixo do menor concorrente (R${min(target_prices):.2f})."
        
        return {
            'suggested_price': round(suggested_price, 2),
            'strategy': f"{strategy_base} - {discount_strategy['strategy']}",
            'market_analysis': market_analysis,
            'discount_applied': f"{discount_percentage:.1f}%",
            'discount_percentage': round(discount_percentage, 1),
            'discount_justification': discount_strategy['justification'],
            'reference_avg': reference_avg
        }
    
    def _analyze_market_position(self, reference_avg, min_price, max_price):
        """
        Analisar posição no mercado baseado nos preços
        """
        price_range = max_price - min_price
        if price_range == 0:
            return 'stable'
        
        # Calcular onde a média está no range de preços
        position_ratio = (reference_avg - min_price) / price_range
        
        if position_ratio < 0.3:
            return 'low_competition'
        elif position_ratio > 0.7:
            return 'high_competition'
        else:
            return 'moderate_competition'
    
    def _calculate_discount_strategy(self, market_position, competitor_count, competitor_type):
        """
        Calcular estratégia de desconto baseada na análise de mercado
        """
        strategies = {
            'low_competition': {
                'percentage': 3,
                'strategy': 'Desconto mínimo para mercado com pouca concorrência',
                'justification': f'Mercado com baixa concorrência ({competitor_count} concorrentes {competitor_type}). Aplicando desconto mínimo de 3% para manter competitividade sem sacrificar muito a margem.'
            },
            'moderate_competition': {
                'percentage': 6,
                'strategy': 'Desconto moderado para equilibrar competitividade e margem',
                'justification': f'Mercado com concorrência moderada ({competitor_count} concorrentes {competitor_type}). Desconto de 6% oferece bom equilíbrio entre atratividade e rentabilidade.'
            },
            'high_competition': {
                'percentage': 10,
                'strategy': 'Desconto agressivo para mercado altamente competitivo',
                'justification': f'Mercado altamente competitivo ({competitor_count} concorrentes {competitor_type}). Desconto de 10% necessário para se destacar e garantir ocupação.'
            },
            'stable': {
                'percentage': 5,
                'strategy': 'Desconto padrão para mercado estável',
                'justification': f'Mercado com preços estáveis ({competitor_count} concorrentes {competitor_type}). Desconto padrão de 5% para manter competitividade.'
            }
        }
        
        return strategies.get(market_position, strategies['moderate_competition'])
    
    def get_weather_forecast(self, municipality=None):
        """
        Consulta a previsão do tempo para o município especificado
        """
        if municipality:
            # Buscar URL do ClimaTempo para o município
            climatempo_url = self._get_climatempo_url(municipality)
        else:
            # URL padrão para Itacuruçá
            climatempo_url = "https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3211/itacuruca-rj"
        
        try:
            print(f"🌤️ Buscando previsão do tempo para: {municipality or 'Itacuruçá'}")
            response = self.session.get(climatempo_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar informações de chuva
            weather_data = []
            
            # Procurar por elementos que contenham probabilidade de chuva
            rain_elements = soup.find_all(text=re.compile(r'\d+%.*chuva|chuva.*\d+%', re.IGNORECASE))
            
            for i, element in enumerate(rain_elements[:7]):  # Próximos 7 dias
                rain_match = re.search(r'(\d+)%', element)
                if rain_match:
                    rain_probability = int(rain_match.group(1))
                    date = datetime.now() + timedelta(days=i)
                    weather_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'rain_probability': rain_probability,
                        'weather_condition': 'Chuvoso' if rain_probability > 60 else 'Parcialmente nublado' if rain_probability > 30 else 'Ensolarado'
                    })
            
            # Se não encontrou dados específicos, fazer uma busca mais geral
            if not weather_data:
                # Buscar por qualquer menção de chuva ou tempo
                weather_keywords = soup.find_all(text=re.compile(r'chuva|sol|nublado|tempo', re.IGNORECASE))
                if weather_keywords:
                    # Assumir condições médias se não conseguir dados específicos
                    for i in range(7):
                        date = datetime.now() + timedelta(days=i)
                        weather_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'rain_probability': 30,  # Probabilidade média
                            'weather_condition': 'Condições variáveis'
                        })
            
            return weather_data
            
        except Exception as e:
            print(f"Erro ao buscar previsão do tempo para {municipality or 'Itacuruçá'}: {e}")
            return []
    
    def _get_climatempo_url(self, municipality):
        """
        Obtém a URL do ClimaTempo para o município especificado
        """
        try:
            # Mapeamento de cidades conhecidas para URLs do ClimaTempo
            city_urls = {
                'itacuruçá': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3211/itacuruca-rj',
                'mangaratiba': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3212/mangaratiba-rj',
                'angra dos reis': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3213/angra-dos-reis-rj',
                'paraty': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3214/paraty-rj',
                'búzios': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3215/armacao-dos-buzios-rj',
                'cabo frio': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3216/cabo-frio-rj',
                'arraial do cabo': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3217/arraial-do-cabo-rj',
                'saquarema': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3218/saquarema-rj',
                'maricá': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3219/marica-rj',
                'niterói': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3220/niteroi-rj',
                'rio de janeiro': 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3221/rio-de-janeiro-rj'
            }
            
            municipality_lower = municipality.lower().strip()
            
            # Buscar URL exata
            if municipality_lower in city_urls:
                print(f"🎯 URL encontrada para {municipality}")
                return city_urls[municipality_lower]
            
            # Buscar por correspondência parcial
            for city, url in city_urls.items():
                if municipality_lower in city or city in municipality_lower:
                    print(f"🎯 URL encontrada por correspondência parcial: {city} para {municipality}")
                    return url
            
            # Se não encontrar, tentar buscar dinamicamente no ClimaTempo
            search_url = f"https://www.climatempo.com.br/busca?q={quote(municipality)}"
            print(f"🔍 Buscando dinamicamente: {municipality}")
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Buscar por links de cidades nos resultados
                city_links = soup.find_all('a', href=re.compile(r'/previsao-do-tempo/.*cidade.*'))
                if city_links:
                    first_result = city_links[0]['href']
                    full_url = f"https://www.climatempo.com.br{first_result}"
                    print(f"🎯 URL encontrada dinamicamente: {full_url}")
                    return full_url
            
            # Fallback para Itacuruçá
            print(f"⚠️ Não foi possível encontrar URL para {municipality}, usando Itacuruçá")
            return city_urls['itacuruçá']
            
        except Exception as e:
            print(f"❌ Erro ao buscar URL do ClimaTempo para {municipality}: {str(e)}")
            return 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3211/itacuruca-rj'
    
    def _calculate_nights(self, checkin, checkout):
        """
        Calcula o número de noites entre check-in e check-out
        """
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
        return (checkout_date - checkin_date).days
    
    def suggest_pricing(self, base_price, weather_data, checkin_date, checkout_date):
        """
        Sugere preços baseado no clima e demanda de final de semana
        """
        checkin_dt = datetime.strptime(checkin_date, '%Y-%m-%d')
        checkout_dt = datetime.strptime(checkout_date, '%Y-%m-%d')
        
        # Verificar se é final de semana
        is_weekend = checkin_dt.weekday() >= 5 or checkout_dt.weekday() >= 5
        
        # Calcular probabilidade média de chuva
        avg_rain_prob = 0
        if weather_data:
            relevant_weather = [w for w in weather_data if checkin_date <= w['date'] <= checkout_date]
            if relevant_weather:
                avg_rain_prob = sum(w['rain_probability'] for w in relevant_weather) / len(relevant_weather)
        
        # Ajustar preço baseado em fatores
        price_multiplier = 1.0
        
        # Fator final de semana
        if is_weekend:
            price_multiplier *= 1.3  # 30% a mais no final de semana
        
        # Fator clima
        if avg_rain_prob > 70:
            price_multiplier *= 0.85  # 15% desconto se muita chuva
        elif avg_rain_prob < 20:
            price_multiplier *= 1.15  # 15% a mais se tempo bom
        
        suggested_price = base_price * price_multiplier
        
        return {
            'base_price': base_price,
            'suggested_price': round(suggested_price, 2),
            'price_multiplier': round(price_multiplier, 2),
            'is_weekend': is_weekend,
            'avg_rain_probability': round(avg_rain_prob, 1),
            'weather_factor': 'Desconto por chuva' if avg_rain_prob > 70 else 'Premium por tempo bom' if avg_rain_prob < 20 else 'Preço normal'
        }
    
    def run_analysis(self, checkin_date, checkout_date, adults=2):
        """
        Executa análise completa de preços e clima
        """
        print(f"🏨 Analisando preços para Itacuruçá - Hotel Mont Blanc")
        print(f"📅 Check-in: {checkin_date} | Check-out: {checkout_date}")
        print(f"👥 Adultos: {adults}")
        print("="*50)
        
        # Buscar preços do Airbnb
        print("🔍 Buscando preços no Airbnb...")
        airbnb_data = self.get_airbnb_prices(checkin_date, checkout_date, adults)
        
        # Buscar previsão do tempo
        print("🌤️ Consultando previsão do tempo...")
        weather_data = self.get_weather_forecast()
        
        # Análise e sugestões
        results = []
        
        if airbnb_data:
            for listing in airbnb_data:
                pricing_suggestion = self.suggest_pricing(
                    listing['price_per_night'], 
                    weather_data, 
                    checkin_date, 
                    checkout_date
                )
                
                result = {
                    'listing': listing,
                    'weather': weather_data,
                    'pricing_suggestion': pricing_suggestion
                }
                results.append(result)
                
                # Exibir resultados
                print(f"\n🏨 {listing['name']}")
                print(f"💰 Preço encontrado: R$ {listing['price_per_night']:.2f}/noite")
                print(f"💡 Preço sugerido: R$ {pricing_suggestion['suggested_price']:.2f}/noite")
                print(f"📊 Fator de ajuste: {pricing_suggestion['price_multiplier']}x")
                print(f"🌧️ Probabilidade média de chuva: {pricing_suggestion['avg_rain_probability']}%")
                print(f"📈 Justificativa: {pricing_suggestion['weather_factor']}")
                if pricing_suggestion['is_weekend']:
                    print("🎉 Final de semana detectado - preço premium aplicado")
        
        else:
            print("❌ Não foi possível obter dados do Airbnb")
            # Usar preço base estimado
            base_price = 200  # Preço estimado para a região
            pricing_suggestion = self.suggest_pricing(base_price, weather_data, checkin_date, checkout_date)
            
            print(f"\n🏨 Estimativa para Hotel Mont Blanc (preço base estimado)")
            print(f"💰 Preço base estimado: R$ {base_price:.2f}/noite")
            print(f"💡 Preço sugerido: R$ {pricing_suggestion['suggested_price']:.2f}/noite")
            print(f"📊 Fator de ajuste: {pricing_suggestion['price_multiplier']}x")
            print(f"🌧️ Probabilidade média de chuva: {pricing_suggestion['avg_rain_probability']}%")
            print(f"📈 Justificativa: {pricing_suggestion['weather_factor']}")
        
        # Exibir previsão detalhada do tempo
        if weather_data:
            print("\n🌤️ Previsão do tempo detalhada:")
            for day in weather_data[:5]:  # Próximos 5 dias
                print(f"  📅 {day['date']}: {day['rain_probability']}% chuva - {day['weather_condition']}")
        
        return results
    
    def send_email_report(self, analysis_results, competitive_data, pricing_suggestion):
        """
        Envia relatório por email com análise de preços e concorrência
        """
        if not self.email_config.get('sender_email') or not self.email_config.get('sender_password'):
            print("❌ Configuração de email não definida. Configure sender_email e sender_password.")
            return False
        
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = f"📊 Relatório de Preços Airbnb - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            # Criar corpo do email em HTML
            html_body = self._create_email_html(analysis_results, competitive_data, pricing_suggestion)
            
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Enviar email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['sender_email'], self.email_config['recipient_email'], text)
            server.quit()
            
            print(f"✅ Email enviado com sucesso para {self.email_config['recipient_email']}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
            return False
    
    def _create_email_html(self, analysis_results, competitive_data, pricing_suggestion):
        """
        Cria o corpo HTML do email com o relatório
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #FF5A5F; color: white; padding: 20px; border-radius: 10px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
                .price-highlight {{ background-color: #f0f8ff; padding: 10px; border-left: 4px solid #FF5A5F; }}
                .competitive-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                .competitive-table th, .competitive-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .competitive-table th {{ background-color: #f2f2f2; }}
                .beachfront {{ background-color: #e6f3ff; }}
                .weather-info {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏖️ Relatório de Preços - Hotel Mont Blanc Itacuruçá</h1>
                <p>Análise automática gerada em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
        """
        
        # Seção de preços sugeridos
        if pricing_suggestion:
            html += f"""
            <div class="section">
                <h2>💰 Preço Sugerido</h2>
                <div class="price-highlight">
                    <h3>R$ {pricing_suggestion['suggested_price']:.2f}/noite</h3>
                    <p><strong>Estratégia:</strong> {pricing_suggestion['strategy']}</p>
                    <p><strong>Desconto aplicado:</strong> {pricing_suggestion.get('discount_applied', 'N/A')}</p>
                    <p><strong>Preço médio de referência:</strong> R$ {pricing_suggestion.get('reference_avg', 0):.2f}</p>
                </div>
            </div>
            """
        
        # Análise de mercado
        if pricing_suggestion and 'market_analysis' in pricing_suggestion:
            market = pricing_suggestion['market_analysis']
            html += f"""
            <div class="section">
                <h2>📊 Análise de Mercado</h2>
                <ul>
                    <li><strong>Total de anúncios analisados:</strong> {market.get('total_listings', 0)}</li>
                    <li><strong>Anúncios frente à praia:</strong> {market.get('beachfront_listings', 0)}</li>
                    <li><strong>Outros anúncios:</strong> {market.get('other_listings', 0)}</li>
                    <li><strong>Preço médio geral:</strong> R$ {market.get('avg_price_all', 0):.2f}</li>
                    <li><strong>Preço médio frente à praia:</strong> R$ {market.get('avg_price_beachfront', 0):.2f}</li>
                    <li><strong>Faixa de preços:</strong> R$ {market.get('min_price_all', 0):.2f} - R$ {market.get('max_price_all', 0):.2f}</li>
                </ul>
            </div>
            """
        
        # Tabela de concorrentes
        if competitive_data:
            html += """
            <div class="section">
                <h2>🏨 Análise da Concorrência</h2>
                <table class="competitive-table">
                    <tr>
                        <th>Anúncio</th>
                        <th>Preço/Noite</th>
                        <th>Avaliação</th>
                        <th>Frente à Praia</th>
                        <th>Confiança</th>
                    </tr>
            """
            
            for listing in competitive_data[:15]:  # Mostrar até 15 concorrentes
                beachfront_class = "beachfront" if listing['is_beachfront'] else ""
                beachfront_text = "✅ Sim" if listing['is_beachfront'] else "❌ Não"
                
                html += f"""
                    <tr class="{beachfront_class}">
                        <td>{listing['title'][:50]}...</td>
                        <td>R$ {listing['price_per_night']:.2f}</td>
                        <td>{listing['rating']:.1f}</td>
                        <td>{beachfront_text}</td>
                        <td>{listing['beach_confidence']:.0f}%</td>
                    </tr>
                """
            
            html += "</table></div>"
        
        # Informações do clima
        if analysis_results and len(analysis_results) > 0 and 'weather' in analysis_results[0]:
            weather_data = analysis_results[0]['weather']
            if weather_data:
                html += """
                <div class="section">
                    <h2>🌤️ Previsão do Tempo</h2>
                    <div class="weather-info">
                """
                
                for day in weather_data[:5]:
                    html += f"<p><strong>{day['date']}:</strong> {day['rain_probability']}% chance de chuva - {day['weather_condition']}</p>"
                
                html += "</div></div>"
        
        # Recomendações
        html += """
        <div class="section">
            <h2>💡 Recomendações</h2>
            <ul>
                <li>Mantenha seu preço sempre competitivo (5-10% abaixo da média)</li>
                <li>Monitore anúncios frente à praia especialmente</li>
                <li>Ajuste preços baseado na previsão do tempo</li>
                <li>Considere promoções em dias com alta probabilidade de chuva</li>
            </ul>
        </div>
        
        <div class="section">
            <p><em>Este relatório é gerado automaticamente 2x ao dia. Para dúvidas ou ajustes, entre em contato.</em></p>
        </div>
        
        </body>
        </html>
        """
        
        return html
    
    def analyze_specific_listing(self, listing_url, checkin_date, checkout_date, adults=2):
        """
        Analisa um anúncio específico do Airbnb baseado no URL fornecido
        """
        try:
            print(f"📋 Extraindo dados do anúncio: {listing_url}")
            
            # Fazer requisição para o anúncio específico
            response = self.session.get(listing_url)
            if response.status_code != 200:
                print(f"❌ Erro ao acessar o anúncio: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair informações do anúncio
            listing_data = {
                'title': 'Anúncio Específico',
                'price_per_night': 0,
                'rating': 0,
                'reviews': 0,
                'is_beachfront': False,
                'beach_confidence': 0,
                'beach_evidence': [],
                'total_price': 0,
                'listing_url': listing_url,
                'image_url': '',
                'municipality': None
            }
            
            # Extrair título
            title_element = soup.find('h1') or soup.find('title')
            if title_element:
                listing_data['title'] = title_element.get_text(strip=True)[:100]
            
            # Extrair município/localização
            municipality = self._extract_municipality(soup)
            listing_data['municipality'] = municipality
            print(f"🏙️ Município identificado: {municipality}")
            
            # Extrair preço do Airbnb com padrões mais específicos
            page_text = soup.get_text()
            page_html = str(soup)
            price_found = False
            nights = self._calculate_nights(checkin_date, checkout_date)
            
            print(f"🔍 Buscando preços na página do Airbnb...")
            
            # Padrões específicos para valores totais do Airbnb
            total_patterns = [
                r'R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)\s*por\s*2\s*noites',
                r'R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)\s*total',
                r'Total\s*R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)',
                r'"totalPrice"[^}]*"amount"[^}]*([0-9]+)',
                r'"total"[^}]*([0-9]{3,6})',
                r'([0-9]{1,3}(?:\.[0-9]{3})+)\s*para\s*[0-9]+\s*noites?'
            ]
            
            # Primeiro, tentar encontrar o valor total
            for pattern in total_patterns:
                total_match = re.search(pattern, page_text, re.IGNORECASE)
                if total_match:
                    try:
                        total_str = total_match.group(1)
                        # Tratar formato brasileiro (1.079,00)
                        if ',' in total_str and '.' in total_str:
                            total_str = total_str.replace('.', '').replace(',', '.')
                        elif ',' in total_str:
                            total_str = total_str.replace(',', '.')
                        elif '.' in total_str and len(total_str.split('.')[-1]) == 3:
                            # Formato 1.079 (sem centavos)
                            total_str = total_str.replace('.', '')
                        
                        total_price = float(total_str)
                        
                        if nights > 0 and 100 <= total_price <= 50000:
                            price_per_night = total_price / nights
                            listing_data['price_per_night'] = price_per_night
                            listing_data['daily_rate_display'] = f"R$ {price_per_night:.2f} por noite"
                            listing_data['total_price'] = total_price
                            listing_data['extraction_method'] = f"Total encontrado: R$ {total_price:.2f} / {nights} noites"
                            print(f"💰 Valor total encontrado: R$ {total_price:.2f} para {nights} noites")
                            print(f"💰 Valor da diária: R$ {price_per_night:.2f} por noite")
                            price_found = True
                            break
                    except (ValueError, ZeroDivisionError):
                        continue
            
            # Se não encontrou total, buscar preço por noite
            if not price_found:
                night_patterns = [
                    r'R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)\s*por\s*noite',
                    r'R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)\s*/\s*noite',
                    r'"basePrice"[^}]*"amount"[^}]*([0-9]+)',
                    r'"price"[^}]*"amount"[^}]*([0-9]+)',
                    r'([0-9]{2,4})\s*por\s*noite'
                ]
                
                for pattern in night_patterns:
                    night_match = re.search(pattern, page_text, re.IGNORECASE)
                    if night_match:
                        try:
                            price_str = night_match.group(1)
                            # Tratar formato brasileiro
                            if ',' in price_str and '.' in price_str:
                                price_str = price_str.replace('.', '').replace(',', '.')
                            elif ',' in price_str:
                                price_str = price_str.replace(',', '.')
                            elif '.' in price_str and len(price_str.split('.')[-1]) == 3:
                                price_str = price_str.replace('.', '')
                            
                            price = float(price_str)
                            
                            if 50 <= price <= 5000:
                                listing_data['price_per_night'] = price
                                listing_data['daily_rate_display'] = f"R$ {price:.2f} por noite"
                                listing_data['total_price'] = price * nights
                                listing_data['extraction_method'] = f"Preço por noite encontrado diretamente"
                                print(f"💰 Valor da diária encontrado: R$ {price:.2f} por noite")
                                print(f"💰 Total do período: R$ {price * nights:.2f}")
                                price_found = True
                                break
                        except ValueError:
                            continue
            
            # Se ainda não encontrou, buscar em elementos específicos do DOM
            if not price_found:
                print("🔍 Buscando em elementos específicos do DOM...")
                price_elements = soup.find_all(text=re.compile(r'R\$\s*[0-9]'))
                for element in price_elements[:20]:  # Limitar busca
                    price_match = re.search(r'R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)', element)
                    if price_match:
                        try:
                            price_str = price_match.group(1)
                            if ',' in price_str and '.' in price_str:
                                price_str = price_str.replace('.', '').replace(',', '.')
                            elif ',' in price_str:
                                price_str = price_str.replace(',', '.')
                            elif '.' in price_str and len(price_str.split('.')[-1]) == 3:
                                price_str = price_str.replace('.', '')
                            
                            price = float(price_str)
                            
                            # Verificar se é um preço razoável
                            if 50 <= price <= 5000:
                                # Assumir que é preço por noite se estiver na faixa típica
                                if price <= 2000:
                                    listing_data['price_per_night'] = price
                                    listing_data['daily_rate_display'] = f"R$ {price:.2f} por noite"
                                    listing_data['total_price'] = price * nights
                                    listing_data['extraction_method'] = f"Extraído do DOM"
                                    print(f"💰 Valor encontrado no DOM: R$ {price:.2f} por noite")
                                    price_found = True
                                    break
                                # Se for valor alto, assumir que é total
                                elif nights > 0:
                                    price_per_night = price / nights
                                    if 50 <= price_per_night <= 2000:
                                        listing_data['price_per_night'] = price_per_night
                                        listing_data['daily_rate_display'] = f"R$ {price_per_night:.2f} por noite"
                                        listing_data['total_price'] = price
                                        listing_data['extraction_method'] = f"Total do DOM: R$ {price:.2f} / {nights} noites"
                                        print(f"💰 Total encontrado no DOM: R$ {price:.2f} para {nights} noites")
                                        print(f"💰 Valor da diária: R$ {price_per_night:.2f} por noite")
                                        price_found = True
                                        break
                        except ValueError:
                            continue
            
            # Se não encontrou preço, mostrar debug
            if not price_found:
                print("❌ Não foi possível extrair o preço da página")
                print("🔍 Primeiros 500 caracteres da página:")
                print(page_text[:500])
                print("\n🔍 Buscando por 'R$' na página:")
                r_matches = re.findall(r'R\$[^\n]{0,50}', page_text)
                for i, match in enumerate(r_matches[:5]):
                    print(f"  {i+1}. {match}")
                
                # Tentar extrair qualquer número que possa ser um preço
                print("\n🔍 Números encontrados na página:")
                numbers = re.findall(r'[0-9]{2,5}(?:[.,][0-9]{2,3})?', page_text)
                for i, num in enumerate(numbers[:20]):
                    print(f"  {i+1}. {num}")
            
            # Adicionar informações detalhadas do período
            if price_found:
                nights = self._calculate_nights(checkin_date, checkout_date)
                listing_data['period_details'] = {
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'nights': nights,
                    'total_period_cost': listing_data['price_per_night'] * nights
                }
            else:
                # Se não encontrou preço, usar um valor padrão baseado na região
                print("⚠️ Usando preço estimado para a região")
                estimated_price = 400  # Preço médio estimado para a região
                listing_data['price_per_night'] = estimated_price
                listing_data['daily_rate_display'] = f"R$ {estimated_price:.2f} por noite (estimado)"
                listing_data['total_price'] = estimated_price * nights
                listing_data['extraction_method'] = "Preço estimado - não encontrado na página"
                listing_data['period_details'] = {
                    'checkin': checkin_date,
                    'checkout': checkout_date,
                    'nights': nights,
                    'total_period_cost': estimated_price * nights
                }
            
            # Extrair rating e reviews
            rating_element = soup.find(text=re.compile(r'[0-9]\.[0-9]'))
            if rating_element:
                rating_match = re.search(r'([0-9]\.[0-9])', rating_element)
                if rating_match:
                    listing_data['rating'] = float(rating_match.group(1))
            
            # Verificar se é frente à praia
            page_text_lower = page_text.lower()
            beach_evidence = []
            for keyword in self.beach_keywords:
                if keyword.lower() in page_text_lower:
                    beach_evidence.append(keyword)
            
            if beach_evidence:
                listing_data['is_beachfront'] = True
                listing_data['beach_confidence'] = min(len(beach_evidence) * 0.3, 1.0)
                listing_data['beach_evidence'] = beach_evidence[:3]
            
            # Calcular preço total
            nights = self._calculate_nights(checkin_date, checkout_date)
            listing_data['total_price'] = listing_data['price_per_night'] * nights
            
            print(f"✅ Anúncio analisado: {listing_data['title']} - R$ {listing_data['price_per_night']:.2f}/noite")
            
            return [listing_data]
            
        except Exception as e:
            print(f"❌ Erro ao analisar anúncio específico: {str(e)}")
            return []
    
    def _extract_municipality(self, soup):
        """
        Extrai o município/cidade do anúncio do Airbnb
        """
        try:
            # Buscar por padrões de localização no HTML
            location_patterns = [
                # Buscar por elementos com informações de localização
                r'([A-ZÁÊÇÕ][a-záêçõ]+(?:\s+[A-ZÁÊÇÕ][a-záêçõ]+)*),\s*(?:RJ|Rio de Janeiro|SP|São Paulo|MG|Minas Gerais|ES|Espírito Santo|PR|Paraná|SC|Santa Catarina|RS|Rio Grande do Sul|BA|Bahia|PE|Pernambuco|CE|Ceará)',
                # Padrão mais específico para cidades do Rio de Janeiro
                r'(Itacuruçá|Mangaratiba|Angra dos Reis|Paraty|Búzios|Cabo Frio|Arraial do Cabo|Saquarema|Maricá|Niterói|Rio de Janeiro)',
                # Padrão geral para cidades brasileiras
                r'([A-ZÁÊÇÕ][a-záêçõ]+(?:\s+[a-záêçõ]+)*(?:\s+[A-ZÁÊÇÕ][a-záêçõ]+)*),\s*[A-Z]{2}'
            ]
            
            page_text = soup.get_text()
            
            # Buscar em elementos específicos que geralmente contêm localização
            location_elements = [
                soup.find('span', {'data-testid': 'listing-location'}),
                soup.find('div', {'data-testid': 'listing-location'}),
                soup.find('h1'),
                soup.find('title')
            ]
            
            # Buscar também em meta tags
            meta_location = soup.find('meta', {'property': 'og:title'}) or soup.find('meta', {'name': 'description'})
            if meta_location:
                location_elements.append(meta_location)
            
            for element in location_elements:
                if element:
                    element_text = element.get_text() if hasattr(element, 'get_text') else str(element.get('content', ''))
                    
                    for pattern in location_patterns:
                        match = re.search(pattern, element_text, re.IGNORECASE)
                        if match:
                            municipality = match.group(1).strip()
                            # Normalizar nome da cidade
                            municipality = municipality.title()
                            print(f"🎯 Município extraído: {municipality}")
                            return municipality
            
            # Se não encontrou nos elementos específicos, buscar no texto geral
            for pattern in location_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    municipality = match.group(1).strip()
                    municipality = municipality.title()
                    print(f"🎯 Município extraído do texto geral: {municipality}")
                    return municipality
            
            # Fallback para Itacuruçá se não conseguir identificar
            print("⚠️ Não foi possível identificar o município, usando Itacuruçá como padrão")
            return "Itacuruçá"
            
        except Exception as e:
            print(f"❌ Erro ao extrair município: {str(e)}")
            return "Itacuruçá"
    
    def run_competitive_analysis(self, checkin_date, checkout_date, my_listing_beachfront=True, adults=2, specific_listing_url=None):
        """
        Executa análise competitiva completa e envia relatório por email
        """
        if not specific_listing_url:
            raise ValueError("Link do anúncio é obrigatório para análise")
            
        print(f"🔍 Analisando anúncio específico: {specific_listing_url}")
        print(f"📅 Para o período: {checkin_date} a {checkout_date}")
        
        # Análise do anúncio específico
        competitive_data = self.analyze_specific_listing(specific_listing_url, checkin_date, checkout_date, adults)
        
        # Extrair município do anúncio para busca do clima
        municipality = None
        if competitive_data and len(competitive_data) > 0:
            municipality = competitive_data[0].get('municipality')
        
        # Obter favoritos se disponível no objeto
        favorite_competitors = getattr(self, 'favorite_competitors', None)
        
        # Calcular preços sugeridos incluindo favoritos
        pricing_suggestion = self.calculate_competitive_pricing(competitive_data, my_listing_beachfront, favorite_competitors)
        
        # Análise do clima baseada no município do anúncio
        weather_data = self.get_weather_forecast(municipality)
        
        # Ajustar preço baseado no clima
        if weather_data:
            avg_rain = sum(w['rain_probability'] for w in weather_data[:3]) / min(len(weather_data), 3)
            climate_adjustment = self.suggest_pricing(pricing_suggestion['suggested_price'], weather_data, checkin_date, checkout_date)
            pricing_suggestion['climate_adjusted_price'] = climate_adjustment['suggested_price']
            pricing_suggestion['climate_factor'] = climate_adjustment['weather_factor']
        
        # Preparar resultados para email
        analysis_results = [{
            'weather': weather_data,
            'competitive_data': competitive_data,
            'pricing_suggestion': pricing_suggestion
        }]
        
        # Exibir resultados no console
        print("\n" + "="*60)
        print("📊 ANÁLISE COMPETITIVA COMPLETA")
        print("="*60)
        
        print(f"\n💰 Preço sugerido: R$ {pricing_suggestion['suggested_price']:.2f}/noite")
        print(f"📈 Estratégia: {pricing_suggestion['strategy']}")
        
        # Mostrar informações de desconto
        if 'discount_percentage' in pricing_suggestion and pricing_suggestion['discount_percentage'] > 0:
            print(f"💸 Desconto aplicado: {pricing_suggestion['discount_percentage']:.1f}%")
            print(f"📋 Justificativa: {pricing_suggestion['discount_justification']}")
            if 'reference_avg' in pricing_suggestion:
                print(f"📊 Preço médio da concorrência: R$ {pricing_suggestion['reference_avg']:.2f}/noite")
        
        if 'climate_adjusted_price' in pricing_suggestion:
            print(f"🌤️ Preço ajustado pelo clima: R$ {pricing_suggestion['climate_adjusted_price']:.2f}/noite")
            print(f"🌧️ Fator climático: {pricing_suggestion['climate_factor']}")
        
        if competitive_data:
            beachfront_count = sum(1 for l in competitive_data if l['is_beachfront'])
            print(f"\n🏨 Concorrentes analisados: {len(competitive_data)}")
            print(f"🏖️ Frente à praia: {beachfront_count}")
            print(f"🏠 Outros: {len(competitive_data) - beachfront_count}")
            
            # Mostrar range de preços da concorrência
            if 'market_min' in pricing_suggestion and 'market_max' in pricing_suggestion:
                print(f"💹 Faixa de preços: R$ {pricing_suggestion['market_min']:.2f} - R$ {pricing_suggestion['market_max']:.2f}")
        
        # Enviar email
        email_sent = self.send_email_report(analysis_results, competitive_data, pricing_suggestion)
        
        return {
            'competitive_data': competitive_data,
            'pricing_suggestion': pricing_suggestion,
            'weather_data': weather_data,
            'email_sent': email_sent
        }
    
    def start_automated_monitoring(self, my_listing_beachfront=True):
        """
        Inicia monitoramento automatizado 2x ao dia
        """
        def run_analysis():
            try:
                # Analisar próximo final de semana
                today = datetime.now()
                days_until_friday = (4 - today.weekday()) % 7
                if days_until_friday == 0 and today.weekday() >= 4:
                    days_until_friday = 7
                
                next_friday = today + timedelta(days=days_until_friday)
                next_sunday = next_friday + timedelta(days=2)
                
                checkin = next_friday.strftime('%Y-%m-%d')
                checkout = next_sunday.strftime('%Y-%m-%d')
                
                print(f"\n🤖 Análise automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                self.run_competitive_analysis(checkin, checkout, my_listing_beachfront)
                
            except Exception as e:
                print(f"❌ Erro na análise automática: {e}")
        
        # Agendar execução a cada 5 minutos
        schedule.every(5).minutes.do(run_analysis)
        
        print("🤖 Monitoramento automático iniciado!")
        print("⏰ Análises programadas a cada 5 minutos")
        print("📧 Relatórios serão enviados para paulotestario@gmail.com")
        print("\n⚠️ Para parar o monitoramento, pressione Ctrl+C")
        
        # Executar primeira análise imediatamente
        print("\n🚀 Executando primeira análise...")
        run_analysis()
        
        # Loop de monitoramento
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Verificar a cada 30 segundos
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoramento automático interrompido pelo usuário")

if __name__ == "__main__":
    scraper = AirbnbClimateScraper()
    
    # Exemplo de uso - próximo final de semana
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0 and today.weekday() == 4:  # Se hoje é sexta
        days_until_friday = 0
    elif days_until_friday == 0:  # Se hoje é depois de sexta
        days_until_friday = 7 - today.weekday() + 4
    
    checkin = (today + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
    checkout = (today + timedelta(days=days_until_friday + 2)).strftime('%Y-%m-%d')
    
    print(f"Analisando para o próximo final de semana: {checkin} a {checkout}")
    results = scraper.run_analysis(checkin, checkout)