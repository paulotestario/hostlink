import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
from airbnb_scraper import AirbnbClimateScraper

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

@app.route('/similaridade')
def similaridade():
    return render_template('similaridade.html')

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

# Handler para Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)