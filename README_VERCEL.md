# 🚀 Deploy HostLink no Vercel

Este guia explica como fazer o deploy da aplicação HostLink no Vercel usando a estrutura de funções serverless.

## 📁 Estrutura para Vercel

A aplicação foi refatorada para ser compatível com Vercel:

```
C:\Airbnb/
├── api/                    # Funções serverless
│   ├── __init__.py
│   ├── app.py             # Flask app compartilhado
│   ├── index.py           # Rota principal /
│   ├── agenda.py          # Rota /agenda
│   ├── analise.py         # Rota /analise
│   └── similaridade.py    # Rota /similaridade
├── static/                # Arquivos estáticos
│   ├── hostlink-theme.css
│   ├── placeholder.jpg
│   └── placeholder.svg
├── templates/             # Templates HTML
│   ├── index.html
│   ├── agenda.html
│   ├── analise.html
│   └── similaridade.html
├── vercel.json           # Configuração do Vercel
├── requirements.txt      # Dependências Python
└── airbnb_scraper.py    # Módulo principal
```

## 🔧 Configuração

### 1. Arquivo `vercel.json`

O arquivo `vercel.json` configura:
- **Builds**: Como construir as funções Python e servir arquivos estáticos
- **Routes**: Mapeamento de URLs para funções serverless

### 2. Funções Serverless

Cada rota principal foi convertida em uma função serverless em `/api`:
- `/` → `/api/index.py`
- `/agenda` → `/api/agenda.py`
- `/analise` → `/api/analise.py`
- `/similaridade` → `/api/similaridade.py`

### 3. Flask App Compartilhado

O arquivo `/api/app.py` contém:
- Configuração do Flask com paths corretos para templates e static
- Todas as rotas e endpoints da API
- Lógica de monitoramento adaptada para serverless

## 🚀 Deploy no Vercel

### Pré-requisitos

1. **Conta no Vercel**: Crie uma conta em [vercel.com](https://vercel.com)
2. **Vercel CLI** (opcional):
   ```bash
   npm install -g vercel
   ```

### Método 1: Deploy via GitHub

1. **Suba o código para GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - HostLink Vercel ready"
   git remote add origin https://github.com/seu-usuario/hostlink.git
   git push -u origin main
   ```

2. **Conecte no Vercel**:
   - Acesse [vercel.com/dashboard](https://vercel.com/dashboard)
   - Clique em "New Project"
   - Importe seu repositório GitHub
   - Vercel detectará automaticamente o `vercel.json`

### Método 2: Deploy via CLI

1. **Login no Vercel**:
   ```bash
   vercel login
   ```

2. **Deploy**:
   ```bash
   vercel
   ```

3. **Deploy para produção**:
   ```bash
   vercel --prod
   ```

## ⚙️ Variáveis de Ambiente

Se sua aplicação usar variáveis de ambiente, configure no Vercel:

1. Acesse o dashboard do projeto
2. Vá em "Settings" → "Environment Variables"
3. Adicione as variáveis necessárias

## 🔍 Limitações do Vercel

### ⚠️ Monitoramento Automático

O monitoramento automático a cada 5 minutos **não funcionará** no Vercel porque:
- Funções serverless têm timeout (máximo 10s no plano gratuito)
- Não há estado persistente entre execuções
- Threads em background não são suportadas

### 💡 Alternativas para Monitoramento

1. **Vercel Cron Jobs** (plano Pro):
   ```json
   {
     "crons": [
       {
         "path": "/api/monitor",
         "schedule": "*/5 * * * *"
       }
     ]
   }
   ```

2. **Serviços externos**:
   - GitHub Actions com cron
   - Zapier/IFTTT
   - Cron-job.org

3. **Plataformas com servidores persistentes**:
   - Render.com
   - Railway.app
   - PythonAnywhere
   - Heroku

## 🧪 Testando Localmente

Para testar a estrutura Vercel localmente:

```bash
# Instalar Vercel CLI
npm install -g vercel

# Executar localmente
vercel dev
```

## 📝 Notas Importantes

1. **Templates**: Os templates HTML são servidos corretamente através das funções serverless
2. **Static Files**: Arquivos CSS, JS e imagens são servidos diretamente pelo Vercel
3. **Cold Starts**: Primeira execução pode ser mais lenta (cold start)
4. **Timeouts**: Funções têm limite de tempo de execução
5. **Memória**: Limite de memória por função (512MB no plano gratuito)

## 🆘 Troubleshooting

### Erro de Import
Se houver erros de import, verifique:
- Paths relativos nos imports
- Estrutura de pastas
- Arquivo `__init__.py` na pasta api

### Templates não encontrados
Verifique se o path no Flask está correto:
```python
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
```

### Função timeout
Para análises longas, considere:
- Otimizar o código
- Usar cache
- Dividir em múltiplas funções
- Migrar para plataforma com servidores persistentes

## 🔗 Links Úteis

- [Documentação Vercel Python](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Vercel CLI](https://vercel.com/docs/cli)
- [Vercel Dashboard](https://vercel.com/dashboard)