import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

@app.route('/agenda')
def agenda():
    return render_template('agenda.html')

# Handler para Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)