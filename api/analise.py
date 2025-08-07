import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

@app.route('/analise')
def analise():
    return render_template('analise.html')

# Handler para Vercel
def handler(request):
    from werkzeug.wrappers import Request, Response
    
    # Criar um objeto Request do Werkzeug
    werkzeug_request = Request(request.environ)
    
    # Processar a requisição através do Flask
    with app.request_context(werkzeug_request.environ):
        response = app.full_dispatch_request()
        
    # Retornar a resposta
    return response