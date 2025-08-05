from flask import Flask, render_template, request, jsonify
import sys
import os

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airbnb_scraper import AirbnbClimateScraper
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Variáveis globais para monitoramento
monitoring_active = False
latest_analysis = None
analysis_history = []

def create_app():
    """Factory function para criar a aplicação Flask"""
    return app

# Importar todas as rotas do web_app original
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agenda')
def agenda():
    return render_template('agenda.html')

@app.route('/analise')
def analise():
    return render_template('analise.html')

@app.route('/similaridade')
def similaridade():
    return render_template('similaridade.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        checkin = data.get('checkin')
        checkout = data.get('checkout')
        adults = int(data.get('adults', 2))
        
        scraper = AirbnbClimateScraper()
        result = scraper.run_analysis(checkin, checkout, adults)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/similarity', methods=['POST'])
def similarity_analysis():
    try:
        data = request.get_json()
        
        # Extrair dados do formulário
        checkin = data.get('checkin')
        checkout = data.get('checkout')
        adults = int(data.get('adults', 2))
        
        # Dados do anúncio de referência
        reference_listing = {
            'title': data.get('title'),
            'image_url': data.get('image_url'),
            'is_beachfront': data.get('is_beachfront', False),
            'description': data.get('description', '')
        }
        
        scraper = AirbnbClimateScraper()
        result = scraper.run_similarity_analysis(
            checkin, checkout, adults, reference_listing
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    global monitoring_active, latest_analysis
    
    if monitoring_active:
        return jsonify({
            'success': False,
            'message': 'Monitoramento já está ativo'
        })
    
    try:
        data = request.get_json()
        beachfront = data.get('beachfront', False)
        
        monitoring_active = True
        
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
                    
                    # Atualizar dados globais
                    latest_analysis = {
                        'timestamp': datetime.now().isoformat(),
                        'period': f"{checkin} a {checkout}",
                        'result': result
                    }
                    
                    # Adicionar ao histórico (manter apenas últimas 10)
                    analysis_history.append(latest_analysis)
                    if len(analysis_history) > 10:
                        analysis_history.pop(0)
                    
                    print(f"✅ Análise automática concluída: {datetime.now()}")
                    
                    # Aguardar 5 minutos
                    for _ in range(300):  # 300 segundos = 5 minutos
                        if not monitoring_active:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"❌ Erro na análise automática: {e}")
                    time.sleep(60)  # Aguardar 1 minuto em caso de erro
        
        # Iniciar thread de monitoramento
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Monitoramento iniciado com sucesso'
        })
        
    except Exception as e:
        monitoring_active = False
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    global monitoring_active
    
    monitoring_active = False
    
    return jsonify({
        'success': True,
        'message': 'Monitoramento interrompido'
    })

@app.route('/api/monitoring/status')
def monitoring_status():
    global monitoring_active, latest_analysis, analysis_history
    
    return jsonify({
        'active': monitoring_active,
        'latest_analysis': latest_analysis,
        'history_count': len(analysis_history),
        'history': analysis_history[-5:] if analysis_history else []  # Últimas 5 análises
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)