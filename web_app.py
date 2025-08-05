#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web para Análise de Preços Airbnb
Interface web para visualizar resultados da análise competitiva
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from airbnb_scraper import AirbnbClimateScraper
from datetime import datetime, timedelta
import json
import threading
import time

app = Flask(__name__)
app.secret_key = 'airbnb_analysis_2024'

# Variáveis globais para armazenar dados
latest_analysis = None
analysis_history = []
monitoring_active = False
monitoring_thread = None
favorite_competitors = []  # Lista de concorrentes favoritos

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html', 
                         latest_analysis=latest_analysis,
                         monitoring_active=monitoring_active)

@app.route('/analise')
def analise():
    """Página de análise detalhada"""
    return render_template('analise.html', 
                         analysis_data=latest_analysis,
                         history=analysis_history[-10:])  # Últimas 10 análises

@app.route('/agenda')
def agenda():
    """Página da agenda de preços"""
    return render_template('agenda.html')

@app.route('/similaridade')
def similaridade():
    """Página de análise de similaridade"""
    return render_template('similaridade.html')

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
def api_sync_favorites():
    """API para sincronizar favoritos do frontend"""
    global favorite_competitors
    
    try:
        data = request.get_json()
        frontend_favorites = data.get('favorites', [])
        
        # Atualizar lista global com os favoritos do frontend
        favorite_competitors = []
        for fav in frontend_favorites:
            favorite_item = {
                'id': fav.get('id'),
                'title': fav.get('title'),
                'price_per_night': fav.get('price_per_night'),
                'location': fav.get('location'),
                'is_beachfront': fav.get('is_beachfront', False),
                'image_url': fav.get('image_url'),
                'listing_url': fav.get('listing_url'),
                'added_date': fav.get('added_date'),
                'last_sync': datetime.now().isoformat()
            }
            favorite_competitors.append(favorite_item)
        
        return jsonify({
            'success': True,
            'message': f'{len(favorite_competitors)} favoritos sincronizados',
            'total_favorites': len(favorite_competitors)
        })
        
    except Exception as e:
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
        
        # Adicionar informações do período
        result['timestamp'] = datetime.now().isoformat()
        result['checkin'] = checkin
        result['checkout'] = checkout
        result['adults'] = adults
        result['beachfront'] = beachfront
        result['period_type'] = period_type
        result['is_weekend'] = period_type == 'weekend'
        result['nights'] = nights
        
        # Atualizar dados globais
        latest_analysis = result
        analysis_history.append(result)
        
        # Manter apenas últimas 50 análises
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
    return jsonify({
        'success': True,
        'data': latest_analysis,
        'monitoring_active': monitoring_active
    })

@app.route('/api/get_history', methods=['GET'])
def api_get_history():
    """API para obter histórico de análises"""
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

if __name__ == '__main__':
    print("🌐 Iniciando aplicação web...")
    print("📊 Acesse: http://localhost:5000")
    print("⚠️ Para parar, pressione Ctrl+C")
    
    app.run(debug=True, host='0.0.0.0', port=5000)