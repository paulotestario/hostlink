import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from airbnb_scraper import AirbnbClimateScraper

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

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

# Handler para Vercel
def handler(request, response):
    return app(request.environ, lambda status, headers: response.status_code)