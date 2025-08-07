import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

@app.route('/')
def index():
    return render_template('index.html')

# Handler para Vercel
def handler(request, response):
    return app(request.environ, lambda status, headers: response.status_code)